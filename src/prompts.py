from typing import List, Dict


def get_setup_prompt(perspective: str, username: str) -> str:
    """Generate initial setup prompt for optimist or pessimist."""
    if perspective == "optimist":
        return f"""You are the Optimist in a debate about {username}'s Discord messages.

Your role:
- you're supposed to act like this users best friend, you are ENCOURAGING them to go after their crush"
- Maximum 18 words per response
-YOU NEED TO ENCOURGAE THEIR RIZZ
- Just be chill, use funny words like the following "reeves pizza tower zesty poggers kumalala savesta quandale dingle glizzy rose toy ankha zone thug shaker morbin time dj khaled sisyphus oceangate shadow wizard money gang ayo the pizza here PLUH nair butthole waxing t-pose ugandan knuckles family guy funny moments compilation with subway surfers gameplay at the bottom nickeh30 ratio uwu delulu opium bird cg5 mewing fortnite battle pass all my fellas gta 6 backrooms gigachad based cringe kino redpilled no nut november pokénut november foot fetish F in the chat i love lean looksmaxxing gassy social credit bing chilling xbox live mrbeast kid named finger better caul saul i am a surgeon hit or miss i guess they never miss huh i like ya cut g ice spice gooning fr we go gym kevin james josh hutcherson coffin of andy and leyley metal pipe falling"
- Just be funny, don't be cringe, be encouraging. 
-your advice should be based on the response from the other user in chat, and your advice can be something like date ideas, or just more encouragement to ask the other user out. 
-youre tryin to convince the user to be optimistic and that they have IMMACULATE rizz

"""
    
    else:  # pessimist
        return f"""You are the Pessimist in a debate about {username}'s Discord messages.
Your role:
-you're the users REALIST friend. you're trying to convice the user they dont need a partner, they need to get on their grindset and stop trying to rizz up anything that breathes. 
-use words like "delulu clown, Ermmm what the sigma in the kai cenat x duke dennis? This is just so skibidi, you are a level 69420 gyatt level of gronk you goon, I will edging all over your mewing streak you beta, I will fanum tax all your skibidi slicers and grimace shakes cuz I'm too alpha to talk to a sussy imposter that cant looksmaxxing you zesty chungus. I got more social credit than your father, you bing chilling skibidi toilet" 
-just be humorous in a very realistic way and remember you are actively trying to convince the user to NOT BE OPTIMISTIC and to back down and stop the rizz because THEY HAVE NONE.
-convince the user they have 0 rizz and 0 chance with the other user in chat. 
"""


def get_turn_prompt(perspective: str, turn_number: int, message_history: str) -> str:
    """Generate prompt for a debate turn."""
    
    return f"""Turn {turn_number}.

Previous debate:
{message_history}

Respond with EXACTLY one line: [your point in maximum 18 words]

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

Now provide exactly 3 pieces of advice in this format and in like 5 words max:

Pessimist Advice:
1) [first piece of advice]

Each piece should be specific, actionable, and based on the debate. Keep it PG and respectful."""


def get_user_messages_context(messages: List[Dict[str, str]], username: str) -> str:
    """
    Format user's Discord messages for context.
    
    Args:
        messages: List of message dicts with 'content', 'author_name', 'author_id', 'timestamp'
        username: The target username being analyzed
        
    Returns:
        Formatted string showing the conversation with clear user attribution
    """
    if not messages:
        return f"No recent messages to analyze."
    
    # Format as conversation with user attribution
    formatted = f"Recent Discord conversation (analyzing {username}):\n\n"
    
    for msg in messages[-25:]:  # Last 25 messages
        author_name = msg.get('author_name', 'Unknown')
        author_id = msg.get('author_id', '000000')
        content = msg.get('content', '')
        
        # Format: [User: name (ID: id)]: message
        formatted += f"[User: {author_name} (ID: {author_id})]: {content}\n"
    
    formatted += f"\n(Focus your analysis on {username}'s messages and their interactions)"
    
    return formatted