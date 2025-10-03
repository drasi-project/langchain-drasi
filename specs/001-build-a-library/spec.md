# Feature Specification: LangChain Extension for Drasi Query Integration

**Feature Branch**: `001-build-a-library`
**Created**: 2025-10-01
**Status**: Draft
**Input**: User description: "Build a library that is an extension on top of LangChain. It builds on the concept of tools to provide a mechanism to read and subscribe to drasi queries. Under the hood, there is an MCP server that will provide MCP resources, the URI scheme is "drasi://query/{query-name}". This follows the MCP spec for resoources: https://modelcontextprotocol.io/specification/2025-06-18/server/resources, reading the resources will return a JSON document. Each resource represents a query and the description field describes what the purpose and nature of each query is. These queries can then be subscribed to, as per the MCP spec. When the result set of the query is changed, the MCP server will emit notifications, with the method of "notifications/{query-name}/added", "notifications/{query-name}/updated" or "notifications/{query-name}/deleted", and the "params" field of these notifications will hold a JSON object describing the change. When these notifcations are received from the underlying MCP server, the Tool implementation must invoke callbacks that were passed to it during construction, these callbacks follow the same principles as the existing callback infrastructure within langchain. Along with this library, there should also be several sample apps that demo the use of this library. There should be a vanilla langchain sample and a langgraph sample. Use Azure OpenAI for these samples."

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
Developers building AI agents need real-time access to data maintained by Drasi queries hosted on remote servers. They want to integrate these dynamic query results into their LangChain-based agents so that the agents can access current data and react to changes as they occur. The library enables developers to connect to remote Drasi MCP servers over HTTP/HTTPS, expose Drasi queries as tools that agents can use to read query results and receive notifications when those results change, allowing agents to respond to data updates in real-time. Agents should be able to discover the queries that are supplied by the MCP server and subscribe or unsubscribe to changes from them. The connection to remote Drasi servers must support authentication via HTTP headers for secure access.

### Acceptance Scenarios
1. **Given** a remote Drasi MCP server URL is configured, **When** the library establishes a connection, **Then** the connection is made over HTTP/HTTPS using the provided URL
2. **Given** authentication headers are configured, **When** the library connects to the MCP server, **Then** the headers are included in all HTTP requests
3. **Given** the MCP connection is established, **When** an agent requests the list of available queries, **Then** the list of queries and their descriptions are returned to the agent
4. **Given** a Drasi query named "active-orders" exists, **When** an agent invokes the tool to read the query, **Then** the current result set is returned as a JSON document
5. **Given** an agent has subscribed to a Drasi query, **When** a new row is added to the query result set, **Then** the agent receives an "added" notification containing the new row data
6. **Given** an agent has subscribed to a Drasi query, **When** an existing row in the result set is modified, **Then** the agent receives an "updated" notification containing the changed row data
7. **Given** an agent has subscribed to a Drasi query, **When** a row is removed from the result set, **Then** the agent receives a "deleted" notification containing information about the removed row
8. **Given** a developer wants to demonstrate the library, **When** they run the vanilla LangChain sample application, **Then** the agent successfully reads from and subscribes to Drasi queries on a remote server
9. **Given** a developer wants to demonstrate the library with state management, **When** they run the LangGraph sample application, **Then** the agent successfully integrates Drasi query tools into its workflow
10. **Given** the MCP connection has not been established, **When** an agent invokes the tool, **Then** the connection must be established to the remote server and held for future use

### Edge Cases
- What happens when a subscription is established but the remote MCP server becomes unavailable?
  - The subscription must be re-created when the MCP server becomes available.
- What happens when the HTTP connection to the remote server times out?
  - Connection errors are raised and retry policies are applied based on configuration
- What happens when authentication headers are invalid or expired?
  - Authentication errors are raised to allow the application to refresh credentials
- What happens when an agent attempts to read or subscribe to a query that doesn't exist?
  - An error is thrown
- What happens when callback execution fails during notification processing?
  - It is up to the consumer of this library to implement error checking in their provided callbacks

### Sample MCP messages

#### Request: Query List

```json
{
  "method": "resources/list",
  "params": {}
}
```

#### Response: Query List

```json
{
  "resources": [
    {
      "name": "freezerx",
      "title": "freezerx",
      "uri": "drasi://query/freezerx",
      "description": "Freezer temperature alert for when it goes above 32 degrees",
      "mimeType": "application/json"
    }
  ]
}
```

#### Request: Query snapshot

```json
{
  "method": "resources/read",
  "params": {
    "uri": "drasi://query/freezerx"
  }
}
```
   
#### Response: Query snapshot

```json
{
  "contents": [
    {
      "uri": "drasi://query/freezerx",
      "mimeType": "application/json",
      "text": "[\n  {\n    \"id\": 1,\n    \"temp\": 37\n  },\n  {\n    \"id\": 3,\n    \"temp\": 41\n  }\n]"
    }
  ]
}
```

