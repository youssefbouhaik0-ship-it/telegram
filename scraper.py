import os
import asyncio
import pandas as pd
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = os.environ["TG_API_ID"]
API_HASH = os.environ["TG_API_HASH"]
SESSION_STRING = os.environ["TG_SESSION_STRING"]
TARGET_GROUP = "alm_alator"

# --- PARSING LOGIC ---
def parse_message(text):
    if not text: return None
    
    # 1. Check if the message follows the Group Rules (must have "Name" and "Price")
    # We look for "اسم العطر" AND "السعر" to be safe.
    if "اسم العطر" not in text or "السعر" not in text:
        return None

    try:
        data = {}
        
        # 2. Extract the Name (Everything after "اسم العطر :")
        # Matches: "اسم العطر : Dior Sauvage" or "اسم العطر:Dior"
        name_match = re.search(r"اسم العطر\s*[:\-.]\s*(.*)", text)
        if name_match:
            data['Fragrance'] = name_match.group(1).strip()
        else:
            data['Fragrance'] = "Unknown"

        # 3. Extract the Price (Everything after "السعر :")
        # Then we strip it down to just the number
        price_line_match = re.search(r"السعر\s*[:\-.]\s*(.*)", text)
        if price_line_match:
            raw_price = price_line_match.group(1).strip()
            # Find the first number in that line (e.g., from "350 riyal" -> "350")
            number_match = re.search(r"(\d+)", raw_price)
            data['Price'] = number_match.group(1) if number_match else raw_price
        else:
            data['Price'] = "0"
            
        data['Full_Text'] = text # Save original text just in case
        return data

    except Exception as e:
        print(f"Error parsing message: {e}")
        return None

# --- MAIN SCRIPT ---
async def main():
    print("--- Connecting to Telegram ---")
    async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
        data = []
        print(f"Scanning {TARGET_GROUP} for Template Messages...")
        
        # Scans the last 3000 messages
        async for message in client.iter_messages(TARGET_GROUP, limit=3000):
            if message.text:
                parsed = parse_message(message.text)
                if parsed:
                    # Add Date
                    parsed['Date'] = message.date.strftime("%Y-%m-%d")
                    data.append(parsed)
        
        # Save results
        if data:
            df = pd.DataFrame(data)
            df.to_excel("fragrance_prices.xlsx", index=False)
            print(f"✅ Success! Found {len(data)} valid sales posts.")
        else:
            print("❌ No messages matched the template rules.")
            print("Double check the TARGET_GROUP name or Invite Link!")

if __name__ == "__main__":
    asyncio.run(main())
