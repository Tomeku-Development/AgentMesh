# Demo Script

# AgentMesh

**Version:** 1.0.0

**Status:** Live Demo Walkthrough

**Demo:** Investment Committee — Autonomous Due Diligence

**Developed by:** Tomeku

**Website:** https://tomeku.com

**Socials**

* Facebook: OfficialTomeku
* X: OfficialTomeku
* YouTube: OfficialTomeku

---

# Table of Contents

1. Demo Goal
2. Audience Takeaways
3. Setup & Pre-Flight
4. Scene-by-Scene Script
5. On-Chain Proof
6. Fallback Plan
7. Timing
8. Q&A Prep

---

# Demo Goal

Show, in under four minutes, an AI organization performing real due diligence and recording a trustworthy decision on Casper — no human writing the analysis, but a human in control.

The narrative: **"A startup applies for investment. Our AI investment committee evaluates it and records its verdict on-chain."**

---

# Audience Takeaways

By the end, the audience should believe three things:

1. Multiple specialized agents genuinely collaborated.
2. The decision was reasoned and evidence-backed, not a single prompt.
3. The outcome is permanently verifiable on Casper.

---

# Setup & Pre-Flight

**Before the demo:**

* [ ] Frontend deployed and reachable; dashboard loaded.
* [ ] Backend healthy (`/health` green); agents warm.
* [ ] Casper Testnet wallet funded; contracts deployed.
* [ ] A prepared startup profile ready to paste.
* [ ] CSPR.cloud / block explorer open in a second tab.
* [ ] Network and a recorded backup video ready (see Fallback).

**Browser tabs:**
1. AgentMesh dashboard.
2. Casper explorer (to show the transaction).

---

# Scene-by-Scene Script

## Scene 1 — The Organization (0:00–0:30)

**Do:** Open the dashboard. Show live network stats (agents online, transactions, proposals, TVL).

**Say:** "This is an autonomous investment organization. These agents — Coordinator, Market, Finance, Legal, Risk — are online and ready to work together."

---

## Scene 2 — Submit the Proposal (0:30–1:00)

**Do:** Click *New Proposal*. Paste the startup profile (name, sector, ask, metrics). Submit.

**Say:** "I'm submitting a real investment request. From here, no human writes the analysis. The mesh takes over."

---

## Scene 3 — Agents Collaborate (1:00–2:15)

**Do:** Show the live workflow view — the coordinator fanning out to specialists; each agent streaming its findings.

**Say:**
* "The **Market agent** sizes the opportunity and competition."
* "The **Finance agent** checks the numbers and runway."
* "The **Legal agent** flags structure and compliance."
* "The **Risk agent** scores the downside."

"Notice every claim comes with supporting evidence — this is transparent reasoning, not a black box."

---

## Scene 4 — Consensus (2:15–2:55)

**Do:** Show the consensus engine aggregating positions, the debate/votes, and the final recommendation with a confidence score.

**Say:** "Now the agents debate and reach consensus. The committee's verdict is *invest / pass / revise* — with a confidence score and a rationale."

---

## Scene 5 — On-Chain Execution (2:55–3:30)

**Do:** Approve the decision (human oversight). Trigger the Casper transaction. Show the pending → confirmed state.

**Say:** "I approve the committee's decision. The Treasury agent now executes on Casper. This isn't a log entry in a database — it's an immutable, verifiable action."

---

## Scene 6 — Proof (3:30–4:00)

**Do:** Switch to the Casper explorer. Show the transaction hash and the recorded decision. Return to the dashboard — stats update.

**Say:** "Here's the transaction on Casper. Anyone — an auditor, a regulator, an LP — can verify what was decided, by whom, and why. That's the difference between AI that talks and AI you can trust."

---

# On-Chain Proof

Highlight on the explorer:

* The deploy/transaction hash.
* The contract that recorded the decision.
* The immutable payload: proposal ID, verdict, confidence, agent signatures.

Tie it back: "Off-chain reasoning, on-chain trust."

---

# Fallback Plan

If live conditions fail:

* **Network issue:** switch to the pre-recorded run; narrate over it.
* **Slow AI response:** use a cached proposal result prepared earlier.
* **Chain congestion:** show a previously confirmed transaction on the explorer.

Never debug live. Cut to the backup and keep the story moving.

---

# Timing

| Scene | Target | Cumulative |
|-------|--------|------------|
| 1 Organization | 0:30 | 0:30 |
| 2 Submit | 0:30 | 1:00 |
| 3 Collaborate | 1:15 | 2:15 |
| 4 Consensus | 0:40 | 2:55 |
| 5 Execute | 0:35 | 3:30 |
| 6 Proof | 0:30 | 4:00 |

---

# Q&A Prep

* **"Is this just GPT with steps?"** No — specialized agents with memory, tools, permissions, and wallets, coordinated by LangGraph, with on-chain execution.
* **"What if the AI is wrong?"** Human approval gates critical actions; evidence is transparent; everything is auditable and reversible at the policy layer.
* **"Why blockchain?"** Verifiable trust between parties and immutable audit — impossible with a private database.
* **"Why Casper?"** Predictable fees for frequent actions, upgradeable contracts, and agentic rails (MCP, x402).

---

**Built for the Casper Agentic Buildathon — by Tomeku.**
