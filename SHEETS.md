# Google Sheets Setup Guide
# ════════════════════════════════════════════════════════

Follow these steps to connect the doorbell to Google Sheets.

## Step 1 — Create a Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click "New Project" → name it "Doorbell"
3. Click "Create"

## Step 2 — Enable APIs

1. Go to APIs & Services → Library
2. Search and enable:
   - "Google Sheets API"
   - "Google Drive API"

## Step 3 — Create a Service Account

1. Go to APIs & Services → Credentials
2. Click "Create Credentials" → "Service Account"
3. Name it "doorbell-bot" → click Done
4. Click on the service account → Keys tab
5. Add Key → Create new key → JSON
6. Download the JSON file
7. RENAME it to: credentials.json
8. PLACE it in your doorbell/ project folder

## Step 4 — Create the Google Sheet

1. Go to https://sheets.google.com
2. Create a new sheet
3. Name it exactly: Doorbell Log
4. Copy the service account email from credentials.json
   (it looks like: doorbell-bot@doorbell-xxxxx.iam.gserviceaccount.com)
5. Share the sheet with that email (Editor access)

## Step 5 — Install dependencies & run

pip install -r requirements.txt
python main.py

## Sheet columns (auto-created):
| Timestamp           | Person  | Type    | Status         |
|---------------------|---------|---------|----------------|
| 2026-04-06 10:23:01 | John    | Known   | Access Granted |
| 2026-04-06 10:25:14 | Unknown | Unknown | Access Denied  |

## Notes:
- If credentials.json is missing, the system still works
  but skips Google Sheets logging (no crash).
- The sheet is created/cleared on first run if empty.