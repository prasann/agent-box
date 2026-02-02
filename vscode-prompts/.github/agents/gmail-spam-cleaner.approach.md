# Gmail Spam Cleaner Agent - Technical Approach

## Overview
Local agent to classify and tag spam/promotional emails using Gmail API + Ollama LLM, processing ~1000 emails/day.

## Architecture

```
┌─────────────────┐
│  Python Script  │
│   (Main Agent)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌──────────┐
│ Gmail  │  │  Ollama  │
│  API   │  │  Local   │
└────────┘  └──────────┘
```

## Components

### 1. Gmail API Integration
**Library**: `google-api-python-client`

**Setup**:
- Enable Gmail API in Google Cloud Console
- Download OAuth2 credentials (`credentials.json`)
- First run: authenticate via browser → saves `token.json`
- Subsequent runs: automatic auth using saved token

**Operations**:
- Fetch emails from INBOX (batch: 100 at a time)
- Filter by date range: `after:YYYY/MM/DD before:YYYY/MM/DD`
- Extract: subject, sender, snippet (body preview)
- Apply label: `NeedsReview/Spam`
- Mark as read (optional)

**Quota**: 1 billion units/day (5 units per read = 200M emails/day limit)

### 2. Ollama LLM Classifier
**Model**: `llama3.2:3b` or `mistral:7b` (lightweight, fast)

**Prompt Template**:
```
Classify this email as SPAM, PROMOTIONAL, or LEGITIMATE.

Subject: {subject}
From: {sender}
Preview: {snippet}

Respond with only: SPAM | PROMOTIONAL | LEGITIMATE
Reason (one line): {brief explanation}
```

**API Call**: HTTP POST to `http://localhost:11434/api/generate`

**Response Parsing**: Extract classification + reason

### 3. Main Agent Logic

**Workflow**:
1. Load processed email IDs from state file (`processed_emails.json`)
2. Build Gmail search query with date range (if provided)
3. Fetch emails from Gmail API matching criteria
4. Filter out already processed emails
5. For each new email:
   - Extract subject, sender, snippet
   - Send to Ollama for classification
   - If SPAM or PROMOTIONAL:
     - Apply label `NeedsReview/Spam`
     - Log: email ID, classification, reason, date
   - Add email ID to processed list
6. Save updated state file
7. Summary: X emails processed, Y tagged (date range: from - to)

**State File** (`processed_emails.json`):
```json
{
  "last_run": "2026-02-02T10:30:00Z",
  "processed_ids": ["abc123", "def456", ...],
  "stats": {
    "total_processed": 5000,
    "spam_tagged": 120,
    "promo_tagged": 450
  }
}
```

## Implementation Plan

### File Structure
```
gmail-spam-cleaner/
├── pyproject.toml          # Package definition + dependencies
├── README.md               # Setup + usage instructions
├── .env                    # Config overrides (gitignored)
├── .gitignore
├── src/
│   └── gmail_spam_cleaner/
│       ├── __init__.py
│       ├── __main__.py     # Entry point with argparse
│       ├── agent.py        # Main orchestrator
│       ├── gmail_client.py # Gmail API wrapper
│       ├── ollama_client.py # Ollama API wrapper
│       ├── models.py       # Pydantic models
│       └── config.py       # Settings
├── data/                   # Runtime data directory
│   ├── credentials.json    # Gmail OAuth client (gitignored)
│   ├── token.json          # Gmail access token (gitignored)
│   ├── processed_emails.json # State file (gitignored)
│   └── logs/
│       └── agent.log       # Runtime logs
```

### Dependencies
```
# Core
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
requests
pydantic>=2.0
pydantic-settings
python-dotenv
tenacity  # Retry logic
```

### Setup Steps
1. Install Ollama, pull model: `ollama pull llama3.2:3b`
2. Enable Gmail API in Google Cloud Console, download OAuth credentials
3. Save credentials as `data/credentials.json`
4. Install via pipx:
   ```bash
   brew install pipx
   pipx ensurepath
   cd gmail-spam-cleaner
   pipx install .
   ```
