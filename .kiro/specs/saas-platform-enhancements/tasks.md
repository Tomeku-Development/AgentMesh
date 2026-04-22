# Implementation Plan: SaaS Platform Enhancements

## Overview

Six enhancements to the MESH SaaS platform: analytics, webhooks, scenarios, SLA monitoring, enhanced RBAC, and agent marketplace. All follow the existing FastAPI patterns (routers → services → models) with SQLAlchemy 2.0 async models and Pydantic schemas. Tasks are ordered for maximum visible impact first, with related work grouped to minimize context switching.

## Tasks

- [x] 1. Extend RBAC roles and add new dependency functions
  - [x] 1.1 Extend WorkspaceRole enum and add role hierarchy
    - In `mesh_platform/models/workspace.py`, extend `WorkspaceRole` enum to add `operator`, `developer`, and `auditor` roles
    - Add `ROLE_LEVELS` dict mapping each role to its numeric level: owner=6, admin=5, operator=4, developer=3, auditor=2, viewer=1
    - _Requirements: 5.1_
  - [x] 1.2 Add new RBAC dependency functions
    - In `mesh_platform/dependencies.py`, add `require_workspace_operator` (permits owner, admin, operator), `require_workspace_auditor` (permits owner, admin, auditor), and `require_workspace_developer` (permits owner, admin, developer)
    - Each function checks membership role against the permitted set and raises 403 if not authorized
    - Follow the existing `require_workspace_admin` pattern
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  - [x] 1.3 Add role assignment endpoint with escalation prevention
    - Add `PUT /workspaces/{workspace_id}/members/{user_id}/role` endpoint to `mesh_platform/routers/workspaces.py`
    - Validate that the assigning user's role level is strictly greater than the target role level using `ROLE_LEVELS`
    - Prevent self-escalation: reject if user tries to assign themselves a higher role
    - Create Pydantic schema for the role update request/response
    - _Requirements: 5.6, 5.7_
  - [x] 1.4 Write property tests for RBAC permission checks
    - **Property 7: RBAC permission check**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**
  - [x] 1.5 Write property test for role escalation prevention
    - **Property 8: Role escalation prevention**
    - **Validates: Requirements 5.7**

- [x] 2. Implement Agent Performance Analytics
  - [x] 2.1 Create analytics service with aggregation queries
    - Create `mesh_platform/services/analytics_service.py`
    - Implement `get_agent_metrics(db, workspace_id, days)`: query `OrderEvent` grouped by `agent_id` for total orders, success rate (settled count / total), average settlement time; join latest `ReputationSnapshot` for current score
    - Implement `get_order_timeline(db, workspace_id, days)`: for each order, compute duration between consecutive `OrderEvent` phase transitions
    - Implement `get_economic_health(db, workspace_id, days)`: aggregate `LedgerEntry` for total volume, avg transaction size, count by tx_type; compute escrow utilization from `EscrowRecord`; compute burn amount
    - Return zero-valued metrics when no data exists (not errors)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 2.2 Create analytics Pydantic schemas
    - Create `mesh_platform/schemas/analytics.py` with response models for agent metrics, order timeline, and economic health
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 2.3 Create analytics router with three endpoints
    - Create `mesh_platform/routers/analytics.py` with three GET endpoints under `/workspaces/{workspace_id}/analytics/`
    - Endpoints: `agents`, `orders/timeline`, `economic`
    - All accept `days` query parameter (default 30, range 1-365)
    - Use `require_workspace_admin` dependency for auth
    - Register router in `mesh_platform/app.py` with `/api/v1` prefix
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 2.4 Write property test for analytics aggregation correctness
    - **Property 1: Analytics aggregation correctness**
    - **Validates: Requirements 1.1, 1.3**
  - [x] 2.5 Write property test for order lifecycle duration computation
    - **Property 2: Order lifecycle duration computation**
    - **Validates: Requirements 1.2**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Custom Scenario Builder
  - [x] 4.1 Create scenario model
    - Create `mesh_platform/models/scenario.py` with `Scenario` SQLAlchemy model
    - Fields: id (uuid4), workspace_id (FK), name (3-200 chars), description, duration_seconds, definition_json (Text), is_system (bool, default False), created_at, updated_at
    - _Requirements: 3.1_
  - [x] 4.2 Create scenario Pydantic schemas with validation
    - Create `mesh_platform/schemas/scenario.py` with request/response models
    - Define `ScenarioDefinition` Pydantic model with nested `AgentConfig`, `GoodsDefinition`, `OrderConfig`, `ChaosEventConfig`
    - Add validators: at least one buyer agent, at least one supplier agent, at least one goods definition, goods must have non-empty name/category and base_price > 0
    - _Requirements: 3.1, 3.2, 3.7_
  - [x] 4.3 Create scenario service with CRUD operations
    - Create `mesh_platform/services/scenario_service.py`
    - Implement create, list (including built-in system scenarios from `mesh/scenarios/`), get, update, delete
    - Serialize/deserialize scenario definitions to/from JSON
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.6_
  - [x] 4.4 Create scenario router with CRUD endpoints
    - Create `mesh_platform/routers/scenarios.py` with POST, GET (list), GET (detail), PUT, DELETE under `/workspaces/{workspace_id}/scenarios`
    - Use `require_workspace_owner` for create/update/delete, `get_workspace` for list/get (viewer+ access)
    - Register router in `mesh_platform/app.py`
    - _Requirements: 3.1, 3.3, 3.5, 3.6_
  - [x] 4.5 Write property test for scenario serialization round-trip
    - **Property 4: Scenario serialization round-trip**
    - **Validates: Requirements 3.1, 3.4**
  - [x] 4.6 Write property test for scenario validation rejects invalid definitions
    - **Property 5: Scenario validation rejects invalid definitions**
    - **Validates: Requirements 3.2, 3.7**

