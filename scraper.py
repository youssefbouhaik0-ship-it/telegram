import os
import sys
import asyncio
import re
import smtplib
import traceback
from datetime import datetime, timezone
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- CRASH REPORTER START ---
try:
    print("--- 🟢 SCRIPT INITIALIZING ---")

    # --- CONFIGURATION ---
    # HACK KEY: Set this to True later when you want to fix emails
    ENABLE_EMAIL = False 

    API_ID = os.environ.get("TG_API_ID")
    API_HASH = os.environ.get("TG_API_HASH")
    SESSION_STRING = os.environ.get("TG_SESSION_STRING")

    # Email Config (Kept here for future use)
    SENDER_EMAIL = os.environ.get("EMAIL_USER")
    SENDER_PASS = os.environ.get("EMAIL_PASS")
    MY_EMAILS = ["youssefbouhaik0@gmail.com"]

    TARGET_GROUP = "alm_alator"
    CUTOFF_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # Check for keys (We skip checking Email keys if email is disabled)
    if not API_ID:
        raise ValueError("❌ API_ID MISSING! Check .yml file and GitHub Secrets.")

    os.makedirs("images", exist_ok=True)

    # --- PARSING ---
    def parse_message(text):
        if not text: return None
        if "اسم العطر" not in text or "السعر" not in text:
            return None
        try:
            data = {}
            name_match = re.search(r"اسم العطر\s*[:\-.]\s*(.*)", text)
            data['Fragrance'] = name_match.group(1).strip() if name_match else "Unknown"
            
            price_match = re.search(r"السعر.*[:\-.]\s*(\d+)", text)
            data['Price'] = int(price_match.group(1)) if price_match else 0
            
            data['Full_Text'] = text
            return data
        except:
            return None

    # --- EMAIL LOGIC (DISABLED VIA HACK KEY) ---
    def send_email_report(file_path, highlights, total_count):
        # THE HACK KEY CHECK
        if not ENABLE_EMAIL:
            print("🚫 Email sending is DISABLED via Hack Key. Skipping.")
            return

        print(f"🚀 Sending email to {len(MY_EMAILS)} recipients...")
        msg = MIMEMultipart()
        date_str = datetime.now().strftime("%Y-%m-%d")
        msg['From'] = SENDER_EMAIL
        msg['Subject'] = f"Daily Fragrance: {TARGET_GROUP} ({date_str})"
        msg['To'] = ", ".join(MY_EMAILS)
        
        # ... (Rest of email logic remains here for later) ...
        # [Truncated for brevity, but the function exists so the code doesn't break]
        # ... 

    # --- MAIN ---
    async def main():
        print("--- Connecting to Telegram ---")
        async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
            
            valid_posts = []
            print(f"⏳ Scanning backwards until {CUTOFF_DATE.date()}...")
            
            async for message in client.iter_messages(TARGET_GROUP):
                if message.date < CUTOFF_DATE:
                    print("🛑 Reached cutoff date.")
                    break

                if message.text:
                    parsed = parse_message(message.text)
                    if parsed:
                        image_path = None
                        if message.photo:
                            try:
                                path = await message.download_media(file="images/")
                                image_path = path
                            except Exception as e:
                                print(f"⚠️ Image download failed: {e}")
                        
                        parsed['Image_Path'] = image_path
                        parsed['Date'] = message.date.strftime("%Y-%m-%d")
                        valid_posts.append(parsed)

            output_file = None
            if valid_posts:
                print(f"✅ Found {len(valid_posts)} items. Creating Excel...")
                output_file = 'fragrance_history.xlsx'
                
                df = pd.DataFrame(valid_posts)
                cols = ['Image_Path', 'Date', 'Fragrance', 'Price', 'Full_Text']
                df = df[cols]

                writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
                df.to_excel(writer, sheet_name='History', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['History']
                worksheet.set_column('A:A', 20)
                worksheet.set_column('B:E', 25)
                
                for index, row in df.iterrows():
                    row_num = index + 1
                    img_path = row['Image_Path']
                    worksheet.set_row(row_num, 100)
                    if img_path and os.path.exists(img_path):
                        try:
                            worksheet.insert_image(row_num, 0, img_path, {'x_scale': 0.1, 'y_scale': 0.1, 'object_position': 1})
                        except: pass
                    else:
                        worksheet.write(row_num, 0, "No Image")

                writer.close()
            
            # This function is called, but will exit immediately because ENABLE_EMAIL is False
            send_email_report(output_file, valid_posts, len(valid_posts))

    if __name__ == "__main__":
        asyncio.run(main())

# --- CRASH REPORTER END ---
except Exception as e:
    print("\n🔥 FATAL ERROR CAUGHT 🔥")
    print(traceback.format_exc())
    sys.exit(1)