5. First run: `gmail-spam-cleaner` → auto-starts browser for OAuth
   - Authenticates with your Google account
   - Saves access token to `data/token.json`
   - Token auto-refreshes (no re-auth needed)
6. Create Gmail label manually: `NeedsReview/Spam`
7. Test: `gmail-spam-cleaner --dry-run`
8. Schedule: Add to cron (run every 6 hours)

### Cron Schedule
```bash
# Process all new emails every 6 hours
0 */6 * * * gmail-spam-cleaner >> ~/.gmail-spam-cleaner/logs/agent.log 2>&1

# Or process specific month (for backlog cleanup)
0 2 * * 0 gmail-spam-cleaner --from-date 2025-01-01 --to-date 2025-01-31 >> ~/.gmail-spam-cleaner/logs/agent.log 2>&1
```

### Monthly Backlog Processing
```bash
# Process emails month by month (for initial cleanup)
for month in {01..12}; do
  gmail-spam-cleaner --from-date 2025-${month}-01 --to-date 2025-${month}-31
  sleep 60  # Wait between months
done
```

### CLI Interface (argparse)
```bash
# Basic usage
gmail-spam-cleaner                # Process all unprocessed emails
gmail-spam-cleaner --dry-run      # Test without tagging
gmail-spam-cleaner --verbose      # Debug logging

# Date range filtering (format: YYYY-MM-DD)
gmail-spam-cleaner --from-date 2026-01-01 --to-date 2026-01-31  # January 2026
gmail-spam-cleaner --from-date 2025-12-01 --to-date 2025-12-31  # December 2025

# Monthly processing examples
gmail-spam-cleaner --from-date 2026-01-01 --to-date 2026-01-31 --max-emails 1000
gmail-spam-cleaner --from-date 2026-02-01 --to-date 2026-02-29

# Other options
--max-emails 500      # Limit per run
```

## Configuration Options

**config.py** (using Pydantic Settings):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ollama
    ollama_model: str = "llama3.2:3b"
    ollama_url: str = "http://localhost:11434/api/generate"
    
    # Gmail
    batch_size: int = 100
    max_emails_per_run: int = 1000
    label_name: str = "NeedsReview/Spam"
    mark_as_read: bool = False
    
    # Processing
    state_file: str = "processed_emails.json"
    log_file: str = "logs/agent.log"
    credentials_file: str = "credentials.json"
    token_file: str = "token.json"
    
    class Config:
        env_file = ".env"
        env_prefix = "GMAIL_CLEANER_"
```

**models.py** (Pydantic models):
```python
from pydantic import BaseModel, EmailStr
from enum import Enum

class Classification(str, Enum):
    SPAM = "SPAM"
    PROMOTIONAL = "PROMOTIONAL"
    LEGITIMATE = "LEGITIMATE"

class Email(BaseModel):
    id: str
    subject: str
    sender: EmailStr
    snippet: str
    labels: list[str] = []

class ClassificationResult(BaseModel):
    email_id: str
    classification: Classification
    reason: str
    confidence: float | None = None
```

## Code Structure Example

**__main__.py**:
```python
import argparse
import logging
from .agent import SpamCleanerAgent
from .config import Settings

def main():
    parser = argparse.ArgumentParser(description='Gmail spam cleaner')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--max-emails', type=int)
    parser.add_argument('--from-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', help='End date (YYYY-MM-DD)')
    args = parser.parse_args()
    
    # Validate date format if provided
    from_date = validate_date(args.from_date) if args.from_date else None
    to_date = validate_date(args.to_date) if args.to_date else None
    
    # Setup logging, load config, run agent
    agent = SpamCleanerAgent(...)
    agent.process_emails(
        dry_run=args.dry_run,
        from_date=from_date,
        to_date=to_date
    )
```

**agent.py**:
```python
class SpamCleanerAgent:
    def __init__(self, gmail_client, ollama_client, config):
        self.gmail = gmail_client
        self.ollama = ollama_client
        self.config = config
    
    def process_emails(self, dry_run=False, from_date=None, to_date=None):
        # Build query with date range
        # Load state → Fetch emails → Classify → Tag → Save state
