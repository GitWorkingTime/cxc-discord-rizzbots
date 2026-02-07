# CXC Discord Rizzbots

Discord bot system with TWO separate bot accounts (Optimist & Pessimist) running in one process, coordinating true alternation debate analysis using Backboard API.

## Architecture

```
main.py                  # Entry point, runs both bots in one process
bot_optimist.py          # Optimist bot client with /setup and /analyze commands
bot_pessimist.py         # Pessimist bot client (no commands, only posting)
orchestrator.py          # Shared state, message buffers, cooldown, lock, posting router
backboard_client.py      # REST API client for Backboard/OpenAI
prompts.py               # Prompt generation for debate turns and advice
session.py               # Session data structures (threads, channels, users)
```

## Features

### Commands (Optimist bot only)

- `/setup` - Configure channels and create threads for two players
  - Parameters: player1, player2, general channel, player1 room, player2 room, assistant IDs
  - Creates Backboard threads for both players
  
- `/analyze` - Run 20-turn alternating debate on buffered messages
  - Analyzes last 25 messages from general channel
  - True alternation: Turn 0 Optimist, Turn 1 Pessimist, etc.
  - Each turn produces one line (max 18 words)
  - After each line, adds it to other bot's thread as context
  - Finally, both bots output 3 pieces of advice

### Posting Router

- Optimist lines posted by Optimist bot account
- Pessimist lines posted by Pessimist bot account
- Real-time streaming to player-specific rooms

### Safety Features

- Global async lock (one analysis at a time)
- 60-second cooldown between analyses
- Per-run timeout handling (5 min total, 30s per turn)
- Graceful abort with fallback messages
- PG content filtering (respectful, no sexual/manipulation)
- Message splitting for Discord limits (<1900 chars)

## Setup

1. Install dependencies:
```bash
pip install -r src/requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Configure `.env`:
```env
OPTIMIST_TOKEN=your_optimist_bot_token
PESSIMIST_TOKEN=your_pessimist_bot_token
BACKBOARD_API_KEY=your_backboard_api_key
BACKBOARD_BASE_URL=https://app.backboard.io/api
BACKBOARD_LLM_PROVIDER=openai
```

4. Invite both bots to your Discord server with appropriate permissions:
   - Read Messages/View Channels
   - Send Messages
   - Use Slash Commands

5. Run:
```bash
python src/main.py
```

## Usage Flow

1. Admin runs `/setup` on Optimist bot:
   - Select player1, player2
   - Select general channel (where messages are buffered)
   - Select player1_room and player2_room (where results go)
   - Provide assistant IDs for Optimist and Pessimist

2. Both bots buffer messages from general channel (last 25)

3. Anyone runs `/analyze` on Optimist bot:
   - Checks cooldown (60s)
   - Acquires global lock
   - For each player:
     - Runs 20-turn debate (Optimist/Pessimist alternating)
     - Posts each line in real-time using correct bot account
     - After 20 turns, generates 3 pieces of advice from each bot
     - Posts advice to player's room

## Debate Flow

For each user:
1. Initialize Optimist and Pessimist threads with setup prompts + message context
2. Run 20 alternating turns:
   - Turn 0: Optimist generates line → add to Pessimist thread
   - Turn 1: Pessimist generates line → add to Optimist thread
   - Turn 2: Optimist generates line → add to Pessimist thread
   - ... (continue alternating)
3. After 20 lines:
   - Optimist generates "Optimist Advice: 1) ... 2) ... 3) ..."
   - Pessimist generates "Pessimist Advice: 1) ... 2) ... 3) ..."

## Development

Type hints and logging throughout. Clean separation of concerns:
- Bot logic in bot_*.py
- Coordination in orchestrator.py
- API calls in backboard_client.py
- State management in session.py
- Prompts in prompts.py
