# Drasi Integration - Debugging Guide

## Changes Made

### 1. Added "all-players" Query

**File:** `resources/queries.yaml`

Added a new continuous query that tracks ALL players (excluding terminators):

```yaml
apiVersion: v1
kind: ContinuousQuery
name: all-players
spec:
  mode: query
  sources:
    subscriptions:
      - id: game
  query: >
    MATCH
      (p:player)
    WHERE NOT p.id STARTS WITH 'T-'
    RETURN
      p.id,
      p.x,
      p.y
```

This query will send notifications whenever:
- A player joins the game (added)
- A player moves (updated)
- A player is eliminated (deleted)

### 2. Enhanced Agent Initialization

**File:** `terminator_agent.py`

- More explicit instructions to the LLM agent
- Tells it to discover queries and subscribe to "all-players"
- Added detailed logging of agent responses
- Prints known players after initialization

### 3. Enhanced Notification Logging

**File:** `terminator_agent.py` - `TerminatorMemory` class

- Logs every notification received (added/updated/deleted)
- Shows the raw notification data for debugging
- Warns if data format is unexpected
- Shows which agent received the notification

### 4. Enhanced Runtime Logging

**File:** `terminator_agent.py` - `run_step()` method

- Shows known players when hunting
- Warns when no players are known (indicates subscription issue)
- More detailed patrol logging

## How to Test

### Step 1: Update Drasi Queries

Apply the updated query configuration:

```bash
cd examples/terminator
drasi apply -f resources/queries.yaml
```

You should see output indicating the `all-players` query was created.

### Step 2: Verify Query in Drasi

Check that the query exists:

```bash
drasi list query
```

You should see both `all-players` and `idle-players` queries.

### Step 3: Start Backend

```bash
./run-backend.sh
```

Watch for: `Started player position broadcast task`

### Step 4: Start Agents with Verbose Output

```bash
./run-agents.sh
```

**Watch for these messages:**

1. **Spawn Messages:**
   ```
   [T-001] Spawned at (x, y)
   [T-002] Spawned at (x, y)
   [T-003] Spawned at (x, y)
   ```

2. **Initialization Messages:**
   ```
   [T-001] Starting initialization - discovering and subscribing to queries...
   ```

3. **Agent Response (if successful):**
   ```
   [T-001] Agent response: I've discovered the following queries...
   [T-001] ✓ Initialization complete - subscribed to queries
   [T-001] Known players: []
   ```

4. **Notification Messages (when players join/move):**
   ```
   [T-001] 🔔 Notification (added) from 'all-players': {'p.id': 'Alice', 'p.x': 10, 'p.y': 15}
   [T-001] ✓ Detected player 'Alice' at (10, 15)
   ```

### Step 5: Join the Game

Open http://localhost:8000 and join with a player name.

**Expected behavior:**

1. Agent terminal should show:
   ```
   [T-001] 🔔 Notification (added) from 'all-players': {'p.id': 'YourName', 'p.x': X, 'p.y': Y}
   [T-001] ✓ Detected player 'YourName' at (X, Y)
   ```

2. When you move:
   ```
   [T-001] 🔔 Notification (updated) from 'all-players': {'p.id': 'YourName', 'p.x': X2, 'p.y': Y2}
   [T-001] ✓ Player 'YourName' moved to (X2, Y2)
   ```

3. Terminators start hunting:
   ```
   [T-001] Hunting player 'YourName' at (X2, Y2) - Known players: ['YourName']
   [T-001] Moved to (X3, Y3) targeting (X2, Y2)
   ```

## Troubleshooting

### Issue: No initialization messages

**Symptom:**
```
[T-001] Spawned at (x, y)
[T-001] ⚠ No known players - patrolling randomly. (Known: [])
```

**Possible causes:**
1. Drasi server not running or not accessible
2. `DRASI_SERVER_URL` incorrect in `.env`
3. Azure OpenAI not configured or quota exceeded

**Debug steps:**
```bash
# Check Drasi server is accessible
curl $DRASI_SERVER_URL/health

# Check .env file
cat .env | grep DRASI_SERVER_URL

# Check Azure OpenAI credentials
cat .env | grep AZURE_OPENAI
```