#### Request: Subscribe to query

```json
{
  "method": "resources/subscribe",
  "params": {
    "uri": "drasi://query/freezerx"
  }
}
```

#### Change notifications coming from the MCP server

The Drasi MCP server sends change notifications using the standard MCP `notifications/resources/updated` format with Drasi-specific params:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "drasi://query/freezerx",
    "operation": "updated",
    "data": {
      "freezerId": "3",
      "previousTemperature": "43",
      "currentTemperature": "44",
      "description": "Temperature of freezer 3 changed from 43 to 44"
    }
  }
}
```

The params object contains three fields:
- **uri**: The resource URI in the format `drasi://query/{query-name}` identifying which query changed
- **operation**: The type of change - either "added", "updated", or "deleted"
- **data**: The actual change data to be passed to the callback handler

When the library receives a `notifications/resources/updated` notification, it extracts the query name from the URI, determines the callback method from the operation field, and invokes the appropriate callback with the data payload.

## Requirements *(mandatory)*

### Functional Requirements

#### Core Library Capabilities
- **FR-001**: System MUST connect to remote Drasi MCP servers over HTTP/HTTPS using a configured URL
- **FR-002**: System MUST support optional HTTP authentication headers for secure access to remote servers
- **FR-003**: System MUST support configurable request timeout for HTTP operations
- **FR-004**: System MUST provide a mechanism to discover available Drasi queries through resource listing
- **FR-005**: System MUST allow reading the current result set of any Drasi query
- **FR-006**: System MUST allow subscribing to change notifications for any Drasi query
- **FR-007**: System MUST communicate with an MCP server using the MCP resource specification over HTTP
- **FR-008**: System MUST represent each Drasi query as a resource with URI format "drasi://query/{query-name}"
- **FR-009**: System MUST retrieve query purpose and nature in the resource description field
- **FR-010**: System MUST receive standard MCP resource update notifications (notifications/resources/updated) from the server
- **FR-011**: System MUST extract the query name from the notification params URI field (format: drasi://query/{query-name})
- **FR-012**: System MUST route notifications to the appropriate callback method based on the operation field (added, updated, or deleted)
- **FR-013**: System MUST pass the data field from notification params to the invoked callback handler
- **FR-014**: System MUST integrate with LangChain's existing callback infrastructure
- **FR-015**: System MUST invoke user-provided callbacks when notifications are received from the MCP server
- **FR-016**: System MUST allow developers to provide callbacks during tool construction

#### Sample Applications
- **FR-017**: System MUST include a vanilla LangChain sample application demonstrating basic query read and subscription from a remote server
- **FR-018**: System MUST include a LangGraph sample application demonstrating integration with stateful workflows
- **FR-019**: Sample applications MUST demonstrate connecting to Azure OpenAI
- **FR-020**: Sample applications MUST demonstrate typical agent use cases involving reactive data access from remote Drasi servers

#### Error Handling & Resilience
- **FR-021**: System MUST provide configuration options for the user to provide a policy on how to manage connection failures to remote servers
- **FR-022**: System MUST log and continue when a callback throws an exception
- **FR-023**: System MUST let the MCP server handle validation
- **FR-024**: System MUST handle HTTP connection timeouts and network errors appropriately

#### Data & State Management
- **FR-025**: System MUST not maintain any local cache of query results, always fetch from the remote MCP server
- **FR-026**: Subscriptions MUST be session-based only and not persisted across restarts

#### Security & Configuration
- **FR-027**: Sample applications MUST use Environment variables for server URLs, authentication tokens, and secrets
- **FR-028**: Sample applications MUST support reading configuration from `.env` files
- **FR-029**: System MUST allow configuration of HTTP headers for authentication (Bearer tokens, API keys, etc.)

### Key Entities

- **Drasi Query**: Represents a named query maintained by the Drasi system. Contains a query name, description of its purpose, and a dynamic result set that changes over time. Each query is exposed as an MCP resource.

- **Query Result Set**: The current set of rows returned by a Drasi query. Represented as a JSON document containing the data. Changes to this result set trigger notifications.

- **Change Notification**: Represents a modification to a query result set. Contains the change type (added, updated, or deleted), the query name, and the data associated with the change (new row, updated row, or deleted row identifier).

- **MCP Resource**: A standardized resource exposed by the remote MCP server following the MCP specification. Contains URI, name, description, and the JSON content representing the query result. Accessed over HTTP/HTTPS.

- **Tool**: The LangChain tool abstraction that wraps Drasi query access. Provides methods to read query results and subscribe to changes from remote servers, integrating with LangChain's tool ecosystem.

- **Callback Handler**: A user-provided function or handler that gets invoked when change notifications are received from the remote server. Follows LangChain's callback patterns for consistency with the framework.

- **HTTP Connection**: The network connection to the remote Drasi MCP server. Supports HTTPS for secure communication and includes authentication headers when configured.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
