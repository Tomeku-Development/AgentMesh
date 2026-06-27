# API Specification

# AgentMesh

**Version:** 1.0.0

**Status:** API Design Specification

**API Version:** v1

**Protocol:** REST + WebSocket

**Developed by:** Tomeku

**Website:** https://tomeku.com

---

# Table of Contents

1. Overview
2. API Philosophy
3. Authentication
4. Authorization
5. REST Endpoints
6. WebSocket Events
7. Error Handling
8. Rate Limiting
9. API Versioning
10. Future APIs

---

# Overview

AgentMesh exposes a RESTful API designed for:

* Organizations
* AI Agents
* Workflows
* Casper Smart Contracts
* Wallets
* Marketplace
* Analytics

Every capability available in the web application is also available through the public API.

Future versions will expose a complete SDK.

---

# Base URL

Production

```http
https://api.agentmesh.ai/v1
```

Development

```http
http://localhost:8000/api/v1
```

---

# Authentication

Preferred

Better Auth

Alternative

Auth.js

Supported Login Methods

* Email
* Google
* GitHub
* Wallet Login (Future)

After authentication

Every request contains

```http
Authorization: Bearer JWT_TOKEN
```

---

# Response Format

Success

```json
{
  "success": true,
  "message": "Workflow created successfully.",
  "data": {}
}
```

Error

```json
{
  "success": false,
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow does not exist."
  }
}
```

---

# HTTP Status Codes

| Code | Meaning          |
| ---- | ---------------- |
| 200  | Success          |
| 201  | Created          |
| 204  | Deleted          |
| 400  | Bad Request      |
| 401  | Unauthorized     |
| 403  | Forbidden        |
| 404  | Not Found        |
| 409  | Conflict         |
| 422  | Validation Error |
| 429  | Rate Limited     |
| 500  | Internal Error   |

---

# Authentication Endpoints

## Register

```http
POST /auth/register
```

Body

```json
{
  "name":"John Doe",
  "email":"john@example.com",
  "password":"********"
}
```

---

## Login

```http
POST /auth/login
```

Returns

```json
{
 "token":"",
 "user":{}
}
```

---

## Logout

```http
POST /auth/logout
```

---

## Refresh Token

```http
POST /auth/refresh
```

---

## Current User

```http
GET /auth/me
```

---

# Organization Endpoints

## List Organizations

```http
GET /organizations
```

---

## Create Organization

```http
POST /organizations
```

Body

```json
{
"name":"Tomeku Labs"
}
```

---

## Organization Details

```http
GET /organizations/{id}
```

---

## Update Organization

```http
PATCH /organizations/{id}
```

---

## Delete Organization

```http
DELETE /organizations/{id}
```

---

## Invite Member

```http
POST /organizations/{id}/members
```

---

## Remove Member

```http
DELETE /organizations/{id}/members/{userId}
```

---

# Project Endpoints

## Create Project

```http
POST /projects
```

Example

```json
{
"title":"Seed Investment",
"description":"Investment proposal"
}
```

---

## List Projects

```http
GET /projects
```

---

## Update Project

```http
PATCH /projects/{id}
```

---

## Delete Project

```http
DELETE /projects/{id}
```

---

# Agent Endpoints

## List Agents

```http
GET /agents
```

---

## Create Agent

```http
POST /agents
```

Example

```json
{
"name":"Finance Agent",
"role":"finance",
"model":"gpt-5.5"
}
```

---

## Get Agent

```http
GET /agents/{id}
```

---

## Update Agent

```http
PATCH /agents/{id}
```

---

## Delete Agent

```http
DELETE /agents/{id}
```

---

## Execute Agent

```http
POST /agents/{id}/execute
```

Example

```json
{
"prompt":"Analyze startup."
}
```

Returns

```json
{
"executionId":"..."
}
```

---

# Workflow Endpoints

## Create Workflow

```http
POST /workflows
```

---

## List Workflows

```http
GET /workflows
```

---

## Get Workflow

```http
GET /workflows/{id}
```

---

## Execute Workflow

```http
POST /workflows/{id}/run
```

---

## Workflow Status

```http
GET /workflow-runs/{id}
```

