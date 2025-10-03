# MCP Protocol Contracts

**Feature**: LangChain-Drasi Library
**Version**: 1.0
**MCP Specification**: 2025-06-18
**Created**: 2025-10-01

---

## 1. Overview

This document defines the JSON schemas and message formats for Model Context Protocol (MCP) interactions between the LangChain-Drasi library and MCP servers. All messages follow the MCP specification and JSON-RPC 2.0 protocol.

**Key Concepts**:
- All requests and responses use JSON-RPC 2.0 format
- Resource URIs follow the pattern: `drasi://query/{query-name}`
- Notifications are server-initiated messages with no response expected
- Subscriptions are session-based and stateless

---

## 2. Resource Discovery

### 2.1 List Resources Request

**Method**: `resources/list`

**Purpose**: Discover all available Drasi queries

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "method"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "method": {
      "type": "string",
      "const": "resources/list"
    },
    "params": {
      "type": "object",
      "properties": {
        "cursor": {
          "type": "string",
          "description": "Optional pagination cursor for large result sets"
        }
      },
      "additionalProperties": false
    }
  }
}
```

### 2.2 List Resources Response

**Purpose**: Return list of available Drasi queries with metadata

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resources": [
      {
        "name": "active-orders",
        "title": "Active Orders",
        "uri": "drasi://query/active-orders",
        "description": "Continuous query tracking all active customer orders",
        "mimeType": "application/json"
      },
      {
        "name": "freezerx",
        "title": "Freezer Temperature Alert",
        "uri": "drasi://query/freezerx",
        "description": "Freezer temperature alert for when it goes above 32 degrees",
        "mimeType": "application/json"
      }
    ],
    "nextCursor": null
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "result"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "result": {
      "type": "object",
      "required": ["resources"],
      "properties": {
        "resources": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "title", "uri", "description", "mimeType"],
            "properties": {
              "name": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_-]+$",
                "description": "Unique query identifier"
              },
              "title": {
                "type": "string",
                "description": "Human-readable query title"
              },
              "uri": {
                "type": "string",
                "pattern": "^drasi://query/[a-zA-Z0-9_-]+$",
                "description": "Resource URI in format drasi://query/{name}"
              },
              "description": {
                "type": "string",
                "minLength": 1,
                "description": "Description of query purpose and nature"
              },
              "mimeType": {
                "type": "string",
                "const": "application/json",
                "description": "Content MIME type"
              }
            }
          }
        },
        "nextCursor": {
          "type": ["string", "null"],
          "description": "Pagination cursor for next page, null if no more results"
        }
      }
    }
  }
}
```

---

## 3. Resource Reading

### 3.1 Read Resource Request

**Method**: `resources/read`

**Purpose**: Fetch current result set of a Drasi query

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "drasi://query/freezerx"
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "method", "params"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "method": {
      "type": "string",
      "const": "resources/read"
    },
    "params": {
      "type": "object",
      "required": ["uri"],
      "properties": {
        "uri": {
          "type": "string",
          "pattern": "^drasi://query/[a-zA-Z0-9_-]+$",
          "description": "URI of the resource to read"
        }
      },
      "additionalProperties": false
    }
  }
}
```

### 3.2 Read Resource Response

**Purpose**: Return current query result set as JSON

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "contents": [
      {
        "uri": "drasi://query/freezerx",
        "mimeType": "application/json",
        "text": "[\n  {\n    \"id\": 1,\n    \"temp\": 37\n  },\n  {\n    \"id\": 3,\n    \"temp\": 41\n  }\n]"
      }
    ]
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "result"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "result": {
      "type": "object",
      "required": ["contents"],
      "properties": {
        "contents": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["uri", "mimeType", "text"],
            "properties": {
              "uri": {
                "type": "string",
                "pattern": "^drasi://query/[a-zA-Z0-9_-]+$"
              },
              "mimeType": {
                "type": "string",
                "const": "application/json"
              },
              "text": {
                "type": "string",
                "description": "JSON-serialized query result array"
              },
              "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Optional ISO 8601 timestamp"
              }
            }
          }
        }
      }
    }
  }
}
```

**Content Format** (parsed from `text` field):
```json
[
  {
    "id": 1,
    "temp": 37,
    "additionalProperties": "allowed"
  }
]
```

