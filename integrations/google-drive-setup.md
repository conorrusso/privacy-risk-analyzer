# Google Drive Integration Setup

**Bandit — Integration Guide**

The Google Drive integration saves risk assessment reports as structured Google Docs and maintains a vendor register spreadsheet.

---

## Prerequisites

- A Google account with Google Drive access
- Google Cloud project with Drive API enabled

---

## Step 1: Create a Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Search for and enable:
   - **Google Drive API**
   - **Google Docs API**
   - **Google Sheets API**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → Service Account**
7. Give it a name (e.g., `privacy-lens-n8n`)
8. Grant role: **Editor**
9. Click the created service account → **Keys → Add Key → JSON**
10. Download the JSON key file — keep this secure

---

## Step 2: Configure n8n Credential

1. In n8n: **Settings → Credentials → New → Google Service Account**
2. Paste the contents of your JSON key file
3. Name the credential `Google Drive - Bandit`

---

## Step 3: Set Up Drive Folder Structure

Create the following folder structure in Google Drive:

```
Bandit/
├── Vendor Assessments/
│   ├── [auto-populated by workflow]
├── Vendor Register (Sheet)/
│   └── vendor-register.gsheet
└── Templates/
    └── [optional: assessment template]
```

Share each folder with your service account email (found in the JSON key as `client_email`).

---

## Step 4: Configure Workflow Nodes

In each workflow's **Save to Google Drive** node:

| Parameter | Value |
|-----------|-------|
| Operation | `Create` |
| Drive | `My Drive` |
| Folder | ID of `Vendor Assessments/` folder |
| File Name | `{{vendor_name}}_{{assessment_date}}_PRS-{{score}}.json` |
| File Content | Output from Parse JSON node |

For the vendor register (Sheets), use the **Google Sheets** node:
| Parameter | Value |
|-----------|-------|
| Operation | `Append Row` |
| Spreadsheet ID | ID of `vendor-register.gsheet` |
| Sheet Name | `Assessments` |

---

## Vendor Register Sheet Schema

The workflow appends one row per assessment. Recommended columns:

| Column | Content |
|--------|---------|
| A | Assessment Date |
| B | Vendor Name |
| C | Privacy Risk Score (PRS) |
| D | Risk Level |
| E | D1 Score |
| F | D2 Score |
| G | D3 Score |
| H | D4 Score |
| I | D5 Score |
| J | D6 Score |
| K | D7 Score |
| L | D8 Score |
| M | DPA Required? |
| N | Legal Review Required? |
| O | Report Link |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `403 Forbidden` | Ensure folder is shared with service account email |
| `File not found` | Check folder ID is correct (get from Drive URL) |
| Sheets append fails | Verify sheet name matches exactly (case-sensitive) |
