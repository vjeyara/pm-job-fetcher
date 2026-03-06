# PM Job Fetcher

**For Land a PM Job cohort members only.** This is one of the tools you get as part of being in the cohort — customize it to yourself, make it yours, and use it as your base for your job search.

It scans 44+ tech company career pages for PM jobs automatically. No API keys. No installs. Just Python. You tell it which companies you care about, and it finds every open PM role across all of them in seconds.

**Make it yours:** The 44 pre-loaded companies are a starting point. Add the companies on YOUR target list — the ones you're actually applying to. That's where this becomes powerful.

---

## Step 1: Check you have Python

Open Terminal (Mac: search "Terminal" in Spotlight) and type:

```
python3 --version
```

If you see something like `Python 3.x.x`, you're good. If not, download Python from https://www.python.org/downloads/

## Step 2: Pick your companies

You have two options:

### Option A: Chat with Claude Code (recommended)

Open Claude Code in this folder and tell it what companies you want to track. Examples:

- "I want to track Google, Meta, Amazon, and Apple"
- "Add all YC companies from this list: [paste your list]"
- "Here's my spreadsheet of target companies: [paste it]"
- "Add https://boards.greenhouse.io/figma"

Claude will auto-detect each company and set everything up for you.

### Option B: Run the add command yourself

```
python3 add_companies.py Figma Ramp Notion Stripe
```

It auto-detects which job board each company uses. If a company isn't found, paste their careers URL:

```
python3 add_companies.py "https://boards.greenhouse.io/stripe"
```

See your current list:
```
python3 add_companies.py --list
```

**Note:** The tool already comes with 44 companies pre-loaded. You only need to add companies if you want extras or want to start with a different list (`python3 add_companies.py --clear` to start fresh).

## Step 3: Fetch jobs

```
python3 fetch_jobs.py
```

Results appear in the `output/` folder as a markdown file. Open it in any text editor, VS Code, or preview it on GitHub.

Run it again tomorrow and it only shows **new** jobs since last time.

### Other options

```
python3 fetch_jobs.py --all      # Show ALL jobs, not just new ones
python3 fetch_jobs.py --reset    # Clear history and start fresh
```

---

## Optional: Slack notifications

Want to get a Slack message whenever new jobs are found? Here's how:

### 1. Create a Slack app (2 minutes)

1. Go to https://api.slack.com/apps
2. Click **Create New App** > **From scratch**
3. Name it `Job Alerts`, pick your workspace, click **Create App**
4. In the left sidebar, click **Incoming Webhooks**
5. Toggle it **ON**
6. Click **Add New Webhook to Workspace**
7. Pick the channel you want alerts in (e.g., #job-alerts), click **Allow**
8. Copy the webhook URL (starts with `https://hooks.slack.com/...`)

### 2. Add it to settings

Open `settings.json` in any text editor and paste your URL:

```json
{
  "slack_webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

Save the file. Next time you run `python3 fetch_jobs.py`, it will send new jobs to Slack automatically.

---

## Optional: Run automatically every day

### Mac

Open Terminal and type:

```
crontab -e
```

Add this line (runs every day at 9am):

```
0 9 * * * cd /path/to/Job\ Fetcher && python3 fetch_jobs.py
```

Replace `/path/to/Job\ Fetcher` with the actual path to this folder. Save and close.

### Or just ask Claude Code

Open Claude Code in this folder and say: "Set up a daily cron job to run this at 9am."

---

## What's in this folder

| File | What it does |
|------|-------------|
| `fetch_jobs.py` | Main script — fetches and filters PM jobs |
| `add_companies.py` | Helper to add companies by name or URL |
| `companies.json` | Your list of companies to check |
| `settings.json` | Optional Slack webhook URL |
| `seen_jobs.json` | Tracks jobs you've already seen (auto-generated) |
| `output/` | Markdown files with job listings (auto-generated) |
| `CLAUDE.md` | Tells Claude Code how to help you with this project |

## Pre-loaded companies (44)

Stripe, Anthropic, Datadog, GitLab, Airtable, Figma, Gusto, Brex, Amplitude, Coinbase, Twilio, Webflow, Lattice, PagerDuty, Samsara, MongoDB, Grammarly, Asana, Robinhood, Chime, Affirm, Toast, Duolingo, Lyft, Pinterest, Reddit, Instacart, Dropbox, Cloudflare, Databricks, Okta, Elastic, Block, Plaid, HubSpot, Spotify, Netflix, Linear, Ramp, Notion, Vanta, OpenSea, Snowflake, Clerk
