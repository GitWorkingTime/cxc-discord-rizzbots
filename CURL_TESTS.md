# Manual curl commands for testing Backboard API

## Test 1: Create a thread
```bash
curl -X GET "https://app.backboard.io/api/threads" \
  -H "X-API-Key: YOUR_BACKBOARD_API_KEY"
```

Expected response:
```json
{
  "id": "thread_abc123...",
  "object": "thread",
  "created_at": 1234567890,
  ...
}
```

## Test 2: Add a message to thread
```bash
curl -X POST "https://app.backboard.io/api/threads/THREAD_ID/messages" \
  -H "X-API-Key: YOUR_BACKBOARD_API_KEY" \
  -F 'content=Hello, this is a test message.' \
  -F 'send_to_llm=true'
```

Expected response:
```json
{
  "id": "msg_abc123...",
  "object": "thread.message",
  "thread_id": "thread_abc123...",
  ...
}
```

## Test 3: List messages in thread
```bash
curl -X GET "https://app.backboard.io/api/threads/THREAD_ID" \
  -H "X-API-Key: YOUR_BACKBOARD_API_KEY"
```

Expected response:
```json
{
  "object": "list",
  "data": [
    {
      "id": "msg_abc123...",
      "object": "thread.message",
      ...
    }
  ]
}
```

## Test 4: Create a run (with assistant)
```bash
curl -X POST "https://app.backboard.io/api/assistants/ASSISTANT_ID/threads" \
  -H "X-API-Key: YOUR_BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected response:
```json
{
  "id": "run_abc123...",
  "object": "thread.run",
  "status": "queued",
  ...
}
```

## Test 5: Check run status
```bash
curl -X POST "https://app.backboard.io/api/threads/THREAD_ID/runs/RUN_ID/submit-tool-outputs" \
  -H "X-API-Key: YOUR_BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tool_outputs":[{"tool_call_id":"","output":""}]}'
```

Expected response:
```json
{
  "id": "run_abc123...",
  "object": "thread.run",
  "status": "completed",  // or "in_progress", "queued", etc.
  ...
}
```

## Test Discord Bot Token (Optimist)
```bash
curl -X GET "https://discord.com/api/v10/users/@me" \
  -H "Authorization: Bot YOUR_OPTIMIST_TOKEN"
```

Expected response:
```json
{
  "id": "123456789...",
  "username": "OptimistBot",
  "discriminator": "0000",
  ...
}
```

## Test Discord Bot Token (Pessimist)
```bash
curl -X GET "https://discord.com/api/v10/users/@me" \
  -H "Authorization: Bot YOUR_PESSIMIST_TOKEN"
```

Expected response:
```json
{
  "id": "987654321...",
  "username": "PessimistBot",
  "discriminator": "0000",
  ...
}
```

## Quick test script
Replace YOUR_BACKBOARD_API_KEY with your actual key:

```bash
# Set your API key
export BACKBOARD_API_KEY="sk-..."

# Create thread and capture ID
THREAD_ID=$(curl -s -X GET "https://app.backboard.io/api/threads" \
  -H "X-API-Key: $BACKBOARD_API_KEY" | grep -o '"thread_id":"[^"]*"' | head -n1 | cut -d'"' -f4)

echo "Created thread: $THREAD_ID"

# Add message
curl -X POST "https://app.backboard.io/api/threads/$THREAD_ID/messages" \
  -H "X-API-Key: $BACKBOARD_API_KEY" \
  -F 'content=Test message' \
  -F 'send_to_llm=true'

# List messages
curl -X GET "https://app.backboard.io/api/threads/$THREAD_ID" \
  -H "X-API-Key: $BACKBOARD_API_KEY"
```
