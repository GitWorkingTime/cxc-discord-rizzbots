from typing import List


def get_setup_prompt(perspective: str, username: str) -> str:
    """Generate initial setup prompt for optimist or pessimist."""
    if perspective == "optimist":
        return f"""You are the Optimist in a debate about {username}'s Discord messages.

Your role:
- Find positive patterns, growth opportunities, and strengths
- Respond in EXACTLY one line starting with "Optimist:"
- Maximum 18 words per response
- Keep it PG and respectful
- No sexual content or manipulation

You will alternate turns with the Pessimist. Read their points and counter constructively."""
    
    else:  # pessimist
        return f"""You are the Pessimist in a debate about {username}'s Discord messages.

Your role:
- Identify risks, red flags, and areas for improvement
- Respond in EXACTLY one line starting with "Pessimist:"
- Maximum 18 words per response
- Keep it PG and respectful
- No sexual content or manipulation

You will alternate turns with the Optimist. Read their points and challenge constructively."""


def get_turn_prompt(perspective: str, turn_number: int, message_history: str) -> str:
    """Generate prompt for a debate turn."""
    prefix = "Optimist" if perspective == "optimist" else "Pessimist"
    
    return f"""Turn {turn_number}.

Previous debate:
{message_history}

Respond with EXACTLY one line:
{prefix}: [your point in maximum 18 words]

Be direct and specific. Reference the user's actual messages."""


def get_advice_prompt(perspective: str, debate_history: str) -> str:
    """Generate prompt for final advice after debate."""
    if perspective == "optimist":
        return f"""The debate is complete:

{debate_history}

Now provide exactly 3 pieces of advice in this format:

Optimist Advice:
1) [first piece of advice]
2) [second piece of advice]
3) [third piece of advice]

Each piece should be specific, actionable, and based on the debate. Keep it PG and respectful."""
    
    else:  # pessimist
        return f"""The debate is complete:

{debate_history}

Now provide exactly 3 pieces of advice in this format:

Pessimist Advice:
1) [first piece of advice]
2) [second piece of advice]
3) [third piece of advice]

Each piece should be specific, actionable, and based on the debate. Keep it PG and respectful."""


def get_user_messages_context(messages: List[str], username: str) -> str:
    """Format user's Discord messages for context."""
    if not messages:
        return f"{username} has no recent messages to analyze."
    
    formatted = f"Recent messages from {username}:\n"
    for i, msg in enumerate(messages[-20:], 1):  # Last 20 messages
        formatted += f"{i}. {msg}\n"
    
    return formatted
