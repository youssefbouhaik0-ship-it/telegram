import os
import sys
import asyncio
import re
import traceback
from datetime import datetime, timezone
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("TG_SESSION_STRING")

TARGET_GROUP = "alm_alator"
# Scan from NOW back to Jan 1, 2026
CUTOFF_DATE = datetime(2026, 1, 25, tzinfo=timezone.utc)

# Crash prevention
if not API_ID:
    print("❌ ERROR: API_ID is missing. Check GitHub Secrets.")
    sys.exit(1)

os.makedirs("images", exist_ok=True)

# --- PARSING LOGIC ---
def parse_message(text):
    if not text: return None
    # Must have "Name" and "Price" in Arabic
    if "اسم العطر" not in text or "السعر" not in text:
        return None
    try:
        data = {}
        # Extract Name
        name_match = re.search(r"اسم العطر\s*[:\-.]\s*(.*)", text)
        data['Fragrance'] = name_match.group(1).strip() if name_match else "Unknown"
        
        # Extract Price
        price_match = re.search(r"السعر.*[:\-.]\s*(\d+)", text)
        data['Price'] = int(price_match.group(1)) if price_match else 0
        
        data['Full_Text'] = text
        return data
    except:
        return None

# --- MAIN SCRIPT ---
async def main():
    print("--- 🟢 STARTING SCRAPE (NO EMAIL) ---")
    async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
        
        valid_posts = []
        print(f"⏳ Scanning backwards until {CUTOFF_DATE.date()}...")
        
        async for message in client.iter_messages(TARGET_GROUP):
            # Stop if older than Jan 1, 2026
            if message.date < CUTOFF_DATE:
                print("🛑 Reached Jan 1, 2026. Stopping.")
                break

            if message.text:
                parsed = parse_message(message.text)
                if parsed:
                    image_path = None
                    if message.photo:
                        try:
                            # Save image to folder
                            path = await message.download_media(file="images/")
                            image_path = path
                        except: pass 
                    
                    parsed['Image_Path'] = image_path
                    parsed['Date'] = message.date.strftime("%Y-%m-%d")
                    valid_posts.append(parsed)

        if valid_posts:
            print(f"✅ Found {len(valid_posts)} items. Creating Excel...")
            output_file = 'fragrance_history.xlsx'
            
            df = pd.DataFrame(valid_posts)
            # Reorder columns
            cols = ['Image_Path', 'Date', 'Fragrance', 'Price', 'Full_Text']
            df = df[cols]

            # Create Excel with Images
            writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='History', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['History']
            worksheet.set_column('A:A', 20) # Image col width
            worksheet.set_column('B:E', 25) # Text col width
            
            for index, row in df.iterrows():
                row_num = index + 1
                img_path = row['Image_Path']
                worksheet.set_row(row_num, 100) # Row height
                
                if img_path and os.path.exists(img_path):
                    try:
                        worksheet.insert_image(row_num, 0, img_path, {'x_scale': 0.1, 'y_scale': 0.1, 'object_position': 1})
                    except: pass
                else:
                    worksheet.write(row_num, 0, "No Image")

            writer.close()
            print(f"🎉 SUCCESS! Saved to {output_file}. Go to Artifacts to download.")
        else:
            print("❌ No items found.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)
