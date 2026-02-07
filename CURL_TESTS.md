# Manual curl commands for testing Backboard API

## Test 1: Create a thread
```bash
curl -X POST "https://api.openai.com/v1/threads" \
  -H "Authorization: Bearer YOUR_BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2"
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
curl -X POST "https://api.openai.com/v1/threads/THREAD_ID/messages" \
  -H "Authorization: Bearer YOUR_BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "role": "user",
    "content": "Hello, this is a test message."
  }'
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
curl -X GET "https://api.openai.com/v1/threads/THREAD_ID/messages" \
  -H "Authorization: Bearer YOUR_BACKBOARD_API_KEY" \
  -H "OpenAI-Beta: assistants=v2"
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
curl -X POST "https://api.openai.com/v1/threads/THREAD_ID/runs" \
  -H "Authorization: Bearer YOUR_BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "assistant_id": "asst_YOUR_ASSISTANT_ID"
  }'
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
curl -X GET "https://api.openai.com/v1/threads/THREAD_ID/runs/RUN_ID" \
  -H "Authorization: Bearer YOUR_BACKBOARD_API_KEY" \
  -H "OpenAI-Beta: assistants=v2"
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
THREAD_ID=$(curl -s -X POST "https://api.openai.com/v1/threads" \
  -H "Authorization: Bearer $BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" | grep -o '"id":"thread_[^"]*"' | cut -d'"' -f4)

echo "Created thread: $THREAD_ID"

# Add message
curl -X POST "https://api.openai.com/v1/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{"role": "user", "content": "Test message"}'

# List messages
curl -X GET "https://api.openai.com/v1/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $BACKBOARD_API_KEY" \
  -H "OpenAI-Beta: assistants=v2"
```