```

**gmail_client.py** (OAuth handling):
```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

def get_gmail_service():
    creds = None
    if os.path.exists('data/token.json'):
        creds = Credentials.from_authorized_user_file('data/token.json')
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Auto-refresh
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'data/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # Opens browser
        
        # Save token for next time
        with open('data/token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def fetch_emails(service, from_date=None, to_date=None, max_results=100):
    # Build query with date range
    query = 'in:inbox'
    if from_date:
        query += f' after:{from_date.strftime("%Y/%m/%d")}'
    if to_date:
        query += f' before:{to_date.strftime("%Y/%m/%d")}'
    
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()
    return results.get('messages', [])
```

## OAuth Token Storage

**Location**: `data/token.json` (local file, gitignored)

**What's stored**:
- Access token (expires in 1 hour)
- Refresh token (long-lived, auto-renews access token)
- Token metadata (scopes, expiry)

**Security**:
- File permissions: 600 (user read/write only)
- Never committed to git (.gitignore)
- Stored locally on your laptop only
- Token can be revoked via Google Account settings

**First-time flow**:
1. No `token.json` exists → Opens browser
2. You authenticate with Google
3. Token saved to `data/token.json`
4. Future runs: Auto-loads token, auto-refreshes if expired

**No re-authentication needed** unless:
- Token manually deleted
- Token revoked in Google settings
- Permissions (scopes) changed in code

## Estimated Development Time

- Project setup + packaging: 1 hour
- Gmail API integration + OAuth: 1.5 hours
- Ollama client: 1 hour
- Core agent + models: 2 hours
- CLI + logging: 0.5 hours
- Testing + refinement: 2 hours
- **Total**: ~8
1. Open Gmail web/app
2. Filter by label: `NeedsReview/Spam`
3. Review tagged emails
4. If correct: Delete
5. If incorrect: Remove label
6. Agent won't reprocess (tracked in state file)

## Safety Features

- **Dry-run mode**: Log classifications without applying labels
- **Never permanently delete**: Only tag for manual review
- **State tracking**: Never reprocess same email
- **Error logging**: Continue on single email failures
- **Rate limiting**: 100ms sleep between Ollama calls

## Performance

- Gmail API: ~10 emails/sec (with rate limiting)
- Ollama inference: ~2-5 emails/sec (3B model on M1/M2 Mac)
- **Bottleneck**: Ollama inference
- **1000 emails**: ~5-10 minutes total runtime
- **Resource usage**: ~2GB RAM (Ollama), minimal CPU

## Future Enhancements (Optional)

- Web UI for reviewing tagged emails
- Rule-based filters (skip known senders)
- Multiple label categories (Low Priority, Newsletters, etc.)
- Sender whitelist/blacklist
- Batch Ollama calls (if API supports)
- Email statistics dashboard

## Why This Approach Works
Project setup + packaging: 1 hour
- Gmail API integration + OAuth: 1.5 hours
- Ollama client: 1 hour
- Core agent + models: 2 hours
- CLI + logging: 0.5 hours
- Testing + refinement: 2 hours
- **Total**: ~8 deletes, only tags for review  
✅ **Scalable**: Handles 1000+ emails/day easily  
✅ **Debuggable**: Clear logs, state tracking  
✅ **Resumable**: Crash recovery via state file  

## Estimated Development Time

- Gmail API setup: 1 hour
- Core agent logic: 2-3 hours
- Ollama integration: 1 hour
- Testing + refinement: 2 hours
- **Total**: ~6-7 hours

## Known Limitations

- Requires Ollama running locally
- Gmail API needs initial OAuth flow
- Can't access emails in other folders (only INBOX)
- Classification accuracy depends on model quality
- No support for attachments/HTML analysis (only text)

## Alternative: IMAP Approach

If Gmail API quotas are a concern (they aren't), can use IMAP:
- No API limits
- More complex auth
- Slower performance
- Less reliable label management

**Recommendation**: Stick with Gmail API (better in every way for this use case)
