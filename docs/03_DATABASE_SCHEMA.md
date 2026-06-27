# Database Schema

# AgentMesh

**Version:** 1.0.0

**Status:** Database Design Specification

**Developed by:** Tomeku

**Website:** https://tomeku.com

---

# Table of Contents

1. Overview
2. Database Philosophy
3. Architecture
4. Core Entities
5. Relationships
6. Tables
7. Index Strategy
8. Audit Strategy
9. Multi-Tenancy
10. Future Expansion

---

# Overview

AgentMesh is built on a relational PostgreSQL database designed for enterprise-scale autonomous organizations.

The database supports:

* Multi-tenancy
* Organizations
* Users
* AI Agents
* Workflows
* Projects
* Smart Contract Integrations
* Wallets
* Audit Logs
* Analytics

The design follows:

* Third Normal Form (3NF)
* UUID Primary Keys
* Soft Deletes
* Audit Logging
* Organization Isolation

---

# Database Philosophy

The database should answer every important business question.

Questions such as:

* Who created this organization?
* Which AI agent made this recommendation?
* Why was funding approved?
* Which smart contract executed this transaction?
* Which workflow produced this result?
* Which version of the AI generated this decision?

Every important event should be traceable.

---

# Database Engine

PostgreSQL 16+

Extensions

* pgvector (optional)
* uuid-ossp
* pgcrypto

ORM

Drizzle ORM

---

# High-Level ER Diagram

```text
Users
 │
 ├──────────────┐
 │              │
 ▼              ▼
Organizations   Sessions
 │
 ▼
Projects
 │
 ▼
Workflows
 │
 ▼
Workflow Runs
 │
 ▼
Agent Executions
 │
 ▼
Consensus
 │
 ▼
Treasury Transactions
 │
 ▼
Casper Blockchain
```

---

# Core Tables

| Table           | Purpose                    |
| --------------- | -------------------------- |
| users           | Platform users             |
| organizations   | Multi-tenant organizations |
| memberships     | Organization members       |
| roles           | RBAC roles                 |
| permissions     | Permission matrix          |
| projects        | Organization projects      |
| workflows       | Workflow definitions       |
| workflow_runs   | Workflow executions        |
| agents          | AI Agent registry          |
| agent_memory    | Long-term memory           |
| executions      | Individual agent runs      |
| consensus       | AI consensus results       |
| wallets         | Blockchain wallets         |
| smart_contracts | Casper contracts           |
| transactions    | Blockchain transactions    |
| notifications   | User notifications         |
| audit_logs      | Immutable audit records    |
| api_keys        | API authentication         |
| integrations    | External integrations      |
| files           | Uploaded assets            |

---

# Users

Stores every registered user.

```sql
users

id UUID PK

name

email

avatar

password_hash

provider

email_verified

created_at

updated_at

deleted_at
```

Relationships

* One User → Many Organizations
* One User → Many Sessions
* One User → Many Wallets

---

# Organizations

Every workspace belongs to an organization.

```sql
organizations

id UUID PK

name

slug

logo

description

plan

status

owner_id

created_at

updated_at
```

Relationships

* Organization → Projects
* Organization → Members
* Organization → Agents
* Organization → Workflows

---

# Memberships

Defines organization membership.

```sql
memberships

id

organization_id

user_id

role_id

joined_at

status
```

---

# Roles

```sql
roles

id

name

description
```

Default Roles

* Owner
* Admin
* Developer
* Analyst
* Observer

---

# Permissions

```sql
permissions

id

resource

action
```

Examples

```text
projects.create

projects.delete

agents.execute

treasury.manage

contracts.deploy

users.invite
```

---

# Projects

A project represents a business initiative.

Examples

* Startup Investment
* Treasury Proposal
* Compliance Review
* Procurement

```sql
projects

id

organization_id

title

description

status

priority

created_by

created_at
```

---

# AI Agents

Stores every autonomous agent.

```sql
agents

id

organization_id

name

role

description

model

temperature

status

wallet_id

memory_id

created_at
```

---

# Agent Capabilities

Each agent supports

