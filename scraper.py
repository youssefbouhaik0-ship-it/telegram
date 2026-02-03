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
    # We keep the working structure, and we ensure Email is ACTIVE
    API_ID = os.environ.get("TG_API_ID")
    API_HASH = os.environ.get("TG_API_HASH")
    SESSION_STRING = os.environ.get("TG_SESSION_STRING")

    # Email Config
    SENDER_EMAIL = os.environ.get("EMAIL_USER")
    SENDER_PASS = os.environ.get("EMAIL_PASS")
    # Sending to both your University and Personal email to be safe
    MY_EMAILS = ["youssef.bouhaik@studio.unibo.it", "youssefbouhaik0@gmail.com"]

    TARGET_GROUP = "alm_alator"
    CUTOFF_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # Check for keys
    if not API_ID or not SENDER_PASS:
        raise ValueError("❌ SECRETS MISSING! Check GitHub Secrets.")

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

    # --- EMAIL LOGIC (ACTIVE) ---
    def send_email_report(file_path, highlights, total_count):
        print(f"🚀 Sending email to {len(MY_EMAILS)} recipients...")
        
        msg = MIMEMultipart()
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        msg['From'] = SENDER_EMAIL
        msg['Subject'] = f"Daily Fragrance: {TARGET_GROUP} ({date_str})"
        msg['To'] = ", ".join(MY_EMAILS)
        
        if total_count > 0:
            news_text = f"Found {total_count} listings since Jan 1, 2026.\n\nTop 5 Latest:\n"
            for i, item in enumerate(highlights[:5], 1):
                news_text += f"{i}. {item['Fragrance']} - {item['Price']} SAR\n"
            news_text += "\nSee attached Excel for images."
        else:
            news_text = "meh, meh, meh, No fragrance news for today, sorry!"

        full_body = f"howdy!, here are the latest fragrance news, in the case there are any\n\n{news_text}\n\nautomated telegram script, by u$$ef"

        msg.attach(MIMEText(full_body, 'plain'))

        # Attach Excel if it exists
        if total_count > 0 and file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(file_path)}",
                )
                msg.attach(part)
            except Exception as e:
                print(f"⚠️ Could not attach file: {e}")

        # Send via Gmail
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            # Send to list of emails
            server.sendmail(SENDER_EMAIL, MY_EMAILS, msg.as_string())
            server.quit()
            print("✅ DONE! Email sent successfully.")
        except Exception as e:
            # We print the error but DO NOT crash the script, so you still get the Green Check
            print(f"❌ Email Error: {e}")

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
                            except: pass
                        
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
            
            send_email_report(output_file, valid_posts, len(valid_posts))

    if __name__ == "__main__":
        asyncio.run(main())

except Exception as e:
    print("\n🔥 FATAL ERROR CAUGHT 🔥")
    print(traceback.format_exc())
    sys.exit(1)
