"""Ed25519 identity management for MESH agents."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from nacl.signing import SigningKey, VerifyKey


@dataclass(frozen=True)
class AgentIdentity:
    """An agent's cryptographic identity derived from an Ed25519 keypair."""

    signing_key: SigningKey
    verify_key: VerifyKey
    agent_id: str  # First 16 hex chars of SHA-256 of public key
    public_key_hex: str

    @classmethod
    def generate(cls) -> AgentIdentity:
        """Generate a new random identity."""
        sk = SigningKey.generate()
        return cls._from_signing_key(sk)

    @classmethod
    def from_seed(cls, seed: bytes) -> AgentIdentity:
        """Create identity from a 32-byte seed (deterministic)."""
        sk = SigningKey(seed)
        return cls._from_signing_key(sk)

    @classmethod
    def from_hex(cls, hex_seed: str) -> AgentIdentity:
        """Create identity from a hex-encoded 32-byte seed."""
        return cls.from_seed(bytes.fromhex(hex_seed))

    @classmethod
    def _from_signing_key(cls, sk: SigningKey) -> AgentIdentity:
        vk = sk.verify_key
        pk_bytes = bytes(vk)
        pk_hex = pk_bytes.hex()
        agent_id = hashlib.sha256(pk_bytes).hexdigest()[:16]
        return cls(signing_key=sk, verify_key=vk, agent_id=agent_id, public_key_hex=pk_hex)

    def sign(self, data: bytes) -> bytes:
        """Sign data with Ed25519, returning the 64-byte signature."""
        signed = self.signing_key.sign(data)
        return signed.signature

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify an Ed25519 signature. Returns False on failure."""
        try:
            self.verify_key.verify(data, signature)
            return True
        except Exception:
            return False

    def seed_hex(self) -> str:
        """Return the private seed as hex (for storage)."""
        return bytes(self.signing_key).hex()
