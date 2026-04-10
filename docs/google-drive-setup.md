# Google Drive Setup Guide

Bandit can connect to your Google Drive to automatically discover and read vendor documents — DPAs, MSAs, SOC 2 reports, BAAs, and more.

Once connected, run `bandit assess "Salesforce" --drive` and Bandit finds, downloads, and analyses every document in that vendor's Drive folder automatically. Assessment results are saved back to Drive alongside the source documents.

---

## Setup sequence

If you are setting up Drive for the first time with existing vendor folders:

```bash
# 1. Configure Drive credentials
bandit setup --drive

# 2. Discover, link, and sync everything
#    Scans your Bandit root folder, links subfolders that match
#    vendor profiles, detects deleted folders, pulls documents.
bandit sync

# 3. Verify everything is connected
bandit dashboard
```

If a Drive folder has no local profile yet:

```bash
bandit vendor add "VendorName"
```

Bandit will find and link the existing folder automatically during intake.

---

## Ongoing sync

`bandit sync` runs automatically at the start and end of every `bandit assess --drive` run.

To manually sync without running an assessment:

```bash
bandit sync              # all vendors
bandit sync "Cyera"      # one vendor
bandit sync --verbose    # show document names
```

To pick up new Drive folders added since last sync, just run `bandit sync` again — discovery runs automatically every time.

---

## Before you start

You will need:
- A Google account with access to Google Drive
- About 10 minutes for the one-time setup
- Your vendor documents already in Google Drive (or ready to upload)

---

## Step 1 — Organise your Drive folder

Create this folder structure in Google Drive:

```
Bandit/                     ← create this root folder
├── Salesforce/             ← one subfolder per vendor
│   ├── dpa.pdf
│   ├── msa.pdf
│   └── soc2-2025.pdf
├── HubSpot/
│   └── dpa.pdf
└── NetSuite/
    └── soc1-2025.pdf
```

Rules:
- The root folder can be named anything you want
- Each vendor subfolder must match the vendor name you use in Bandit (case-insensitive)
- File names don't matter — Bandit auto-detects what each document is
- Subfolders can contain any mix of document types

---

## Step 2 — Create a Google Cloud project

Bandit needs read and write access to your Drive — it reads vendor documents and saves HTML assessment reports back to vendor folders. This requires a free Google Cloud project.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click "Select a project" at the top
3. Click "New Project"
4. Name it "Bandit" (or anything you like)
5. Click "Create"

---

## Step 3 — Enable the Google Drive API

1. In your new project, go to: **APIs & Services → Library**
2. Search for "Google Drive API"
3. Click on it and click **Enable**

---

## Step 4 — Create OAuth credentials

1. Go to: **APIs & Services → Credentials**
2. Click **"Create Credentials" → "OAuth client ID"**
3. If prompted, configure the consent screen first:
   - User Type: **External**
   - App name: Bandit
   - User support email: your email
   - Developer contact: your email
   - Save and continue through all steps
   - No scopes to add here — Bandit requests the Drive scope automatically during authentication
   - Add your email as a test user
4. Back on Create Credentials → OAuth client ID:
   - Application type: **Desktop app**
   - Name: Bandit
   - Click **"Create"**
5. Click **"Download JSON"**
6. Save the file somewhere you can find it
   (e.g. `~/Downloads/bandit-credentials.json`)

---

## Step 5 — Get your Drive folder ID

1. Open Google Drive in your browser
2. Navigate to your Bandit root folder (the one containing vendor subfolders)
3. Copy either the **full URL** from your browser address bar or just the **folder ID** at the end — both work:
   ```
   Full URL:  https://drive.google.com/drive/u/0/folders/1YOYAT1DxmLjFRfoN3irpm3xGbafVZv7_
   Bare ID:   1YOYAT1DxmLjFRfoN3irpm3xGbafVZv7_
   ```
   Bandit will extract the ID automatically if you paste the full URL.

---

## Step 6 — Run bandit setup --drive

```bash
bandit setup --drive
```

Bandit will ask for:

1. **Path to your credentials JSON file**
   → paste the path e.g. `~/Downloads/bandit-credentials.json`

2. **Your browser will open automatically**
   → log in with your Google account
   → click Allow to grant Bandit read and write access to Google Drive
   → browser tab will confirm success

3. **Your Bandit root folder ID**
   → paste the folder ID or full URL you copied in Step 5

4. Bandit scans the folder and confirms:
   ```
   ✓ Connected to Google Drive
   ✓ Found 12 vendor subfolders
   ✓ Configuration saved
   ```

Setup saves your progress after each step. If you quit or lose connection mid-wizard, re-running `bandit setup --drive` resumes from where you left off. If all steps are already complete, you'll be asked "Drive already configured. Reconfigure? [y/N]".

---

## Step 7 — Run your first Drive assessment

```bash
bandit assess "Salesforce" --drive
```

