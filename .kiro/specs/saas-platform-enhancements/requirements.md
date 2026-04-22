# Requirements Document

## Introduction

This document specifies six SaaS platform enhancements for the MESH decentralized multi-agent supply chain coordination system. These enhancements are scoped for a 2–4 hour implementation window targeting the Vertex Swarm Challenge 2026 submission. The focus is on delivering maximum visible impact: API endpoints with aggregation queries over existing PostgreSQL data, new database models for webhooks/scenarios/SLAs/marketplace, expanded RBAC roles, and targeted dashboard components where time permits.

The existing platform already persists all MQTT events (orders, bids, ledger transactions, escrow, reputation updates, heartbeats) to PostgreSQL via the event sink. The enhancements build on this foundation.

## Glossary

- **Platform_API**: The FastAPI REST API at `mesh_platform/` serving `/api/v1/*` endpoints
- **Dashboard**: The SvelteKit real-time UI at `dashboard/`
- **Event_Sink**: The MQTT subscriber process that persists MQTT events to PostgreSQL
- **Workspace**: A multi-tenant isolation unit with its own agents, orders, and configuration
- **Agent**: An autonomous agent instance (Buyer, Supplier, Logistics, Inspector, Oracle) operating within a workspace
- **Order**: A supply chain purchase order that progresses through protocol phases (DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE)
- **OrderEvent**: An event-sourced record of a state transition on an order
- **LedgerEntry**: A double-entry accounting record of a MESH_CREDIT transfer
- **ReputationEvent**: A record of a reputation score change for an agent capability
- **SLA**: A Service Level Agreement defining performance thresholds for a workspace
- **Webhook**: An outbound HTTP POST notification sent when a MESH event occurs
- **Scenario**: A configurable supply chain simulation defining agent roles, goods catalogs, order timelines, and chaos events
- **Agent_Template**: A reusable agent configuration (role, capabilities, initial balance, parameters) that can be registered and discovered
- **RBAC**: Role-Based Access Control governing what actions a workspace member can perform
- **WorkspaceMembership**: The association between a User and a Workspace, including the assigned role

## Requirements

### Requirement 1: Agent Performance Analytics

**User Story:** As a workspace admin, I want to view historical analytics on agent performance, so that I can understand how agents are behaving over time and identify bottlenecks.

#### Acceptance Criteria

1. WHEN a workspace admin requests agent analytics for a time range, THE Platform_API SHALL return per-agent metrics including total orders handled, average settlement time in seconds, success rate as a percentage, and current reputation score
2. WHEN a workspace admin requests order lifecycle timelines, THE Platform_API SHALL return the duration in seconds between each OrderEvent phase transition for each order in the workspace
3. WHEN a workspace admin requests economic health metrics, THE Platform_API SHALL return aggregate LedgerEntry statistics including total volume, average transaction size, escrow utilization rate, and burn amount for the workspace within the specified time range
4. THE Platform_API SHALL compute agent analytics from existing OrderEvent, LedgerEntry, ReputationEvent, and AgentStatusLog tables using aggregation queries
5. WHEN no data exists for the requested time range, THE Platform_API SHALL return zero-valued metrics with an empty results array rather than an error

### Requirement 2: Webhook and Integration Layer

**User Story:** As a workspace owner, I want to configure outbound webhooks so that external systems receive notifications when MESH events occur, and I want to trigger order creation from external systems.

#### Acceptance Criteria

1. WHEN a workspace owner creates a webhook registration, THE Platform_API SHALL store the target URL, event types to subscribe to, and an HMAC secret for signature verification
2. WHEN an MQTT event matching a registered webhook's event types is persisted by the Event_Sink, THE Platform_API SHALL send an HTTP POST to the webhook URL within 30 seconds containing the event payload and an HMAC-SHA256 signature header
3. IF a webhook delivery fails with a non-2xx response, THEN THE Platform_API SHALL retry delivery up to 3 times with exponential backoff (delays of 10, 30, and 90 seconds)
4. WHEN a webhook delivery permanently fails after all retries, THE Platform_API SHALL record the failure in a delivery log with the HTTP status code and response body
5. WHEN an external system sends a valid POST request to the inbound trigger endpoint with order parameters, THE Platform_API SHALL create an Order record and publish the corresponding MQTT message to the workspace topic
6. THE Platform_API SHALL validate that webhook URLs use HTTPS protocol before accepting registration
7. WHEN a workspace owner requests webhook delivery history, THE Platform_API SHALL return the last 100 delivery attempts with status, response code, and timestamp

### Requirement 3: Custom Scenario Builder

