#!/usr/bin/env python3
"""PM Job Fetcher — Find product management jobs across 50+ companies."""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import date, datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "companies.json")
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")
SEEN_JOBS_FILE = os.path.join(SCRIPT_DIR, "seen_jobs.json")
WEEKLY_STATS_FILE = os.path.join(SCRIPT_DIR, "weekly_stats.json")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
REQUEST_TIMEOUT = 15
DELAY_BETWEEN_REQUESTS = 0.5
USER_AGENT = "Mozilla/5.0 (compatible; PMJobFetcher/1.0)"

SENIORITY_ORDER = {"⬆️ Staff PM": 0, "🔹 Senior PM": 1, "📌 PM": 2}
GEO_ORDER = {
    "🇺🇸 United States": 0,
    "🌐 Remote": 1,
    "🇪🇺 Europe": 2,
    "🌏 Asia Pacific": 3,
    "🌍 International": 4,
    "📍 Not Specified": 5,
}


# --- Config ---

def load_config(path):
    if not os.path.exists(path):
        print(f"Error: Config file not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        config = json.load(f)
    errors = []
    if "filters" not in config:
        errors.append("Missing 'filters' key")
    else:
        if "title_keywords" not in config["filters"] or not config["filters"]["title_keywords"]:
            errors.append("'filters.title_keywords' must be a non-empty list")
        if "exclude_keywords" not in config["filters"]:
            errors.append("Missing 'filters.exclude_keywords'")
    if "companies" not in config or not config["companies"]:
        errors.append("'companies' must be a non-empty list")
    else:
        for i, c in enumerate(config["companies"]):
            for key in ("name", "ats", "slug"):
                if key not in c:
                    errors.append(f"Company #{i} missing '{key}'")
            if c.get("ats") not in ("greenhouse", "lever", "ashby"):
                errors.append(f"Company '{c.get('name', i)}': ats must be greenhouse, lever, or ashby")
    if errors:
        print("Config validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    return config


# --- ATS Fetchers ---

def fetch_greenhouse(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    jobs = []
    for j in data.get("jobs", []):
        location = j.get("location", {})
        if isinstance(location, dict):
            location = location.get("name", "")
        jobs.append({
            "id": str(j["id"]),
            "title": j.get("title", ""),
            "location": location or "",
            "url": j.get("absolute_url", ""),
            "posted_at": j.get("updated_at", ""),
        })
    return jobs


def fetch_lever(slug):
    url = f"https://api.lever.co/v0/postings/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    jobs = []
    for j in data:
        categories = j.get("categories", {})
        location = categories.get("location", "") if isinstance(categories, dict) else ""
        jobs.append({
            "id": str(j["id"]),
            "title": j.get("text", ""),
            "location": location or "",
            "url": j.get("hostedUrl", ""),
            "posted_at": j.get("createdAt"),  # Unix ms timestamp
        })
    return jobs


def fetch_ashby(slug):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    jobs = []
    for j in data.get("jobs", []):
        location = j.get("location", "")
        if isinstance(location, dict):
            location = location.get("name", "")
        jobs.append({
            "id": str(j["id"]),
            "title": j.get("title", ""),
            "location": location or "",
            "url": j.get("jobUrl", ""),
            "posted_at": j.get("publishedAt", j.get("updatedAt", "")),
        })
    return jobs


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}


# --- Classification ---

def parse_posted_date(raw):
    """Parse Greenhouse ISO string, Lever Unix-ms, or Ashby ISO into a date object."""
    if not raw:
        return None
    try:
        if isinstance(raw, (int, float)):
            return datetime.utcfromtimestamp(raw / 1000).date()
        return date.fromisoformat(str(raw)[:10])
    except Exception:
        return None


def classify_geography(location):
    if not location or not location.strip():
        return "📍 Not Specified"
    loc = location.lower()
    if "remote" in loc:
        return "🌐 Remote"
    us_signals = [
        "united states", " us,", ", us", "u.s.",
        "san francisco", "new york", "nyc", "seattle", "austin", "boston",
        "chicago", "los angeles", "denver", "atlanta", "miami", "portland",
        "san jose", "palo alto", "menlo park", "mountain view", "sunnyvale",
        "bellevue", "redmond", "cambridge", "washington dc", "raleigh",
        ", ca", ", ny", ", wa", ", tx", ", ma", ", il", ", co", ", ga",
        ", fl", ", nc", ", va", ", or", ", mn", ", oh",
    ]
    if any(s in loc for s in us_signals):
        return "🇺🇸 United States"
    europe_signals = [
        "london", "berlin", "paris", "amsterdam", "dublin", "stockholm",
        "madrid", "barcelona", "munich", "zurich", "copenhagen", "helsinki",
        "oslo", "warsaw", "prague", "lisbon", "brussels", "vienna",
        "united kingdom", "germany", "france", "netherlands", "ireland",
        "sweden", "europe", " uk", "spain", "italy", "poland", "portugal",
    ]
    if any(s in loc for s in europe_signals):
        return "🇪🇺 Europe"
    apac_signals = [
        "singapore", "tokyo", "sydney", "bangalore", "india", "hong kong",
        "seoul", "melbourne", "australia", "japan", "beijing", "shanghai",
        "mumbai", "delhi", "taipei", "jakarta",
    ]
    if any(s in loc for s in apac_signals):
        return "🌏 Asia Pacific"
    return "🌍 International"


def classify_seniority(title):
    t = title.lower()
    if "staff" in t:
        return "⬆️ Staff PM"
    if "senior" in t:
        return "🔹 Senior PM"
    return "📌 PM"


# --- Filtering ---

def is_pm_job(title, filters):
    title_lower = title.lower()
    for kw in filters.get("exclude_keywords", []):
        if kw.lower() in title_lower:
            return False
    matched = False
    for kw in filters["title_keywords"]:
        if kw.lower() in title_lower:
            matched = True
            break
    if not matched:
        return False
    levels = filters.get("experience_levels", [])
    if levels:
        for level in levels:
            if level.lower() in title_lower:
                return True
        return False
    return True


# --- Dedup ---

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen_jobs(seen):
    tmp = SEEN_JOBS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(seen, f, indent=2)
    os.replace(tmp, SEEN_JOBS_FILE)


def make_dedup_key(ats, slug, job_id):
    return f"{ats}:{slug}:{job_id}"


# --- Settings ---

def load_settings():
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    # Environment variable overrides file (used in GitHub Actions)
    if os.environ.get("SLACK_WEBHOOK_URL"):
        settings["slack_webhook_url"] = os.environ["SLACK_WEBHOOK_URL"]
    return settings


# --- Weekly Stats ---

def get_week_start(d=None):
    """Return the Monday of the given date's week."""
    if d is None:
        d = date.today()
    return d - timedelta(days=d.weekday())


def load_weekly_stats():
    if os.path.exists(WEEKLY_STATS_FILE):
        with open(WEEKLY_STATS_FILE, "r") as f:
            return json.load(f)
    return None


def save_weekly_stats(stats):
    tmp = WEEKLY_STATS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(stats, f, indent=2)
    os.replace(tmp, WEEKLY_STATS_FILE)


def update_weekly_stats(new_count, company_names):
    """Accumulate today's job count. Auto-resets on a new Monday."""
    today = date.today()
    week_start = get_week_start(today).isoformat()
    stats = load_weekly_stats()

    if stats is None or stats.get("week_start") != week_start:
        stats = {
            "week_start": week_start,
            "companies_at_week_start": sorted(company_names),
            "daily": {},
        }

    stats["daily"][today.isoformat()] = new_count
    save_weekly_stats(stats)
    return stats


def generate_weekly_summary(stats, current_companies):
    week_start = date.fromisoformat(stats["week_start"])
    week_end = week_start + timedelta(days=6)
    total_jobs = sum(stats["daily"].values())

    companies_at_start = set(stats.get("companies_at_week_start", []))
    companies_now = set(current_companies)
    new_companies = sorted(companies_now - companies_at_start)

    lines = [
        f"# 📋 Weekly PM Jobs Summary",
        f"## Week of {week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')}",
        "",
        "---",
        "",
        "## 📊 At a Glance",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| 🆕 Net new jobs alerted this week | **{total_jobs}** |",
        f"| 🏢 New companies added this week | **{len(new_companies)}** |",
        f"| 🏭 Total companies monitored | **{len(companies_now)}** |",
        "",
        "## 📅 Daily Breakdown",
        "",
        "| Date | New Jobs |",
        "|------|----------|",
    ]

    current = week_start
    while current <= min(week_end, date.today()):
        count = stats["daily"].get(current.isoformat(), 0)
        lines.append(f"| {current.strftime('%a, %b %d')} | {count} |")
        current += timedelta(days=1)

    lines.append("")

    lines.append("## 🏢 New Companies Added This Week")
    lines.append("")
    if new_companies:
        for c in new_companies:
            lines.append(f"- {c}")
    else:
        lines.append("_No new companies added this week._")

    lines.append("")
    return "\n".join(lines)


# --- Slack ---

def send_slack(webhook_url, results, today_str):
    total_new = sum(len(jobs) for jobs in results.values())
    if total_new == 0:
        return
    lines = [f"*PM Job Listings — {today_str}*\n{total_new} new jobs found:\n"]
    for company_key, jobs in sorted(results.items()):
        if not jobs:
            continue
        name, ats = company_key
        lines.append(f"*{name}* ({len(jobs)} jobs)")
        for j in jobs[:5]:
            loc = f" — {j['location']}" if j["location"] else ""
            if j["url"]:
                lines.append(f"  <{j['url']}|{j['title']}>{loc}")
            else:
                lines.append(f"  {j['title']}{loc}")
        if len(jobs) > 5:
            lines.append(f"  ...and {len(jobs) - 5} more")
        lines.append("")
    payload = json.dumps({"text": "\n".join(lines)}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        print("Slack notification sent!")
    except Exception as e:
        print(f"Slack notification failed: {e}")


# --- WhatsApp ---

def send_whatsapp(phone, apikey, results, today_str):
    total_new = sum(len(jobs) for jobs in results.values())
    if total_new == 0:
        return
    lines = [f"New PM Jobs — {today_str}", f"{total_new} new job(s) found:\n"]
    for company_key, jobs in sorted(results.items()):
        if not jobs:
            continue
        name, _ = company_key
        lines.append(f"{name} ({len(jobs)} job(s)):")
        for j in jobs[:3]:
            loc = f" [{j['location']}]" if j["location"] else ""
            lines.append(f"  • {j['title']}{loc}")
            if j["url"]:
                lines.append(f"    {j['url']}")
        if len(jobs) > 3:
            lines.append(f"  ...and {len(jobs) - 3} more")
        lines.append("")
    text = "\n".join(lines)
    encoded = urllib.parse.quote(text)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded}&apikey={apikey}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        print("WhatsApp notification sent!")
    except Exception as e:
        print(f"WhatsApp notification failed: {e}")


# --- Markdown Output ---

def generate_markdown(results, errors, no_jobs_companies, total_companies, today_str):
    total_new = sum(len(jobs) for jobs in results.values())
    lines = [
        f"# PM Job Listings — {today_str}",
        f"> **{total_new} new Senior/Staff PM jobs** across {total_companies} companies"
        + (f" ({len(errors)} errors)" if errors else ""),
        "",
    ]

    if not results:
        lines.append("_No new jobs found today._")
        lines.append("")
    else:
        # Flatten and enrich all jobs with geo/seniority/date
        all_jobs = []
        for (name, ats), jobs in results.items():
            for j in jobs:
                enriched = dict(j)
                enriched["company"] = name
                enriched["geo"] = classify_geography(j["location"])
                enriched["seniority"] = classify_seniority(j["title"])
                enriched["posted_date"] = parse_posted_date(j.get("posted_at"))
                all_jobs.append(enriched)

        # Sort: Geography → Seniority (Staff first) → Company A–Z → Date newest first
        all_jobs.sort(key=lambda j: (
            GEO_ORDER.get(j["geo"], 99),
            SENIORITY_ORDER.get(j["seniority"], 99),
            j["company"].lower(),
            -(j["posted_date"].toordinal() if j["posted_date"] else 0),
        ))

        current_geo = None
        current_seniority = None

        for j in all_jobs:
            # New geography section
            if j["geo"] != current_geo:
                if current_geo is not None:
                    lines.append("")
                current_geo = j["geo"]
                current_seniority = None
                lines.append(f"## {current_geo}")
                lines.append("")

            # New seniority group within geography
            if j["seniority"] != current_seniority:
                if current_seniority is not None:
                    lines.append("")
                current_seniority = j["seniority"]
                lines.append(f"### {current_seniority}")
                lines.append("")
                lines.append("| Company | Title | Posted | Location | Link |")
                lines.append("|---------|-------|--------|----------|------|")

            # Job row
            company = j["company"].replace("|", "\\|")
            title = j["title"].replace("|", "\\|")
            location = (j["location"] or "—").replace("|", "\\|")
            link = f"[Apply]({j['url']})" if j["url"] else "—"
            posted = j["posted_date"]
            posted_str = posted.strftime("%b %d") if posted else "—"
            lines.append(f"| {company} | {title} | {posted_str} | {location} | {link} |")

        lines.append("")

    if no_jobs_companies:
        lines.append("---")
        lines.append("")
        lines.append("## Companies with no new PM jobs")
        lines.append(", ".join(sorted(no_jobs_companies)))
        lines.append("")

    if errors:
        lines.append("## Errors (skipped)")
        for name, msg in sorted(errors):
            lines.append(f"- {name}: {msg}")
        lines.append("")

    return "\n".join(lines)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Fetch PM job listings from company career pages.")
    parser.add_argument("--reset", action="store_true", help="Clear seen jobs and show everything")
    parser.add_argument("--all", action="store_true", help="Show all matching jobs, not just new ones")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to companies.json")
    parser.add_argument("--weekly", action="store_true", help="Force-generate this week's summary now")
    args = parser.parse_args()

    config = load_config(args.config)
    filters = config["filters"]
    companies = config["companies"]
    company_names = [c["name"] for c in companies]

    if args.reset and os.path.exists(SEEN_JOBS_FILE):
        os.remove(SEEN_JOBS_FILE)
        print("Cleared seen jobs history.")

    seen = load_seen_jobs()
    today_str = date.today().strftime("%B %d, %Y")
    today_iso = date.today().isoformat()

    results = {}
    errors = []
    no_jobs = []
    new_count = 0

    print(f"Fetching PM jobs from {len(companies)} companies...\n")

    for i, company in enumerate(companies):
        name = company["name"]
        ats = company["ats"]
        slug = company["slug"]
        print(f"  [{i+1}/{len(companies)}] {name}...", end=" ", flush=True)

        try:
            fetcher = FETCHERS[ats]
            all_jobs = fetcher(slug)
            pm_jobs = [j for j in all_jobs if is_pm_job(j["title"], filters)]

            new_jobs = []
            for j in pm_jobs:
                key = make_dedup_key(ats, slug, j["id"])
                if args.all or key not in seen:
                    new_jobs.append(j)
                    seen[key] = today_iso

            if new_jobs:
                results[(name, ats)] = new_jobs
                new_count += len(new_jobs)
                print(f"{len(new_jobs)} new PM jobs")
            else:
                no_jobs.append(name)
                print("no new PM jobs")

        except urllib.error.HTTPError as e:
            msg = f"HTTP {e.code} — slug may have changed"
            errors.append((name, msg))
            print(f"ERROR ({msg})")
        except urllib.error.URLError as e:
            msg = f"Connection error — {e.reason}"
            errors.append((name, msg))
            print(f"ERROR ({msg})")
        except Exception as e:
            msg = str(e)
            errors.append((name, msg))
            print(f"ERROR ({msg})")

        if i < len(companies) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Save seen jobs
    save_seen_jobs(seen)

    # Generate daily markdown
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"jobs_{date.today().isoformat()}.md")
    md = generate_markdown(results, errors, no_jobs, len(companies), today_str)
    with open(output_file, "w") as f:
        f.write(md)

    # Update weekly stats
    stats = update_weekly_stats(new_count, company_names)

    # Auto-generate weekly summary on Saturdays, or when --weekly flag is used
    is_saturday = date.today().weekday() == 5
    if args.weekly or is_saturday:
        week_start = get_week_start().isoformat()
        weekly_file = os.path.join(OUTPUT_DIR, f"weekly_{week_start}.md")
        weekly_md = generate_weekly_summary(stats, company_names)
        with open(weekly_file, "w") as f:
            f.write(weekly_md)
        print(f"Weekly summary: {weekly_file}")

    # Send Slack notification if configured
    settings = load_settings()
    slack_url = settings.get("slack_webhook_url", "")
    if slack_url and new_count > 0:
        send_slack(slack_url, results, today_str)

    # Send WhatsApp notification if configured
    whatsapp_phone = settings.get("whatsapp_phone", "")
    whatsapp_apikey = settings.get("whatsapp_apikey", "")
    if whatsapp_phone and whatsapp_apikey and new_count > 0:
        send_whatsapp(whatsapp_phone, whatsapp_apikey, results, today_str)

    print(f"\nDone! {new_count} new PM jobs found.")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