Bandit will:
1. Find the Salesforce subfolder in your Drive
2. Download documents to a secure temp directory
3. Auto-detect each document type
4. Run the full assessment pipeline
5. Clean up the temp files
6. Save the HTML report back to the Salesforce folder in Drive

---

## Usage

Single vendor assessment:

```bash
bandit assess "Salesforce" --drive
bandit assess "Salesforce" --drive --verbose
```

Batch assessment — all vendors with Drive folders:

```bash
bandit batch vendors.txt --drive
```

To disable saving reports to Drive, set in `bandit.config.yml`:

```yaml
integrations:
  google_drive:
    auto_save_reports: false
```

---

## Configuration

Drive settings are stored in `bandit.config.yml`:

```yaml
integrations:
  google_drive:
    enabled: true
    root_folder_id: "1ABC123xyz..."
    credentials_path: "~/.bandit/google-credentials.json"
    auto_save_reports: true
```

Edit this file directly to change settings.
Or re-run `bandit setup --drive` to reconfigure.

---

## Troubleshooting

**"Google credentials not found"**
Run `bandit setup --drive` to complete setup.
Make sure you pointed to the right credentials.json path.

**"Vendor folder not found in Drive"**
Check the subfolder name matches the vendor name you're using in Bandit. Matching is case-insensitive but spelling must match exactly.
Example: folder named "Salesforce" matches `bandit assess "Salesforce"` or `bandit assess "salesforce"`

**"Token expired" or authentication errors**
Delete the token and re-authenticate:
```bash
rm ~/.bandit/google-token.json
bandit assess "YourVendor" --drive
```
Your browser will open for a fresh login. Running `bandit setup --drive` alone does not always fix this if the token is present but has the wrong permissions.

**"403 Insufficient Permission" on Drive save**
Your token was created with read-only scope before Bandit added report saving. Delete the token and re-authenticate:
```bash
rm ~/.bandit/google-token.json
bandit assess "YourVendor" --drive
```
On the Google consent screen, accept "See, edit, create and delete all your Google Drive files". Bandit now detects this automatically on startup, but if you see this error the token needs replacing.

**Drive documents not improving scores**
Check the manifest output when running with `--verbose`.
Make sure documents show as "Ready" not "Failed".
Scanned PDFs (no text layer) cannot be read — use text-based PDFs instead.

**"Access denied" on Drive folder**
Make sure the Google account you authenticated with has access to the Drive folder you configured.

---

## Vendor profile sync (v1.3)

In addition to reading documents and saving reports, Bandit syncs your vendor profile database to Drive. This lets your whole team share a single source of truth for vendor intake data and assessment history.

### How folder matching works

When you run `bandit vendor add "HubSpot"`, Bandit checks Drive before starting the wizard:

- **Exact match** — a folder named "HubSpot" (case-insensitive) already exists → linked silently, no prompt
- **Close match** — a folder named "Hub Spot" or "hubspot" is found → Bandit asks: *"Found 'Hub Spot' — use this folder? [Y/n]"*
- **No match** — no folder found → Bandit offers to create one at the end of the wizard

You can also skip Drive linking entirely and manage the folder manually later.

### Where profiles are stored

Vendor profiles are stored in two places:

| Location | Purpose |
|----------|---------|
| `~/.bandit/vendor-profiles.json` | Local cache — always used as primary |
| `.vendor-profiles.json` in Drive root | Shared copy — synced to/from Drive |

The file is stored in your **Bandit root folder** in Drive (the same folder you configured in `bandit setup --drive`), not inside individual vendor subfolders.

### When sync happens

Bandit syncs the profile database at the following points:

- After `bandit vendor add` completes
- After `bandit vendor edit` completes
- At the start of `bandit assess --drive` (pulls latest from Drive before assessing)
- At the end of `bandit assess --drive` (pushes updated history after assessing)

### Sync is non-blocking

If Drive is unavailable or the sync fails for any reason, Bandit continues normally using the local cache. Sync failures are logged but never interrupt an assessment or wizard.

The local cache is always the write target first. Drive sync is best-effort.

### Team sharing

All team members with access to the Bandit Drive root folder share the same `.vendor-profiles.json`. The sync model is last-write-wins — simultaneous writes from two machines could overwrite each other. In practice this is rare because assessments take several minutes.

For teams running frequent concurrent assessments, treat the Drive copy as a periodic backup and reconcile locally if needed.

---

## Security and privacy

- Bandit requests **read and write** access to Drive — needed to save HTML reports back to vendor folders after each assessment
- Your credentials never leave your machine
- Documents are downloaded to a temporary directory that is deleted after each assessment
- Reports are saved back to the matching vendor subfolder in Drive after each assessment. Disable with `auto_save_reports: false` in `bandit.config.yml`
- Your API key and Drive token are stored in `~/.bandit/` on your local machine only