### Issue: Initialization completes but no notifications

**Symptom:**
```
[T-001] ✓ Initialization complete - subscribed to queries
[T-001] Known players: []
[T-001] ⚠ No known players - patrolling randomly. (Known: [])
```

**Possible causes:**
1. Subscription succeeded but WebSocket connection failed
2. Query not returning data
3. Notification format mismatch

**Debug steps:**

1. Check if query returns data:
   ```bash
   # Use Drasi CLI to read query results
   drasi get query all-players
   ```

2. Check Drasi MCP server logs for errors

3. Verify subscription was created:
   ```bash
   drasi list subscription
   ```

### Issue: Unexpected data format warnings

**Symptom:**
```
[T-001] 🔔 Notification (added) from 'all-players': {'id': 'Alice', 'x': 10, 'y': 15}
[T-001] ⚠ Unexpected data format in notification: {'id': 'Alice', 'x': 10, 'y': 15}
```

**Cause:** Query returns different field names than expected

**Fix:** Update the query in `resources/queries.yaml` to return:
```cypher
RETURN
  p.id,    # Not just 'id'
  p.x,     # Not just 'x'
  p.y      # Not just 'y'
```

Or update `TerminatorMemory` to handle the actual field names.

### Issue: Agent can't connect to Drasi

**Symptom:**
```
[T-001] ✗ Error during initialization: Connection refused
```

**Debug steps:**

1. Verify Drasi MCP server is running:
   ```bash
   ps aux | grep drasi
   netstat -an | grep 8083  # or your DRASI_SERVER_URL port
   ```

2. Check firewall rules

3. Try connecting manually:
   ```bash
   curl -v $DRASI_SERVER_URL
   ```

## Expected Log Output (Success)

When everything works correctly, you should see:

```
Terminator Game - Starting Up
============================================================

Connecting to database: localhost:5432/game
Database connected
Cleared previous terminators

Starting 3 terminator agents...
[T-001] Spawned at (15, 8)
[T-001] Starting initialization - discovering and subscribing to queries...
[T-002] Spawned at (42, 20)
[T-002] Starting initialization - discovering and subscribing to queries...
[T-003] Spawned at (30, 12)
[T-003] Starting initialization - discovering and subscribing to queries...

# ... LLM reasoning ...

[T-001] Agent response: I've discovered 2 queries: 'all-players' and 'idle-players'. I'm now subscribing to 'all-players'...
[T-001] ✓ Initialization complete - subscribed to queries
[T-001] Known players: []

# Player joins...

[T-001] 🔔 Notification (added) from 'all-players': {'p.id': 'Alice', 'p.x': 25, 'p.y': 10}
[T-001] ✓ Detected player 'Alice' at (25, 10)
[T-002] 🔔 Notification (added) from 'all-players': {'p.id': 'Alice', 'p.x': 25, 'p.y': 10}
[T-002] ✓ Detected player 'Alice' at (25, 10)
[T-003] 🔔 Notification (added) from 'all-players': {'p.id': 'Alice', 'p.x': 25, 'p.y': 10}
[T-003] ✓ Detected player 'Alice' at (25, 10)

# Terminators start hunting...

[T-001] Hunting player 'Alice' at (25, 10) - Known players: ['Alice']
[T-001] Moved to (16, 8) targeting (25, 10)
[T-002] Hunting player 'Alice' at (25, 10) - Known players: ['Alice']
[T-002] Moved to (41, 20) targeting (25, 10)
```

## Next Steps

1. Apply the updated queries: `drasi apply -f resources/queries.yaml`
2. Restart the agents: `./run-agents.sh`
3. Join the game and watch the logs
4. If you see notification messages, Drasi integration is working!
5. If not, check the troubleshooting section above

## Quick Diagnostic Checklist

- [ ] Drasi server is running
- [ ] `DRASI_SERVER_URL` is correct in `.env`
- [ ] Queries applied: `drasi list query` shows `all-players`
- [ ] Azure OpenAI credentials configured
- [ ] Backend running with broadcast task
- [ ] Agents initialized without errors
- [ ] Notification messages appear when players join/move
- [ ] Terminators hunt players (not just random patrol)
