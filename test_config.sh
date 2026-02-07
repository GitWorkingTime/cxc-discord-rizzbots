#!/bin/bash

# Test script for Backboard API and Discord bot configuration
# Run: bash test_config.sh

set -e

echo "=== Testing Backboard API Configuration ==="
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Check required variables
if [ -z "$BACKBOARD_API_KEY" ]; then
    echo "❌ BACKBOARD_API_KEY not set"
    exit 1
fi

if [ -z "$BACKBOARD_BASE_URL" ]; then
    BACKBOARD_BASE_URL="https://api.openai.com/v1"
fi

echo "Using Backboard URL: $BACKBOARD_BASE_URL"
echo ""

# Test 1: Create a thread
echo "Test 1: Creating a thread..."
THREAD_RESPONSE=$(curl -s -X POST "$BACKBOARD_BASE_URL/threads" \
  -H "Authorization: Bearer $BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2")

THREAD_ID=$(echo $THREAD_RESPONSE | grep -o '"id":"thread_[^"]*"' | cut -d'"' -f4)

if [ -z "$THREAD_ID" ]; then
    echo "❌ Failed to create thread"
    echo "Response: $THREAD_RESPONSE"
    exit 1
fi

echo "✅ Thread created: $THREAD_ID"
echo ""

# Test 2: Add a message to the thread
echo "Test 2: Adding a message to thread..."
MESSAGE_RESPONSE=$(curl -s -X POST "$BACKBOARD_BASE_URL/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $BACKBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "role": "user",
    "content": "Hello, this is a test message."
  }')

MESSAGE_ID=$(echo $MESSAGE_RESPONSE | grep -o '"id":"msg_[^"]*"' | cut -d'"' -f4)

if [ -z "$MESSAGE_ID" ]; then
    echo "❌ Failed to add message"
    echo "Response: $MESSAGE_RESPONSE"
    exit 1
fi

echo "✅ Message added: $MESSAGE_ID"
echo ""

# Test 3: List messages in thread
echo "Test 3: Listing messages in thread..."
LIST_RESPONSE=$(curl -s -X GET "$BACKBOARD_BASE_URL/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $BACKBOARD_API_KEY" \
  -H "OpenAI-Beta: assistants=v2")

MESSAGE_COUNT=$(echo $LIST_RESPONSE | grep -o '"object":"thread.message"' | wc -l)

if [ "$MESSAGE_COUNT" -eq "0" ]; then
    echo "❌ No messages found in thread"
    echo "Response: $LIST_RESPONSE"
    exit 1
fi

echo "✅ Found $MESSAGE_COUNT message(s) in thread"
echo ""

echo "=== Testing Discord Bot Tokens ==="
echo ""

# Test Discord Optimist Bot
echo "Test 4: Checking Optimist bot token..."
if [ -z "$OPTIMIST_TOKEN" ]; then
    echo "❌ OPTIMIST_TOKEN not set"
else
    OPTIMIST_CHECK=$(curl -s -X GET "https://discord.com/api/v10/users/@me" \
      -H "Authorization: Bot $OPTIMIST_TOKEN")
    
    OPTIMIST_USERNAME=$(echo $OPTIMIST_CHECK | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$OPTIMIST_USERNAME" ]; then
        echo "❌ Invalid OPTIMIST_TOKEN"
        echo "Response: $OPTIMIST_CHECK"
    else
        echo "✅ Optimist bot: $OPTIMIST_USERNAME"
    fi
fi
echo ""

# Test Discord Pessimist Bot
echo "Test 5: Checking Pessimist bot token..."
if [ -z "$PESSIMIST_TOKEN" ]; then
    echo "❌ PESSIMIST_TOKEN not set"
else
    PESSIMIST_CHECK=$(curl -s -X GET "https://discord.com/api/v10/users/@me" \
      -H "Authorization: Bot $PESSIMIST_TOKEN")
    
    PESSIMIST_USERNAME=$(echo $PESSIMIST_CHECK | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$PESSIMIST_USERNAME" ]; then
        echo "❌ Invalid PESSIMIST_TOKEN"
        echo "Response: $PESSIMIST_CHECK"
    else
        echo "✅ Pessimist bot: $PESSIMIST_USERNAME"
    fi
fi
echo ""

echo "=== Configuration Test Complete ==="
echo ""
echo "Summary:"
echo "- Backboard API: ✅ Working"
echo "- Thread ID: $THREAD_ID (can be used for testing)"
echo ""
echo "Next steps:"
echo "1. Make sure both Discord bots are invited to your server"
echo "2. Run: python src/main.py"
echo "3. Use /setup command in Discord to configure channels"
echo "4. Use /analyze command to start debate analysis"