* Memory
* Prompt
* APIs
* MCP Tools
* Wallet
* Reputation

---

# Workflows

Defines reusable workflow templates.

```sql
workflows

id

organization_id

name

description

version

graph_json

status
```

Example

Investment Committee

↓

Research

↓

Finance

↓

Legal

↓

Risk

↓

Consensus

↓

Treasury

---

# Workflow Runs

Each workflow execution generates a run.

```sql
workflow_runs

id

workflow_id

organization_id

status

started_at

completed_at

duration

initiated_by
```

---

# Agent Executions

Every AI action is recorded.

```sql
executions

id

workflow_run_id

agent_id

status

tokens_used

latency

cost

started_at

completed_at
```

This table powers:

* Analytics
* Debugging
* Billing
* Performance

---

# Consensus

Stores final AI recommendations.

```sql
consensus

id

workflow_run_id

result

confidence

summary

approved

generated_at
```

---

# Wallets

Every organization and AI agent may own wallets.

```sql
wallets

id

organization_id

agent_id

network

address

encrypted_private_key

created_at
```

Supported Networks

* Casper

Future

* Ethereum
* Solana
* Bitcoin

---

# Smart Contracts

Tracks deployed contracts.

```sql
smart_contracts

id

organization_id

name

network

contract_hash

version

status
```

---

# Transactions

Every blockchain execution.

```sql
transactions

id

wallet_id

contract_id

hash

network

status

gas

timestamp
```

---

# Agent Memory

Semantic memory storage.

```sql
agent_memory

id

agent_id

vector_id

title

content

metadata

created_at
```

Stored inside

Qdrant

Metadata stored inside PostgreSQL.

---

# API Keys

Developer authentication.

```sql
api_keys

id

organization_id

name

hashed_key

permissions

expires_at
```

---

# Files

Stores uploaded assets.

```sql
files

id

organization_id

owner_id

filename

mime_type

size

storage_url
```

---

# Notifications

```sql
notifications

id

user_id

type

title

message

read

created_at
```

---

# Audit Logs

One of the most important tables.

Every important action produces an audit record.

```sql
audit_logs

id

organization_id

user_id

agent_id

action

resource

metadata

ip_address

created_at
```

Examples

```text
Workflow Started

Proposal Approved

Wallet Created

Contract Deployed

Treasury Released

User Invited

Role Updated
```

---

# Relationships

```text
User

│

└── Organization

│

├── Projects

├── Agents

├── Wallets

├── Workflows

├── Smart Contracts

└── Audit Logs

Workflow

│

└── Workflow Run

│

└── Agent Executions

│

└── Consensus

│

└── Blockchain Transaction
```

---

# Index Strategy

Indexes

```sql
email

organization_id

workflow_id

agent_id

wallet_id

transaction_hash

created_at

status
```

Composite Indexes

```sql
organization_id + status

workflow_id + created_at

agent_id + status

transaction_hash + network
```

---

# Soft Deletes

Every business table supports

```sql
deleted_at TIMESTAMP NULL
```

No permanent deletion.

Only archival.

---

# Multi-Tenancy

Every row belongs to exactly one organization.

Isolation is enforced through:

* Organization IDs
* Row-Level Security
* RBAC
* API Authorization

No organization can access another organization's data.

---

# Future Tables

Future versions will introduce

* Agent Marketplace
* Agent Reputation
* Prompt Library
* Marketplace Purchases
* Agent Billing
* AI Models
* Plugins
* Team Templates
* Knowledge Bases
* Agent Commerce

---

# Database Summary

The AgentMesh database is designed for enterprise-grade autonomous organizations.

Its architecture emphasizes:

* Security
* Scalability
* Auditability
* Blockchain integration
* AI-native workflows
* Multi-tenancy

Every user action, AI execution, and blockchain transaction is recorded to ensure complete transparency, accountability, and operational trust.

---

## Developed by Tomeku

**Website:** https://tomeku.com

**Facebook:** https://facebook.com/OfficialTomeku

**X:** https://x.com/OfficialTomeku

**YouTube:** https://youtube.com/@OfficialTomeku

© 2026 Tomeku. All Rights Reserved.
