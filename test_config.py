#!/usr/bin/env python3
"""
Test script for Backboard Responses API and Discord bot configuration.
Run: python test_config.py
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()


async def test_backboard():
    """Test Backboard Responses API connection."""
    print("\n=== Testing Backboard Responses API ===\n")
    
    api_key = os.getenv('BACKBOARD_API_KEY')
    base_url = os.getenv('BACKBOARD_BASE_URL', 'https://api.backboard.io')
    model = os.getenv('BACKBOARD_MODEL', 'gpt-4o-mini')
    
    if not api_key:
        print("❌ BACKBOARD_API_KEY not set in .env")
        return False
    
    print(f"Using Backboard URL: {base_url}")
    print(f"Using model: {model}")
    
    try:
        import aiohttp
        
        # Test: Send a simple request
        print("\nTest: Sending a test request...")
        
        url = f"{base_url}/responses"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'test successful' if you can read this."}
            ],
            "max_tokens": 50
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ API request failed with status {response.status}")
                    print(f"Error: {error_text}")
                    return False
                
                data = await response.json()
                assistant_message = data['choices'][0]['message']['content']
                
                print(f"✅ Response received: {assistant_message}")
                print(f"✅ Backboard Responses API is working correctly")
                
        return True
        
    except ImportError:
        print("❌ aiohttp package not installed. Run: pip install aiohttp")
        return False
    except asyncio.TimeoutError:
        print("❌ Request timed out. Check your network connection.")
        return False
    except Exception as e:
        print(f"❌ Backboard API test failed: {e}")
        return False


async def test_discord_optimist():
    """Test Optimist Discord bot token."""
    print("\n=== Testing Optimist Bot Token ===\n")
    
    token = os.getenv('OPTIMIST_TOKEN')
    
    if not token:
        print("❌ OPTIMIST_TOKEN not set in .env")
        return False
    
    try:
        import discord
        
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        ready_event = asyncio.Event()
        
        @client.event
        async def on_ready():
            print(f"✅ Optimist bot: {client.user.name} (ID: {client.user.id})")
            ready_event.set()
            await client.close()
        
        # Start bot with timeout
        bot_task = asyncio.create_task(client.start(token))
        
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            print("❌ Bot connection timed out")
            bot_task.cancel()
            return False
        
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        
        return True
        
    except ImportError:
        print("❌ discord.py not installed. Run: pip install discord.py")
        return False
    except discord.LoginFailure:
        print("❌ Invalid bot token")
        return False
    except Exception as e:
        print(f"❌ Optimist bot token test failed: {e}")
        return False


async def test_discord_pessimist():
    """Test Pessimist Discord bot token."""
    print("\n=== Testing Pessimist Bot Token ===\n")
    
    token = os.getenv('PESSIMIST_TOKEN')
    
    if not token:
        print("❌ PESSIMIST_TOKEN not set in .env")
        return False
    
    try:
        import discord
        
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        ready_event = asyncio.Event()
        
        @client.event
        async def on_ready():
            print(f"✅ Pessimist bot: {client.user.name} (ID: {client.user.id})")
            ready_event.set()
            await client.close()
        
        # Start bot with timeout
        bot_task = asyncio.create_task(client.start(token))
        
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            print("❌ Bot connection timed out")
            bot_task.cancel()
            return False
        
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        
        return True
        
    except ImportError:
        print("❌ discord.py not installed. Run: pip install discord.py")
        return False
    except discord.LoginFailure:
        print("❌ Invalid bot token")
        return False
    except Exception as e:
        print(f"❌ Pessimist bot token test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Configuration Test Script")
    print("=" * 60)
    
    # Check .env exists
    if not os.path.exists('.env'):
        print("\n❌ .env file not found. Copy .env.example to .env and configure it.")
        return
    
    results = []
    
    # Test Backboard
    backboard_ok = await test_backboard()
    results.append(("Backboard Responses API", backboard_ok))
    
    # Test Discord bots
    optimist_ok = await test_discord_optimist()
    results.append(("Optimist Bot", optimist_ok))
    
    pessimist_ok = await test_discord_pessimist()
    results.append(("Pessimist Bot", pessimist_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
    
    all_ok = all(ok for _, ok in results)
    
    if all_ok:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Make sure both Discord bots are invited to your server")
        print("2. Run: python src/main.py")
        print("3. Use /setup command in Discord to configure channels")
        print("4. Use /analyze command to start debate analysis")
    else:
        print("\n⚠️  Some tests failed. Please fix the configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())