---

## Cancel Workflow

```http
DELETE /workflow-runs/{id}
```

---

# Consensus API

## Submit Decision

```http
POST /consensus
```

---

## View Consensus

```http
GET /consensus/{id}
```

---

## Consensus History

```http
GET /consensus/history
```

---

# Wallet API

## Create Wallet

```http
POST /wallets
```

---

## Connect Wallet

```http
POST /wallets/connect
```

---

## Wallet Details

```http
GET /wallets/{id}
```

---

## Transactions

```http
GET /wallets/{id}/transactions
```

---

# Casper Smart Contract API

## Deploy Contract

```http
POST /contracts/deploy
```

---

## List Contracts

```http
GET /contracts
```

---

## Execute Contract

```http
POST /contracts/{id}/execute
```

---

## View Contract

```http
GET /contracts/{id}
```

---

# Treasury API

## Treasury Balance

```http
GET /treasury
```

---

## Release Funds

```http
POST /treasury/release
```

---

## Escrow

```http
POST /treasury/escrow
```

---

# Marketplace API

## Browse Marketplace

```http
GET /marketplace
```

---

## Install Agent

```http
POST /marketplace/install
```

---

## Publish Agent

```http
POST /marketplace/publish
```

---

# Files API

Upload

```http
POST /files
```

Download

```http
GET /files/{id}
```

Delete

```http
DELETE /files/{id}
```

---

# Analytics API

Dashboard

```http
GET /analytics/dashboard
```

Organization

```http
GET /analytics/organization
```

Agents

```http
GET /analytics/agents
```

Treasury

```http
GET /analytics/treasury
```

Consensus

```http
GET /analytics/consensus
```

---

# Audit API

List Logs

```http
GET /audit
```

Single Log

```http
GET /audit/{id}
```

---

# Notifications

List

```http
GET /notifications
```

Mark Read

```http
PATCH /notifications/{id}
```

---

# Search API

Universal Search

```http
GET /search?q=investment
```

Returns

Projects

Agents

Organizations

Workflows

Files

Contracts

---

# WebSocket API

Endpoint

```text
wss://api.agentmesh.ai/ws
```

Realtime Events

* Workflow Started
* Workflow Completed
* Agent Finished
* Consensus Updated
* Treasury Released
* Smart Contract Confirmed
* Notification Received

Example

```json
{
"type":"workflow.completed",
"workflowId":"123",
"status":"success"
}
```

---

# Rate Limiting

Authenticated

```text
1000 requests/hour
```

Public

```text
100 requests/hour
```

Premium

Unlimited

---

# Security

Every endpoint validates

* Authentication
* Organization
* RBAC
* Request Signature
* Input Validation

Sensitive endpoints require:

* MFA (Future)
* Wallet Signature
* Human Confirmation

---

# API Versioning

Current

```text
v1
```

Future

```text
v2
```

Breaking changes will never affect previous versions.

---

# Future APIs

Future releases will introduce

* GraphQL API
* MCP Server API
* AI Plugin API
* Agent Marketplace API
* x402 Payment API
* Cross-Chain API
* AI Commerce API
* Organization Federation API

---

# SDK Roadmap

Official SDKs

* JavaScript
* TypeScript
* Python
* Go
* Rust

Future

* Swift
* Kotlin
* .NET

---

# API Design Principles

The AgentMesh API follows five guiding principles:

1. **Consistency** — predictable naming and responses.
2. **Security** — authentication, authorization, and signed operations by default.
3. **Observability** — every action is traceable through audit logs.
4. **Scalability** — stateless services with horizontal scaling.
5. **Developer Experience** — clean REST conventions, OpenAPI support, SDKs, and comprehensive documentation.

The API is designed to power not only the AgentMesh web platform but also third-party integrations, enterprise systems, and autonomous AI agents interacting with the Casper ecosystem.

---

## Developed by Tomeku

**Website:** https://tomeku.com

**Facebook:** https://facebook.com/OfficialTomeku

**X:** https://x.com/OfficialTomeku

**YouTube:** https://youtube.com/@OfficialTomeku

© 2026 Tomeku. All Rights Reserved.