**Content Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "description": "Query result set as array of objects",
  "items": {
    "type": "object",
    "description": "Individual query result row",
    "additionalProperties": true
  }
}
```

---

## 4. Resource Subscription

### 4.1 Subscribe Request

**Method**: `resources/subscribe`

**Purpose**: Subscribe to change notifications for a Drasi query

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/subscribe",
  "params": {
    "uri": "drasi://query/freezerx"
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "method", "params"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "method": {
      "type": "string",
      "const": "resources/subscribe"
    },
    "params": {
      "type": "object",
      "required": ["uri"],
      "properties": {
        "uri": {
          "type": "string",
          "pattern": "^drasi://query/[a-zA-Z0-9_-]+$",
          "description": "URI of the resource to subscribe to"
        }
      },
      "additionalProperties": false
    }
  }
}
```

### 4.2 Subscribe Response

**Purpose**: Confirm subscription was established

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {}
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "result"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "result": {
      "type": "object",
      "description": "Empty object confirms successful subscription",
      "additionalProperties": false
    }
  }
}
```

### 4.3 Unsubscribe Request

**Method**: `resources/unsubscribe`

**Purpose**: Cancel subscription to query notifications

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/unsubscribe",
  "params": {
    "uri": "drasi://query/freezerx"
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "method", "params"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number"]
    },
    "method": {
      "type": "string",
      "const": "resources/unsubscribe"
    },
    "params": {
      "type": "object",
      "required": ["uri"],
      "properties": {
        "uri": {
          "type": "string",
          "pattern": "^drasi://query/[a-zA-Z0-9_-]+$"
        }
      },
      "additionalProperties": false
    }
  }
}
```

### 4.4 Unsubscribe Response

**Purpose**: Confirm subscription was cancelled

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {}
}
```

---

## 5. Change Notifications

### 5.1 Added Notification

**Method**: `notifications/{query-name}/added`

**Purpose**: Notify when a new row is added to query results

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/freezerx/added",
  "params": {
    "freezerId": "2",
    "temperature": "35",
    "description": "Temperature of freezer 2 exceeded threshold"
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "method", "params"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "method": {
      "type": "string",
      "pattern": "^notifications/[a-zA-Z0-9_-]+/added$",
      "description": "Notification method in format: notifications/{query-name}/added"
    },
    "params": {
      "type": "object",
      "description": "Added row data (schema varies by query)",
      "additionalProperties": true,
      "minProperties": 1
    }
  }
}
```

### 5.2 Updated Notification

**Method**: `notifications/{query-name}/updated`

**Purpose**: Notify when an existing row in query results is modified

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/active-orders/updated",
  "params": {
    "orderId": "12345",
    "status": "shipped",
    "updatedAt": "2025-10-01T15:30:00Z"
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "method", "params"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "method": {
      "type": "string",
      "pattern": "^notifications/[a-zA-Z0-9_-]+/updated$",
      "description": "Notification method in format: notifications/{query-name}/updated"
    },
    "params": {
      "type": "object",
      "description": "Updated row data (schema varies by query)",
      "additionalProperties": true,
      "minProperties": 1
    }
  }
}
```

### 5.3 Deleted Notification

**Method**: `notifications/{query-name}/deleted`

**Purpose**: Notify when a row is removed from query results

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/active-orders/deleted",
  "params": {
    "orderId": "12345",
    "deletedAt": "2025-10-01T15:45:00Z"
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "method", "params"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "method": {
      "type": "string",
      "pattern": "^notifications/[a-zA-Z0-9_-]+/deleted$",
      "description": "Notification method in format: notifications/{query-name}/deleted"
    },
    "params": {
      "type": "object",
      "description": "Deleted row identifier data (schema varies by query)",
      "additionalProperties": true,
      "minProperties": 1
    }
  }
}
```

---

## 6. Error Responses

### 6.1 General Error Response

**Purpose**: Communicate errors for any request

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32602,
    "message": "Resource not found",
    "data": {
      "uri": "drasi://query/nonexistent",
      "availableQueries": ["active-orders", "freezerx"]
    }
  }
}
```

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jsonrpc", "id", "error"],
  "properties": {
    "jsonrpc": {
      "type": "string",
      "const": "2.0"
    },
    "id": {
      "type": ["string", "number", "null"]
    },
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": {
          "type": "integer",
          "description": "JSON-RPC error code"
        },
        "message": {
          "type": "string",
          "description": "Human-readable error message"
        },
        "data": {
          "type": "object",
          "description": "Additional error context",
          "additionalProperties": true
        }
      }
    }
  }
}
```

### 6.2 Standard Error Codes

| Code | Name | Description | Usage |
|------|------|-------------|-------|
| -32700 | Parse error | Invalid JSON | Malformed request |
| -32600 | Invalid Request | Not valid JSON-RPC | Missing required fields |
| -32601 | Method not found | Method doesn't exist | Unsupported operation |
| -32602 | Invalid params | Invalid parameters | Wrong URI format, missing params |
| -32603 | Internal error | Server internal error | Unexpected server failure |
| -32000 | Resource not found | Query doesn't exist | Non-existent query URI |
| -32001 | Subscription failed | Cannot subscribe | Subscription error |
| -32002 | Connection failed | Cannot connect to source | Drasi connection issue |

