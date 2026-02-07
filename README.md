# CXC Discord Rizzbots

Discord bot with true alternation debate analysis using Backboard API.

## Features

- `/setup` - Create debate threads (optimist & pessimist) for your account
- `/analyze` - Run 20-turn alternating debate on your Discord messages
- Global analysis lock (one analysis at a time)
- 60-second cooldown between analyses
- Timeout handling with fallback messages
- PG content filtering

## Setup

1. Install dependencies:
```bash
pip install -r src/requirements.txt
```

2. Create `.env` file with:
```
DISCORD_TOKEN=your_discord_bot_token
BACKBOARD_API_KEY=your_backboard_api_key
BACKBOARD_BASE_URL=https://api.openai.com/v1
OPTIMIST_ASSISTANT_ID=asst_xxxxxxxxxxxxx
PESSIMIST_ASSISTANT_ID=asst_xxxxxxxxxxxxx
```

3. Run bot:
```bash
python src/main.py
```

## Architecture

- `bot.py` - Discord bot with slash commands
- `backboard_client.py` - Backboard/OpenAI API client with timeout handling
- `session.py` - Session management with lock and cooldown
- `prompts.py` - Prompt generation for debate turns and advice
- `main.py` - Entry point

## Debate Flow

1. User runs `/setup` to create two threads (optimist & pessimist)
2. User runs `/analyze` to start debate:
   - Fetch user's recent messages
   - Run 20 alternating turns (Turn 0: Optimist, Turn 1: Pessimist, etc.)
   - Each turn produces one line (max 18 words)
   - After each turn, line is added to other bot's thread
3. After 20 turns, both bots generate 3 pieces of advice
4. Results posted to Discord channel

## Safety

- Global async lock prevents concurrent analyses
- 60-second cooldown between analyses
- Per-run timeout (5 minutes total, 30 seconds per turn)
- Abort with fallback message on timeout (no crashes)
- Content filtering (PG, respectful, no sexual/manipulation)
- Message splitting for Discord limits
