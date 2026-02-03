import os
import asyncio
import re
import smtplib
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
TARGET_GROUP = "FragranceDealsSA" # <--- CHECK THIS NAME!

# --- PARSING LOGIC ---
def parse_message(text):
    if not text: return None
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

# --- EMAIL LOGIC ---
def send_email(file_path, highlights):
    msg = EmailMessage()
    msg['Subject'] = f"👃 Daily Fragrance Report - {len(highlights)} Items Found"
    msg['From'] = EMAIL_ADDR
    msg['To'] = EMAIL_ADDR # Sending to yourself
    
    # Create the Body Text
    body = "Here are the top 5 latest fragrance listings from the group:\n\n"
    for i, item in enumerate(highlights[:5], 1):
        body += f"{i}. {item['Fragrance']} - {item['Price']} SAR\n"
    
    body += "\nSee the attached Excel file for photos and full details."
    msg.set_content(body)

    # Attach Excel
    with open(file_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='xlsx', filename='fragrance_report.xlsx')

    # Send
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDR, EMAIL_PASS)
        smtp.send_message(msg)
    print("📧 Email sent successfully!")

# --- MAIN SCRIPT ---
async def main():
    print("--- Connecting to Telegram ---")
    async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
        
        valid_posts = []
        
        print(f"Scanning {TARGET_GROUP}...")
        # Scan last 3000 messages
        async for message in client.iter_messages(TARGET_GROUP, limit=3000):
            if message.text:
                parsed = parse_message(message.text)
                if parsed:
                    # Download Photo if available
                    image_path = None
                    if message.photo:
                        # Save to a folder named 'images'
                        path = await message.download_media(file=f"images/{message.id}")
                        image_path = path
                    
                    parsed['Image_Path'] = image_path
                    parsed['Date'] = message.date.strftime("%Y-%m-%d")
                    valid_posts.append(parsed)

        if not valid_posts:
            print("❌ No valid posts found.")
            return

        print(f"✅ Found {len(valid_posts)} items. Creating Excel...")

        # --- CREATE EXCEL WITH IMAGES ---
        df = pd.DataFrame(valid_posts)
        # Reorder columns to put Image first
        cols = ['Image_Path', 'Date', 'Fragrance', 'Price', 'Full_Text']
        df = df[cols]

        writer = pd.ExcelWriter('fragrance_report.xlsx', engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Deals', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Deals']

        # Formatting
        worksheet.set_column('A:A', 20) # Width for Image column
        worksheet.set_column('B:E', 25) # Width for text columns
        
        # Loop through rows to insert images
        for index, row in df.iterrows():
            row_num = index + 1 # +1 because header is row 0
            img_path = row['Image_Path']
            
            if img_path and os.path.exists(img_path):
                # Set row height to fit image
                worksheet.set_row(row_num, 100)
                # Insert image into Column A (Scale down to fit)
                worksheet.insert_image(row_num, 0, img_path, {'x_scale': 0.1, 'y_scale': 0.1, 'object_position': 1})
            else:
                worksheet.write(row_num, 0, "No Image")

        writer.close()
        
        # --- SEND EMAIL ---
        print("Sending Email...")
        send_email('fragrance_report.xlsx', valid_posts)

if __name__ == "__main__":
    asyncio.run(main())