**User Story:** As a workspace owner, I want to configure custom supply chain scenarios with specific agent roles, goods catalogs, and pricing rules, so that I can simulate different supply chain configurations instead of using only the hardcoded demo.

#### Acceptance Criteria

1. WHEN a workspace owner creates a scenario, THE Platform_API SHALL store the scenario definition including a name, description, duration, list of agent role configurations, goods catalog, order timeline, and optional chaos events
2. THE Platform_API SHALL validate that each scenario contains at least one buyer agent, one supplier agent, and one goods definition
3. WHEN a workspace owner lists scenarios, THE Platform_API SHALL return all scenarios belonging to the workspace plus the built-in system scenarios
4. THE Platform_API SHALL serialize scenario definitions to JSON and deserialize them back to equivalent objects (round-trip property)
5. WHEN a workspace owner updates a scenario, THE Platform_API SHALL replace the stored definition and return the updated scenario
6. WHEN a workspace owner deletes a scenario, THE Platform_API SHALL remove the scenario record and return a confirmation
7. THE Platform_API SHALL validate that goods definitions include a name, category, and base price greater than zero

### Requirement 4: SLA Monitoring and Alerts

**User Story:** As a workspace admin, I want to define SLA rules for my workspace and receive alerts when they are breached, so that I can monitor system health and respond to performance degradation.

#### Acceptance Criteria

1. WHEN a workspace admin creates an SLA rule, THE Platform_API SHALL store the rule with a metric type (order_settlement_time, agent_uptime, or order_success_rate), a threshold value, a comparison operator (less_than, greater_than), and a check interval in seconds
2. WHEN the SLA evaluation runs, THE Platform_API SHALL compare the current metric value against each active SLA rule's threshold and create an alert record for each breach
3. WHEN an SLA breach is detected, THE Platform_API SHALL record an alert with the SLA rule ID, the actual metric value, the threshold value, and the breach timestamp
4. WHEN a workspace admin requests active alerts, THE Platform_API SHALL return all unacknowledged alerts for the workspace ordered by breach timestamp descending
5. WHEN a workspace admin acknowledges an alert, THE Platform_API SHALL mark the alert as acknowledged with the acknowledging user ID and timestamp
6. THE Platform_API SHALL evaluate SLA rules by querying OrderEvent timestamps and AgentStatusLog records from the existing database tables

### Requirement 5: Enhanced RBAC

**User Story:** As a workspace owner, I want to assign granular roles (operator, auditor, developer) to workspace members beyond the current owner/admin/viewer roles, so that I can control access to specific platform features.

#### Acceptance Criteria

1. THE Platform_API SHALL support six workspace roles: owner, admin, operator, auditor, developer, and viewer
2. WHEN a request requires admin-level access, THE Platform_API SHALL permit users with owner or admin roles and deny users with operator, auditor, developer, or viewer roles
3. WHEN a request targets agent management or scenario execution endpoints, THE Platform_API SHALL permit users with owner, admin, or operator roles
4. WHEN a request targets analytics, audit logs, or webhook delivery history endpoints, THE Platform_API SHALL permit users with owner, admin, or auditor roles
5. WHEN a request targets API key management or SDK-related endpoints, THE Platform_API SHALL permit users with owner, admin, or developer roles
6. WHEN a workspace owner assigns a role to a member, THE Platform_API SHALL update the WorkspaceMembership record and return the updated membership
7. THE Platform_API SHALL prevent any member from escalating their own role to a level higher than their current role

### Requirement 6: Agent Marketplace (Lightweight)

**User Story:** As a developer, I want to register custom agent templates and discover templates created by others, so that I can reuse proven agent configurations across workspaces.

#### Acceptance Criteria

1. WHEN a developer registers an agent template, THE Platform_API SHALL store the template with a name, description, agent role, default capabilities list, default initial balance, configuration parameters as JSON, and the author's user ID
2. WHEN a user searches the marketplace, THE Platform_API SHALL return templates matching the search query filtered by role or capability, ordered by usage count descending
3. WHEN a user requests a specific template, THE Platform_API SHALL return the full template definition including configuration parameters
4. WHEN a workspace admin instantiates a template, THE Platform_API SHALL create an AgentDefinition in the target workspace using the template's defaults, allowing parameter overrides
5. THE Platform_API SHALL track a usage count on each template that increments when the template is instantiated
6. THE Platform_API SHALL validate that template names are unique within the system and contain between 3 and 100 characters
7. WHEN a template author updates their template, THE Platform_API SHALL replace the stored definition and return the updated template
