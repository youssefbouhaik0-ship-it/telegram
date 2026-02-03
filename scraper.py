import os
import asyncio
import pandas as pd
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

# 1. Configuration
API_ID = os.environ["TG_API_ID"]
API_HASH = os.environ["TG_API_HASH"]
SESSION_STRING = os.environ["TG_SESSION_STRING"]
TARGET_GROUP = "FragranceDealsSA" # <--- REPLACE THIS with the real group username

# 2. Parsing Function
def parse_message(text):
    if not text: return None
    # Matches numbers next to Riyal/SAR
    pattern = r"(\d+)\s?(ريال|ر\.س|SAR|﷼)"
    match = re.search(pattern, text)
    if match:
        return {
            "date": None, 
            "name": text.split('\n')[0][:60].strip(), 
            "price": match.group(1),
            "currency": match.group(2)
        }
    return None

# 3. Main Logic
async def main():
    print("--- Connecting to Telegram ---")
    async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
        data = []
        print(f"Scanning {TARGET_GROUP}...")

        # Scan last 3000 messages
        async for message in client.iter_messages(TARGET_GROUP, limit=3000):
            if message.text:
                parsed = parse_message(message.text)
                if parsed:
                    parsed['date'] = message.date.strftime("%Y-%m-%d")
                    data.append(parsed)

        if data:
            df = pd.DataFrame(data)
            df.to_excel("fragrance_prices.xlsx", index=False)
            print(f"Success! Saved {len(data)} items.")
        else:
            print("No prices found.")

if __name__ == "__main__":
    asyncio.run(main())
