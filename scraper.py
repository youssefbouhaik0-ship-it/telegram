import os
import asyncio
import re
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = os.environ["TG_API_ID"]
API_HASH = os.environ["TG_API_HASH"]
SESSION_STRING = os.environ["TG_SESSION_STRING"]
EMAIL_ADDR = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
TARGET_GROUP = "alm_alator"

# Date Cutoff: January 1, 2026
CUTOFF_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)

# --- PARSING LOGIC ---
def parse_message(text):
    if not text: return None
    # Filter: Must follow the group template
    if "اسم العطر" not in text or "السعر" not in text:
        return None

    try:
        data = {}
        # Extract Name
        name_match = re.search(r"اسم العطر\s*[:\-.]\s*(.*)", text)
        data['Fragrance'] = name_match.group(1).strip() if name_match else "Unknown"
        
        # Extract Price (Digits only)
        price_match = re.search(r"السعر.*[:\-.]\s*(\d+)", text)
        data['Price'] = int(price_match.group(1)) if price_match else 0
        
        data['Full_Text'] = text
        return data
    except:
        return None

# --- EMAIL LOGIC (OFFICE 365 / UNIBO) ---
def send_email(file_path, highlights, total_count):
    msg = EmailMessage()
    msg['Subject'] = f"👃 Historic Fragrance Report (Jan 2026) - {total_count} Items"
    msg['From'] = EMAIL_ADDR
    msg['To'] = EMAIL_ADDR # Sends to your Unibo email
    
    body = f"Here is the fragrance history from Jan 1, 2026 to today.\n\n"
    body += f"Total Listings Found: {total_count}\n\n"
    body += "Top 5 Latest Listings:\n"
    for i, item in enumerate(highlights[:5], 1):
        body += f"{i}. {item['Fragrance']} - {item['Price']} SAR\n"
    
    body += "\nSee attached Excel file for images."
    msg.set_content(body)

    # Attach Excel
    with open(file_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='xlsx', filename='fragrance_history.xlsx')

    print("🔌 Connecting to Office 365 Server...")
    try:
        # UPDATED: Using Office 365 Server Settings
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls() # Secure the connection
            smtp.login(EMAIL_ADDR, EMAIL_PASS)
            smtp.send_message(msg)
        print("✅ Email sent successfully to " + EMAIL_ADDR)
    except Exception as e:
        print(f"❌ Email Failed: {e}")

# --- MAIN SCRIPT ---
async def main():
    print("--- Connecting to Telegram ---")
    async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
        
        valid_posts = []
        print(f"⏳ Scanning backwards until {CUTOFF_DATE.date()}...")
        
        # Scan messages backwards
        async for message in client.iter_messages(TARGET_GROUP):
            
            # Stop if we reach 2025
            if message.date < CUTOFF_DATE:
                print("🛑 Reached Jan 1, 2026. Stopping.")
                break

            if message.text:
                parsed = parse_message(message.text)
                if parsed:
                    # Download Photo
                    image_path = None
                    if message.photo:
                        path = await message.download_media(file=f"images/{message.id}")
                        image_path = path
                    
                    parsed['Image_Path'] = image_path
                    parsed['Date'] = message.date.strftime("%Y-%m-%d")
                    valid_posts.append(parsed)

        if not valid_posts:
            print("❌ No posts found.")
            return

        print(f"✅ Found {len(valid_posts)} items. Creating Excel...")

        # Create Excel
        df = pd.DataFrame(valid_posts)
        cols = ['Image_Path', 'Date', 'Fragrance', 'Price', 'Full_Text']
        df = df[cols]

        output_file = 'fragrance_history.xlsx'
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='History', index=False)
        
        worksheet = writer.sheets['History']
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:E', 25)
        
        for index, row in df.iterrows():
            row_num = index + 1
            img_path = row['Image_Path']
            worksheet.set_row(row_num, 100)
            if img_path and os.path.exists(img_path):
                worksheet.insert_image(row_num, 0, img_path, {'x_scale': 0.1, 'y_scale': 0.1, 'object_position': 1})
            else:
                worksheet.write(row_num, 0, "No Image")

        writer.close()
        
        # Send Email
        send_email(output_file, valid_posts, len(valid_posts))

if __name__ == "__main__":
    asyncio.run(main())
