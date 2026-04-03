"""In-memory credit ledger with escrow for MESH economic model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from mesh.core.messages import LedgerTransaction


class InsufficientFundsError(Exception):
    pass


class EscrowNotFoundError(Exception):
    pass


@dataclass
class EscrowRecord:
    """Funds held in escrow for an order."""
    escrow_id: str
    order_id: str
    from_agent: str
    amount: float
    released: bool = False


class Ledger:
    """Deterministic in-memory double-entry ledger synced via BFT-ordered MQTT.

    Since FoxMQ guarantees all agents see transactions in the same order,
    every agent running the same ledger logic will converge to the same state.
    """

    BURN_ADDRESS = "__burned__"

    def __init__(self) -> None:
        self._balances: dict[str, float] = {}
        self._escrows: dict[str, EscrowRecord] = {}
        self._transactions: list[LedgerTransaction] = []

    def init_balance(self, agent_id: str, amount: float) -> None:
        """Set initial balance for an agent."""
        self._balances[agent_id] = amount

    def balance(self, agent_id: str) -> float:
        """Get current balance. Returns 0 for unknown agents."""
        return self._balances.get(agent_id, 0.0)

    def all_balances(self) -> dict[str, float]:
        return dict(self._balances)

    def transfer(
        self,
        from_agent: str,
        to_agent: str,
        amount: float,
        tx_type: str = "payment",
        order_id: str = "",
        memo: str = "",
    ) -> LedgerTransaction:
        """Transfer credits between agents. Raises InsufficientFundsError."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        from_balance = self._balances.get(from_agent, 0.0)
        if from_balance < amount:
            raise InsufficientFundsError(
                f"{from_agent} has {from_balance:.2f}, needs {amount:.2f}"
            )

        self._balances[from_agent] = from_balance - amount
        self._balances.setdefault(to_agent, 0.0)
        if to_agent != self.BURN_ADDRESS:
            self._balances[to_agent] += amount

        tx = LedgerTransaction(
            tx_type=tx_type,
            from_agent=from_agent,
            to_agent=to_agent,
            amount=amount,
            order_id=order_id,
            memo=memo,
            balance_after_from=self._balances[from_agent],
            balance_after_to=self._balances.get(to_agent, 0.0),
        )
        self._transactions.append(tx)
        return tx

    def escrow_lock(
        self,
        from_agent: str,
        amount: float,
        order_id: str,
    ) -> EscrowRecord:
        """Lock funds in escrow for an order."""
        from_balance = self._balances.get(from_agent, 0.0)
        if from_balance < amount:
            raise InsufficientFundsError(
                f"{from_agent} has {from_balance:.2f}, needs {amount:.2f}"
            )

        self._balances[from_agent] = from_balance - amount
        escrow_id = str(uuid.uuid4())
        record = EscrowRecord(
            escrow_id=escrow_id,
            order_id=order_id,
            from_agent=from_agent,
            amount=amount,
        )
        self._escrows[order_id] = record

        tx = LedgerTransaction(
            tx_type="escrow_lock",
            from_agent=from_agent,
            to_agent="__escrow__",
            amount=amount,
            order_id=order_id,
            memo=f"Escrow locked for order {order_id}",
            balance_after_from=self._balances[from_agent],
            balance_after_to=amount,
        )
        self._transactions.append(tx)
        return record

    def escrow_release(
        self,
        order_id: str,
        distributions: list[tuple[str, float, str]],
    ) -> list[LedgerTransaction]:
        """Release escrowed funds to multiple recipients.

        Args:
            order_id: The order whose escrow to release.
            distributions: List of (agent_id, amount, memo) tuples.
                Total must not exceed escrowed amount.

        Returns:
            List of transactions created.
        """
        if order_id not in self._escrows:
            raise EscrowNotFoundError(f"No escrow for order {order_id}")

        record = self._escrows[order_id]
        if record.released:
            raise EscrowNotFoundError(f"Escrow for order {order_id} already released")

        total_distributed = sum(amt for _, amt, _ in distributions)
        if total_distributed > record.amount + 0.01:  # float tolerance
            raise ValueError(
                f"Distribution total {total_distributed:.2f} exceeds escrow {record.amount:.2f}"
            )

        transactions = []
        for to_agent, amount, memo in distributions:
            if amount <= 0:
                continue
            self._balances.setdefault(to_agent, 0.0)
            if to_agent != self.BURN_ADDRESS:
                self._balances[to_agent] += amount
            tx = LedgerTransaction(
                tx_type="escrow_release",
                from_agent="__escrow__",
                to_agent=to_agent,
                amount=amount,
                order_id=order_id,
                memo=memo,
                balance_after_from=0.0,
                balance_after_to=self._balances.get(to_agent, 0.0),
            )
            self._transactions.append(tx)
            transactions.append(tx)

        # Return any remainder to original depositor
        remainder = record.amount - total_distributed
        if remainder > 0.01:
            self._balances[record.from_agent] += remainder
            tx = LedgerTransaction(
                tx_type="escrow_release",
                from_agent="__escrow__",
                to_agent=record.from_agent,
                amount=remainder,
                order_id=order_id,
                memo="Escrow remainder returned",
                balance_after_from=0.0,
                balance_after_to=self._balances[record.from_agent],
            )
            self._transactions.append(tx)
            transactions.append(tx)

        record.released = True
        return transactions

    def escrow_refund(self, order_id: str) -> LedgerTransaction:
        """Refund escrowed funds back to the original depositor."""
        if order_id not in self._escrows:
            raise EscrowNotFoundError(f"No escrow for order {order_id}")

        record = self._escrows[order_id]
        if record.released:
            raise EscrowNotFoundError(f"Escrow for order {order_id} already released")

        self._balances[record.from_agent] += record.amount
        record.released = True

        tx = LedgerTransaction(
            tx_type="escrow_release",
            from_agent="__escrow__",
            to_agent=record.from_agent,
            amount=record.amount,
            order_id=order_id,
            memo="Full escrow refund",
            balance_after_from=0.0,
            balance_after_to=self._balances[record.from_agent],
        )
        self._transactions.append(tx)
        return tx

    def get_escrow(self, order_id: str) -> EscrowRecord | None:
        return self._escrows.get(order_id)

    @property
    def transaction_count(self) -> int:
        return len(self._transactions)

    @property
    def recent_transactions(self) -> list[LedgerTransaction]:
        return self._transactions[-50:]

    def total_transacted(self) -> float:
        """Sum of all transaction amounts."""
        return sum(tx.amount for tx in self._transactions)