---

## 7. Connection Lifecycle

### 7.1 Initialization Sequence

```
Client                                    MCP Server
  |                                           |
  |------ initialize request --------------->|
  |                                           |
  |<----- initialize response ----------------|
  |        (with server capabilities)         |
  |                                           |
  |------ initialized notification --------->|
  |                                           |
  |  [Connection established, ready for use] |
```

### 7.2 Subscription Lifecycle

```
Client                                    MCP Server
  |                                           |
  |------ resources/subscribe -------------->|
  |                                           |
  |<----- subscription confirmed -------------|
  |                                           |
  |  [Subscription active]                    |
  |                                           |
  |<----- notifications/{query}/added --------|
  |<----- notifications/{query}/updated ------|
  |<----- notifications/{query}/deleted ------|
  |                                           |
  |------ resources/unsubscribe ------------>|
  |                                           |
  |<----- unsubscribe confirmed --------------|
  |                                           |
  |  [Subscription terminated]                |
```

### 7.3 Reconnection Flow

```
Client                                    MCP Server
  |                                           |
  |  [Connection lost]                        X
  |
  |  [Reconnect attempt]
  |                                           |
  |------ initialize request --------------->|
  |<----- initialize response ----------------|
  |------ initialized notification --------->|
  |                                           |
  |  [Re-establish subscriptions]             |
  |------ resources/subscribe (query1) ----->|
  |------ resources/subscribe (query2) ----->|
  |<----- confirmations ----------------------|
  |                                           |
  |  [Subscriptions restored]                 |
```

---

## 8. Validation Rules

### 8.1 URI Format Validation

**Pattern**: `^drasi://query/[a-zA-Z0-9_-]+$`

**Valid Examples**:
- `drasi://query/active-orders`
- `drasi://query/freezerx`
- `drasi://query/user_profile_123`

**Invalid Examples**:
- `drasi://queries/test` (wrong path)
- `drasi://query/test query` (contains space)
- `http://query/test` (wrong scheme)
- `drasi://query/` (missing query name)

### 8.2 Query Name Validation

**Pattern**: `^[a-zA-Z0-9_-]+$`

**Rules**:
- Alphanumeric characters only
- Underscores and hyphens allowed
- No spaces or special characters
- Minimum 1 character
- Case-sensitive

### 8.3 Notification Method Validation

**Pattern**: `^notifications/[a-zA-Z0-9_-]+/(added|updated|deleted)$`

**Components**:
1. Prefix: `notifications/`
2. Query name: `[a-zA-Z0-9_-]+`
3. Separator: `/`
4. Change type: `added|updated|deleted`

**Valid Examples**:
- `notifications/active-orders/added`
- `notifications/freezerx/updated`
- `notifications/user_profile/deleted`

### 8.4 Content Validation

**Query Result Content**:
- Must be valid JSON array
- Array items must be objects
- Empty array is valid
- No maximum size (handled by server)

**Notification Params**:
- Must be valid JSON object
- At least one property required
- Property names are query-specific
- Values can be any JSON type

---

## 9. Transport Considerations

### 9.1 Supported Transports

The MCP protocol can be implemented over multiple transports:

1. **stdio (Standard I/O)**
   - Default for subprocess-based servers
   - Messages via stdin/stdout
   - One message per line

2. **HTTP + SSE (Server-Sent Events)**
   - HTTP POST for requests
   - SSE for server notifications
   - Suitable for web environments

3. **WebSocket**
   - Bidirectional communication
   - Lower latency for notifications
   - Suitable for long-lived connections

### 9.2 Message Framing (stdio)

**Line-Delimited JSON**:
- Each message on a single line
- Terminated by newline (`\n`)
- No pretty-printing or extra whitespace

**Example**:
```
{"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}
{"jsonrpc":"2.0","id":1,"result":{"resources":[...]}}
```

---

## 10. Security Considerations

### 10.1 Input Validation

**Required Validations**:
1. URI scheme must be `drasi://`
2. Query names must match allowed pattern
3. All JSON must be well-formed
4. Parameter types must match schema
5. Resource content must be valid JSON array

### 10.2 Error Information

**Safe Error Messages**:
- Include query name only if it exists
- Don't expose internal paths or system info
- Provide available queries for "not found" errors
- Log detailed errors server-side only

### 10.3 Subscription Security

**Considerations**:
- Validate subscription permissions (if applicable)
- Limit concurrent subscriptions per client
- Implement subscription timeouts
- Clean up orphaned subscriptions