- [x] 5. Implement Agent Marketplace
  - [x] 5.1 Create marketplace model
    - Create `mesh_platform/models/marketplace.py` with `AgentTemplate` SQLAlchemy model
    - Fields: id (uuid4), name (unique, 3-100 chars), description, agent_role, capabilities_json (Text), default_initial_balance, config_json (Text), author_id (FK users.id), usage_count (default 0), created_at, updated_at
    - _Requirements: 6.1_
  - [x] 5.2 Create marketplace Pydantic schemas
    - Create `mesh_platform/schemas/marketplace.py` with request/response models
    - Include `TemplateCreate`, `TemplateUpdate`, `TemplateResponse`, `InstantiateRequest` schemas
    - Add name validation (3-100 chars)
    - _Requirements: 6.1, 6.4, 6.6_
  - [x] 5.3 Create marketplace service
    - Create `mesh_platform/services/marketplace_service.py`
    - Implement register, search (text search on name/description, filter by role/capability, order by usage_count DESC), get, update (author only), instantiate (create AgentDefinition from template defaults + overrides, increment usage_count)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_
  - [x] 5.4 Create marketplace router
    - Create `mesh_platform/routers/marketplace.py`
    - Global endpoints: POST/GET/GET-detail/PUT under `/marketplace/templates`
    - Workspace-scoped: POST `/workspaces/{workspace_id}/marketplace/instantiate/{template_id}` (require admin+)
    - Register router in `mesh_platform/app.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.7_
  - [x] 5.5 Write property test for marketplace search filtering and ordering
    - **Property 9: Marketplace search returns filtered and ordered results**
    - **Validates: Requirements 6.2**
  - [x] 5.6 Write property test for template instantiation merge
    - **Property 10: Template instantiation merges defaults with overrides**
    - **Validates: Requirements 6.4**
  - [x] 5.7 Write property test for template name validation
    - **Property 11: Template name validation**
    - **Validates: Requirements 6.6**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Webhook and Integration Layer
  - [x] 7.1 Create webhook models
    - Create `mesh_platform/models/webhook.py` with `WebhookRegistration` and `WebhookDelivery` SQLAlchemy models
    - WebhookRegistration: id, workspace_id, url, event_types (JSON array as Text), secret, is_active, created_at
    - WebhookDelivery: id, webhook_id, event_type, payload_json, status, http_status_code, response_body, attempt_number, delivered_at, created_at
    - _Requirements: 2.1, 2.4_
  - [x] 7.2 Create webhook Pydantic schemas
    - Create `mesh_platform/schemas/webhook.py` with request/response models
    - Include HTTPS URL validation for webhook registration
    - Include inbound trigger request schema
    - _Requirements: 2.1, 2.5, 2.6_
  - [x] 7.3 Create webhook service with delivery logic
    - Create `mesh_platform/services/webhook_service.py`
    - Implement register, list, delete, get delivery history
    - Implement `dispatch_event(db, workspace_id, event_type, payload)`: query matching webhooks, create WebhookDelivery records, fire async httpx.post with HMAC-SHA256 signature header (`X-Mesh-Signature: sha256={hmac}`)
    - Implement retry logic (up to 3 attempts with exponential backoff)
    - Implement inbound trigger: create Order record and publish MQTT message
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  - [x] 7.4 Create webhook router
    - Create `mesh_platform/routers/webhooks.py` with POST/GET/DELETE for webhook registrations, GET for delivery history, POST for inbound trigger
    - Use `require_workspace_owner` for webhook management, `require_workspace_operator` for inbound trigger
    - Register router in `mesh_platform/app.py`
    - _Requirements: 2.1, 2.5, 2.7_
  - [x] 7.5 Write property test for webhook HTTPS URL validation
    - **Property 3: Webhook HTTPS URL validation**
    - **Validates: Requirements 2.6**

- [x] 8. Implement SLA Monitoring and Alerts
  - [x] 8.1 Create SLA models
    - Create `mesh_platform/models/sla.py` with `SLARule` and `SLAAlert` SQLAlchemy models
    - SLARule: id, workspace_id, metric_type, threshold, operator, check_interval_seconds, is_active, created_at
    - SLAAlert: id, workspace_id, rule_id, metric_type, actual_value, threshold_value, breached_at, acknowledged, acknowledged_by, acknowledged_at
    - _Requirements: 4.1, 4.3_
  - [x] 8.2 Create SLA Pydantic schemas
    - Create `mesh_platform/schemas/sla.py` with request/response models for rules and alerts
    - Validate metric_type is one of: order_settlement_time, agent_uptime, order_success_rate
    - Validate operator is one of: less_than, greater_than
    - _Requirements: 4.1_
  - [x] 8.3 Create SLA service with evaluation logic
    - Create `mesh_platform/services/sla_service.py`
    - Implement CRUD for SLA rules (create, list, delete)
    - Implement metric computation: order_settlement_time (avg seconds from request to settled), agent_uptime (% active heartbeats), order_success_rate (% settled orders)
    - Implement `evaluate_rules(db, workspace_id)`: for each active rule, compute metric, compare against threshold using operator, create SLAAlert on breach
    - Implement alert listing (unacknowledged, ordered by breached_at DESC) and acknowledgment
    - Handle division-by-zero: return 0.0 default when no data exists
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - [x] 8.4 Create SLA router
    - Create `mesh_platform/routers/sla.py` with endpoints for rule CRUD, evaluation trigger, alert listing, and alert acknowledgment
    - All endpoints require `require_workspace_admin` dependency
    - Register router in `mesh_platform/app.py`
    - _Requirements: 4.1, 4.2, 4.4, 4.5_
  - [x] 8.5 Write property test for SLA breach detection correctness
    - **Property 6: SLA breach detection correctness**
    - **Validates: Requirements 4.2**

- [x] 9. Update conftest and register all new models
  - Update `platform_tests/conftest.py` to import all new models (WebhookRegistration, WebhookDelivery, Scenario, SLARule, SLAAlert, AgentTemplate) so SQLite test DB creates all tables
  - _Requirements: all_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- RBAC is implemented first because all other features depend on the new role dependencies
- Analytics and scenarios are prioritized for maximum visible impact
- Checkpoints ensure incremental validation
- Property tests use Hypothesis with minimum 100 iterations per property
- All new routers register in `app.py` with `/api/v1` prefix following existing patterns