---

## 11. Performance Guidelines

### 11.1 Response Size Limits

| Operation | Recommended Limit | Handling |
|-----------|------------------|----------|
| Resource list | 1000 resources | Use pagination (cursor) |
| Resource read | 10 MB | Consider chunking or streaming |
| Notification params | 100 KB | Keep notifications focused |

### 11.2 Timeout Recommendations

| Operation | Recommended Timeout | Rationale |
|-----------|---------------------|-----------|
| Connection | 30 seconds | Allow for cold start |
| Resource list | 10 seconds | Fast metadata operation |
| Resource read | 60 seconds | May involve query execution |
| Subscribe | 10 seconds | Quick registration |
| Notification delivery | 5 seconds | Real-time requirement |

### 11.3 Batching Strategies

**Not Supported in MCP Spec**:
- Single request per operation
- No request batching (unlike JSON-RPC)
- Client should manage concurrent requests

**Subscription Batching**:
- Client can subscribe to multiple queries
- Each requires separate subscribe request
- Server may optimize internally

---

## 12. Example Interaction Flows

### 12.1 Complete Discovery and Read Flow

```json
// 1. List available queries
→ {"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}

← {"jsonrpc":"2.0","id":1,"result":{"resources":[
    {"name":"freezerx","uri":"drasi://query/freezerx",
     "description":"Freezer alerts","mimeType":"application/json"}
  ],"nextCursor":null}}

// 2. Read specific query
→ {"jsonrpc":"2.0","id":2,"method":"resources/read",
   "params":{"uri":"drasi://query/freezerx"}}

← {"jsonrpc":"2.0","id":2,"result":{"contents":[
    {"uri":"drasi://query/freezerx","mimeType":"application/json",
     "text":"[{\"id\":1,\"temp\":37}]"}
  ]}}
```

### 12.2 Subscribe and Receive Notifications

```json
// 1. Subscribe to query
→ {"jsonrpc":"2.0","id":3,"method":"resources/subscribe",
   "params":{"uri":"drasi://query/freezerx"}}

← {"jsonrpc":"2.0","id":3,"result":{}}

// 2. Receive added notification
← {"jsonrpc":"2.0","method":"notifications/freezerx/added",
   "params":{"freezerId":"2","temperature":"35"}}

// 3. Receive updated notification
← {"jsonrpc":"2.0","method":"notifications/freezerx/updated",
   "params":{"freezerId":"1","temperature":"40"}}

// 4. Unsubscribe
→ {"jsonrpc":"2.0","id":4,"method":"resources/unsubscribe",
   "params":{"uri":"drasi://query/freezerx"}}

← {"jsonrpc":"2.0","id":4,"result":{}}
```

### 12.3 Error Handling Flow

```json
// 1. Try to read non-existent query
→ {"jsonrpc":"2.0","id":5,"method":"resources/read",
   "params":{"uri":"drasi://query/invalid"}}

← {"jsonrpc":"2.0","id":5,"error":{
    "code":-32000,"message":"Resource not found",
    "data":{"uri":"drasi://query/invalid",
            "availableQueries":["freezerx","active-orders"]}
  }}

// 2. List available queries to recover
→ {"jsonrpc":"2.0","id":6,"method":"resources/list","params":{}}

← {"jsonrpc":"2.0","id":6,"result":{"resources":[...]}}
```

---

## 13. Implementation Checklist

### 13.1 Client Implementation Requirements

- [ ] Implement JSON-RPC 2.0 message formatting
- [ ] Support all required request methods (list, read, subscribe, unsubscribe)
- [ ] Parse all notification types (added, updated, deleted)
- [ ] Validate URI format before sending requests
- [ ] Handle error responses appropriately
- [ ] Implement reconnection with subscription restoration
- [ ] Support chosen transport (stdio, HTTP+SSE, or WebSocket)
- [ ] Validate response schemas
- [ ] Parse JSON content from text field
- [ ] Implement timeout handling for all operations

### 13.2 Server Implementation Requirements

- [ ] Implement JSON-RPC 2.0 response formatting
- [ ] Support resource discovery (list)
- [ ] Provide resource content (read)
- [ ] Manage subscriptions (subscribe/unsubscribe)
- [ ] Emit notifications for query changes
- [ ] Generate correct notification method names
- [ ] Validate incoming request schemas
- [ ] Implement error responses with appropriate codes
- [ ] Handle concurrent subscriptions
- [ ] Clean up orphaned subscriptions

---

**Document Status**: Complete
**Last Updated**: 2025-10-01
**Related Documents**:
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/spec.md`
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/contracts/python-api.md`
