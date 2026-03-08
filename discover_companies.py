#!/usr/bin/env python3
"""
Weekly company discovery digest for PM roles.
Compares a curated master list (Fortune 50, top EU/India lists) against
your existing tracker and surfaces companies you haven't added yet.

Usage:
    python3 discover_companies.py          # run weekly discovery
    python3 discover_companies.py --all    # show all untracked companies (ignore seen history)
    python3 discover_companies.py --reset  # clear seen history (start fresh next run)
    python3 discover_companies.py --list   # show full master list with tracking status
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE    = os.path.join(SCRIPT_DIR, "companies.json")
SETTINGS_FILE  = os.path.join(SCRIPT_DIR, "settings.json")
SEEN_FILE      = os.path.join(SCRIPT_DIR, "discovered_companies.json")
OUTPUT_DIR     = os.path.join(SCRIPT_DIR, "output")

# ─────────────────────────────────────────────────────────────────────────────
# MASTER LIST — curated top companies for PM roles
# Format: (display_name, region, list/category, why_notable)
# ─────────────────────────────────────────────────────────────────────────────
MASTER_COMPANIES = [

    # ═══════════════════════════════════════════
    # UNITED STATES — Fortune 50 & Top Tech
    # ═══════════════════════════════════════════
    ("Apple",           "US", "Fortune 50 · Big Tech",      "Most valuable company; huge PM org across hardware, software, services"),
    ("Microsoft",       "US", "Fortune 50 · Big Tech",      "Azure, Office 365, LinkedIn, GitHub, Copilot"),
    ("Alphabet",        "US", "Fortune 50 · Big Tech",      "Google Search, Cloud, Maps, DeepMind, Waymo"),
    ("Amazon",          "US", "Fortune 50 · Big Tech",      "AWS, Prime, Alexa, Advertising, Grocery"),
    ("Meta",            "US", "Fortune 50 · Big Tech",      "Facebook, Instagram, WhatsApp, Reality Labs"),
    ("Tesla",           "US", "Fortune 50 · EV & AI",       "EVs, FSD, Dojo, Optimus — data-heavy PM roles"),
    ("Walmart",         "US", "Fortune 50 · Retail Tech",   "Massive digital + supply chain transformation"),
    ("JPMorgan Chase",  "US", "Fortune 50 · FinTech",       "Largest US bank; huge internal product platform"),
    ("Visa",            "US", "Fortune 50 · Payments",      "Global payment network and developer APIs"),
    ("Mastercard",      "US", "Fortune 50 · Payments",      "Payment infrastructure and open banking"),
    ("UnitedHealth",    "US", "Fortune 50 · HealthTech",    "Optum, one of the largest HealthTech PM orgs"),
    ("Goldman Sachs",   "US", "Fortune 50 · FinTech",       "Marcus, API banking, trading platforms"),
    ("Salesforce",      "US", "Enterprise SaaS",            "CRM, Slack, Tableau, MuleSoft, Einstein AI"),
    ("Adobe",           "US", "Enterprise SaaS",            "Creative Cloud, Experience Cloud, Firefly AI"),
    ("ServiceNow",      "US", "Enterprise SaaS",            "IT/HR/Finance workflow automation"),
    ("Workday",         "US", "Enterprise SaaS",            "HR and financial management cloud"),
    ("Intuit",          "US", "Consumer FinTech",           "QuickBooks, TurboTax, Credit Karma, Mailchimp"),
    ("PayPal",          "US", "FinTech",                    "Payments, Venmo, Braintree, Hyperwallet"),
    ("Uber",            "US", "Marketplace",                "Rides, Eats, Freight — large PM org"),
    ("Airbnb",          "US", "Marketplace",                "Home and experiences marketplace"),
    ("DoorDash",        "US", "Marketplace",                "Food delivery and local logistics"),
    ("Palantir",        "US", "Data & Gov Tech",            "Gotham, Foundry, AIP — government and enterprise"),
    ("Confluent",       "US", "Data Streaming",             "Kafka-based real-time data platform"),
    ("Snowflake",       "US", "Data Cloud",                 "Cloud data warehousing and sharing"),
    ("Databricks",      "US", "Data & AI",                  "Lakehouse, Unity Catalog, Mosaic AI"),
    ("HashiCorp",       "US", "Developer Tools",            "Terraform, Vault, Consul — infra automation"),
    ("Zendesk",         "US", "CX SaaS",                    "Customer service and engagement platform"),
    ("Atlassian",       "US", "Developer SaaS",             "Jira, Confluence, Trello, Compass"),
    ("Zoom",            "US", "Enterprise SaaS",            "Video, Phone, Contact Center, AI Companion"),
    ("DocuSign",        "US", "Enterprise SaaS",            "Agreement Cloud, Intelligent Agreement Mgmt"),
    ("Veeva Systems",   "US", "Life Sciences SaaS",         "Vault, CRM, commercial cloud for pharma"),
    ("Sprinklr",        "US", "CX SaaS",                    "Unified customer experience management"),
    ("HubSpot",         "US", "MarTech SaaS",               "CRM, Marketing Hub, Sales Hub"),
    ("Klaviyo",         "US", "MarTech",                    "Email and SMS for ecommerce"),
    ("Monday.com",      "US", "Productivity SaaS",          "Work OS — project, product, marketing"),
    ("ClickUp",         "US", "Productivity SaaS",          "All-in-one project management"),
    ("Miro",            "US", "Collaboration",              "Visual workspace and online whiteboard"),
    ("Canva",           "US", "Design Platform",            "AI-first design platform, $26B valuation"),
    ("Rippling",        "US", "HR Tech",                    "HR, IT, Finance unified platform"),
    ("Carta",           "US", "FinTech SaaS",               "Equity management and cap table"),
    ("Calendly",        "US", "Productivity SaaS",          "Scheduling automation platform"),
    ("Vercel",          "US", "Developer Tools",            "Frontend deployment, Next.js creator"),
    ("Wiz",             "US", "Cybersecurity",              "Cloud security, acquired by Google for $32B"),
    ("CrowdStrike",     "US", "Cybersecurity",              "Falcon platform — endpoint and cloud security"),
    ("Palo Alto Networks", "US", "Cybersecurity",           "SASE, XDR, cloud-delivered security"),
    ("Vanta",           "US", "Compliance SaaS",            "Security compliance automation"),
    ("Drata",           "US", "Compliance SaaS",            "Continuous compliance monitoring"),
    ("Hugging Face",    "US", "AI / ML Platform",           "Open source AI — 500K+ models and datasets"),
    ("Scale AI",        "US", "AI / Data",                  "AI training data, RLHF, government AI"),
    ("Perplexity AI",   "US", "AI / Search",                "AI-first search engine, growing fast"),
    ("Harvey AI",       "US", "AI / Legal",                 "AI for law firms and legal professionals"),
    ("Glean",           "US", "AI / Enterprise Search",     "Enterprise AI search across all tools"),
    ("Writer",          "US", "AI / Enterprise",            "Enterprise generative AI platform"),
    ("Anyscale",        "US", "AI Infrastructure",          "Ray distributed computing, managed cloud"),
    ("Rivian",          "US", "EV Tech",                    "Electric delivery vans, R1T/R1S trucks"),
    ("SpaceX",          "US", "Space Tech",                 "Rockets, Starlink — software PM roles exist"),
    ("Roblox",          "US", "Gaming / Metaverse",         "User-generated 3D experiences, 70M+ DAU"),
    ("Epic Games",      "US", "Gaming",                     "Fortnite, Unreal Engine, Epic Games Store"),

    # ═══════════════════════════════════════════
    # EUROPE — Top Tech & Fintech
    # ═══════════════════════════════════════════
    ("SAP",               "Europe", "Germany · Enterprise SaaS",  "Largest European software company"),
    ("Spotify",           "Europe", "Sweden · Consumer Tech",     "Audio streaming, podcasts, audiobooks"),
    ("Klarna",            "Europe", "Sweden · FinTech",           "BNPL and shopping assistant platform"),
    ("Revolut",           "Europe", "UK · FinTech / Neobank",     "Digital bank, $45B valuation, 40M+ users"),
    ("Wise",              "Europe", "UK · FinTech",               "International money transfers and accounts"),
    ("Monzo",             "Europe", "UK · FinTech",               "UK's leading consumer digital bank"),
    ("Starling Bank",     "Europe", "UK · FinTech",               "UK SME and consumer digital bank"),
    ("Checkout.com",      "Europe", "UK · Payments",              "Enterprise payment processing platform"),
    ("GoCardless",        "Europe", "UK · Payments",              "Bank-to-bank recurring payment network"),
    ("SumUp",             "Europe", "UK · SME FinTech",           "Mobile card payments for small businesses"),
    ("Adyen",             "Europe", "Netherlands · Payments",     "Unified payments platform for enterprise"),
    ("Mollie",            "Europe", "Netherlands · Payments",     "Payments for European SMBs"),
    ("Booking.com",       "Europe", "Netherlands · Travel Tech",  "World's largest accommodation platform"),
    ("ASML",              "Europe", "Netherlands · Semiconductors", "Monopoly on EUV chip-making machines"),
    ("Qonto",             "Europe", "France · FinTech",           "Business banking for SMEs"),
    ("Spendesk",          "Europe", "France · FinTech",           "Spend management for finance teams"),
    ("Pennylane",         "Europe", "France · FinTech",           "Finance management and accounting SaaS"),
    ("Alan",              "Europe", "France · HealthTech",        "Digital-first health insurance"),
    ("Doctolib",          "Europe", "France · HealthTech",        "Doctor appointment booking, 80M+ patients"),
    ("Back Market",       "Europe", "France · Marketplace",       "Certified refurbished devices marketplace"),
    ("Contentsquare",     "Europe", "France · Analytics",         "Digital experience analytics"),
    ("Ledger",            "Europe", "France · Crypto",            "Hardware wallets and crypto security"),
    ("Zalando",           "Europe", "Germany · E-commerce",       "Fashion and lifestyle platform, 50M+ customers"),
    ("Delivery Hero",     "Europe", "Germany · Marketplace",      "Food delivery in 70+ countries"),
    ("HelloFresh",        "Europe", "Germany · DTC",              "Meal kit delivery, largest globally"),
    ("Celonis",           "Europe", "Germany · Enterprise SaaS",  "Process mining and execution management"),
    ("Personio",          "Europe", "Germany · HR Tech",          "HR platform for European SMEs"),
    ("GetYourGuide",      "Europe", "Germany · Travel Tech",      "Tours and experiences booking"),
    ("Trade Republic",    "Europe", "Germany · FinTech",          "Investment and savings app"),
    ("Mambu",             "Europe", "Germany · BankTech",         "Cloud-native banking platform"),
    ("SolarisBank",       "Europe", "Germany · BaaS",             "Banking as a Service for fintechs"),
    ("N26",               "Europe", "Germany · FinTech",          "International digital bank"),
    ("Billie",            "Europe", "Germany · B2B FinTech",      "Buy Now Pay Later for businesses"),
    ("Pleo",              "Europe", "Denmark · FinTech",          "Smart company cards and spend management"),
    ("Bolt",              "Europe", "Estonia · Marketplace",      "Ride-hailing + delivery in 45+ countries"),
    ("Pipedrive",         "Europe", "Estonia · CRM SaaS",         "Sales CRM for small teams"),
    ("Wolt",              "Europe", "Finland · Marketplace",      "Food delivery, owned by DoorDash"),
    ("Northvolt",         "Europe", "Sweden · CleanTech",         "EV battery manufacturer, BMW/VW backed"),
    ("Einride",           "Europe", "Sweden · Autonomous",        "Electric autonomous freight trucks"),
    ("Wayve",             "Europe", "UK · Autonomous Vehicles",   "AI for autonomous vehicles"),
    ("Skyscanner",        "Europe", "UK · Travel Tech",           "Flight and hotel search comparison"),
    ("Deliveroo",         "Europe", "UK · Marketplace",           "Food delivery, publicly listed"),
    ("Accurx",            "Europe", "UK · HealthTech",            "Healthcare communication platform (NHS)"),
    ("Synthesia",         "Europe", "UK · AI Video",              "AI video generation for enterprise"),
    ("Featurespace",      "Europe", "UK · AI / FinTech",          "Behavioral analytics for fraud detection"),
    ("ComplyAdvantage",   "Europe", "UK · RegTech",               "Financial crime risk intelligence"),
    ("Thought Machine",   "Europe", "UK · BankTech",              "Cloud-native core banking (Vault)"),
    ("Onfido",            "Europe", "UK · RegTech",               "Digital identity verification"),
    ("Flagright",         "Europe", "Germany · RegTech",          "Real-time AML compliance for FinTechs"),
    ("Hawk AI",           "Europe", "Germany · AI / FinTech",     "Transaction monitoring with AI"),

    # ═══════════════════════════════════════════
    # INDIA — Unicorns, Top Product & Tech
    # ═══════════════════════════════════════════
    ("Flipkart",          "India", "E-commerce",              "India's largest e-commerce, Walmart owned"),
    ("Meesho",            "India", "Social Commerce",         "Reseller e-commerce, 150M+ users"),
    ("Nykaa",             "India", "Beauty E-commerce",       "Publicly listed beauty and fashion platform"),
    ("Zepto",             "India", "Quick Commerce",          "10-minute grocery delivery, $1.4B raised"),
    ("Blinkit",           "India", "Quick Commerce",          "Instant delivery, owned by Zomato"),
    ("Swiggy",            "India", "Food & Quick Commerce",   "Food delivery + Instamart, IPO 2024"),
    ("Zomato",            "India", "Food & Commerce",         "Food delivery, listed; owns Blinkit, Hyperpure"),
    ("Razorpay",          "India", "FinTech",                 "Payment gateway and banking stack, $7.5B"),
    ("PhonePe",           "India", "FinTech / Payments",      "UPI payments leader, Walmart owned, $12B"),
    ("CRED",              "India", "FinTech / Lifestyle",     "Credit card rewards and financial services"),
    ("BharatPe",          "India", "FinTech",                 "Merchant payments and PostPe credit"),
    ("Groww",             "India", "FinTech / Investment",    "Stock and mutual fund investing, $3B"),
    ("Zerodha",           "India", "FinTech / Brokerage",     "India's largest discount broker"),
    ("INDmoney",          "India", "FinTech / Wealth",        "Super money app for NRI and residents"),
    ("Jupiter",           "India", "FinTech / Neobank",       "Digital bank for salaried professionals"),
    ("Cashfree Payments", "India", "FinTech Infra",           "Payment infrastructure and payouts"),
    ("Juspay",            "India", "FinTech Infra",           "Payment orchestration and UX"),
    ("Setu",              "India", "FinTech API",             "Open banking and payments APIs (Pi Labs)"),
    ("Perfios",           "India", "FinTech / Data",          "Financial data intelligence platform"),
    ("Signzy",            "India", "RegTech / AI",            "Digital onboarding and KYC"),
    ("Ola",               "India", "Mobility",                "Ride-hailing + Ola Electric, $6B+ valuation"),
    ("Rapido",            "India", "Mobility",                "Bike taxi and auto, 200M+ users"),
    ("Ola Electric",      "India", "EV Tech",                 "India's #1 electric scooter brand, listed"),
    ("Ather Energy",      "India", "EV Tech",                 "Premium electric scooters"),
    ("Byju's",            "India", "EdTech",                  "Largest EdTech globally, facing restructuring"),
    ("Unacademy",         "India", "EdTech",                  "Online exam prep and live learning"),
    ("upGrad",            "India", "EdTech / WorkTech",       "Online higher education and skilling"),
    ("Physics Wallah",    "India", "EdTech",                  "Affordable test prep, $2.8B valuation"),
    ("Practo",            "India", "HealthTech",              "Doctor consultation and hospital management"),
    ("PharmEasy",         "India", "HealthTech",              "Online pharmacy and diagnostics"),
    ("Pristyn Care",      "India", "HealthTech",              "Surgical care marketplace platform"),
    ("Innovaccer",        "India", "HealthTech / Data",       "Health data platform, US and India"),
    ("Acko",              "India", "InsurTech",               "Digital-first general and health insurance"),
    ("PolicyBazaar",      "India", "InsurTech",               "Insurance aggregator, publicly listed"),
    ("Digit Insurance",   "India", "InsurTech",               "Simplified general insurance"),
    ("Zoho",              "India", "Enterprise SaaS",         "Suite of 50+ business apps, bootstrapped"),
    ("Freshworks",        "India", "Enterprise SaaS",         "CRM, ITSM, customer support, listed"),
    ("BrowserStack",      "India", "Dev Tools / SaaS",        "Cross-browser and app testing platform"),
    ("Postman",           "India", "Dev Tools",               "API collaboration platform, $5.6B"),
    ("Chargebee",         "India", "FinTech SaaS",            "Subscription billing and revenue management"),
    ("CleverTap",         "India", "MarTech SaaS",            "Mobile engagement and analytics"),
    ("MoEngage",          "India", "MarTech SaaS",            "Customer engagement and retention"),
    ("Darwinbox",         "India", "HR Tech SaaS",            "Cloud HR platform, $950M valuation"),
    ("Leadsquared",       "India", "CRM SaaS",                "Sales and marketing CRM, $1B valuation"),
    ("Exotel",            "India", "Communication SaaS",      "Cloud telephony and contact center"),
    ("InMobi",            "India", "AdTech",                  "Global mobile advertising platform"),
    ("Dream11",           "India", "Gaming / Fantasy",        "Fantasy sports platform, $8B valuation"),
    ("Mobile Premier League", "India", "Gaming",              "Mobile gaming and e-sports"),
    ("Sharechat",         "India", "Social Media",            "Indian language social platform, $5B"),
    ("Dailyhunt",         "India", "Media / Content",         "News + short video (Josh), 300M+ users"),
    ("Glance",            "India", "Media / Content",         "AI lock screen content, InMobi group"),
    ("OYO Rooms",         "India", "Travel / Hospitality",    "Hotel aggregator and management"),
    ("MakeMyTrip",        "India", "Travel Tech",             "India's largest travel platform, listed"),
    ("Ixigo",             "India", "Travel Tech",             "Travel discovery and booking"),
    ("Zetwerk",           "India", "B2B / Manufacturing",     "B2B manufacturing marketplace, $2.7B"),
    ("Udaan",             "India", "B2B E-commerce",          "B2B trade platform for retailers"),
    ("Delhivery",         "India", "Logistics",               "Supply chain and logistics, listed"),
    ("Shiprocket",        "India", "Logistics SaaS",          "Ecommerce shipping aggregator"),
    ("Shadowfax",         "India", "Last-mile Logistics",     "Hyperlocal delivery platform"),
    ("BlackBuck",         "India", "Trucking Tech",           "Digital trucking and logistics, listed"),
    ("Locus",             "India", "Logistics SaaS",          "Supply chain decision intelligence"),
    ("Cars24",            "India", "Auto Tech",               "Used car buying and selling, $3.3B"),
    ("Spinny",            "India", "Auto Tech",               "Full-stack used car platform"),
    ("Urban Company",     "India", "Home Services",           "At-home services marketplace"),
    ("NoBroker",          "India", "Real Estate Tech",        "No-commission property platform"),
    ("Livspace",          "India", "Interior Design Tech",    "Online interior design and renovation"),
    ("CoinDCX",           "India", "Crypto",                  "India's largest crypto exchange"),
    ("CoinSwitch",        "India", "Crypto",                  "Crypto investment platform"),
    ("Polygon",           "India", "Web3 / Blockchain",       "Ethereum scaling solution, global"),
    ("Ninjacart",         "India", "AgriTech",                "Fresh produce B2B supply chain"),
    ("DeHaat",            "India", "AgriTech",                "End-to-end farmer services platform"),
    ("TCS",               "India", "IT Services · Product",   "Global IT services + product engineering teams"),
    ("Infosys",           "India", "IT Services · Product",   "Global IT + Infosys BPM product teams"),
    ("Wipro",             "India", "IT Services · Product",   "IT services with engineering product segment"),
    ("HCL Technologies",  "India", "IT Services · Products",  "Software products + engineering services"),
    ("Freshworks",        "India", "Enterprise SaaS",         "CRM, ITSM, customer support, listed"),
    ("Persistent Systems","India", "Digital Engineering",     "Product engineering partner for global firms"),
    ("Mphasis",           "India", "FinTech IT Services",     "Financial services and digital tech"),
]

# De-duplicate by (name, region)
seen = set()
DEDUPED_COMPANIES = []
for entry in MASTER_COMPANIES:
    key = (entry[0].lower(), entry[1])
    if key not in seen:
        seen.add(key)
        DEDUPED_COMPANIES.append(entry)
MASTER_COMPANIES = DEDUPED_COMPANIES


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def tracked_names():
    """Return lowercase set of company names already in companies.json."""
    config = load_json(CONFIG_FILE, {"companies": []})
    return {c["name"].lower() for c in config.get("companies", [])}


def seen_suggestions():
    """Return lowercase set of names that have already been surfaced in a digest."""
    data = load_json(SEEN_FILE, {"seen": []})
    return set(data.get("seen", []))


def mark_seen(names):
    data = load_json(SEEN_FILE, {"seen": []})
    existing = set(data.get("seen", []))
    existing.update(n.lower() for n in names)
    data["seen"] = sorted(existing)
    data["last_run"] = datetime.now().isoformat()
    save_json(SEEN_FILE, data)


def send_slack(webhook_url, message):
    payload = json.dumps({"text": message}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print(f"  [Slack] Failed: {e}")
        return False


def group_by_region(companies):
    groups = {}
    for name, region, category, why in companies:
        groups.setdefault(region, []).append((name, category, why))
    return groups


def region_emoji(region):
    if region == "US":
        return "🇺🇸"
    if region == "Europe":
        return "🇪🇺"
    if region == "India":
        return "🇮🇳"
    return "🌐"


# ─────────────────────────────────────────────────────────────────────────────
# Discovery logic
# ─────────────────────────────────────────────────────────────────────────────

def discover(show_all=False):
    already_tracked = tracked_names()
    already_seen    = set() if show_all else seen_suggestions()

    new_companies = []
    for name, region, category, why in MASTER_COMPANIES:
        if name.lower() in already_tracked:
            continue
        if name.lower() in already_seen:
            continue
        new_companies.append((name, region, category, why))

    return new_companies, already_tracked


def generate_digest(new_companies, already_tracked):
    today       = datetime.now()
    week_str    = today.strftime("Week %W, %Y")
    date_str    = today.strftime("%B %d, %Y")
    total_new   = len(new_companies)
    total_master = len(MASTER_COMPANIES)
    total_tracked = sum(
        1 for name, region, category, why in MASTER_COMPANIES
        if name.lower() in already_tracked
    )

    groups = group_by_region(new_companies)

    lines = [
        f"# 🔍 Company Discovery Digest — {week_str}",
        f"> Generated {date_str} · {total_new} new companies to explore · {total_tracked}/{total_master} already in your tracker",
        "",
        "---",
        "",
        "## How to add any company below",
        "```bash",
        "python3 add_companies.py \"Company Name\"",
        "```",
        "",
        "---",
        "",
    ]

    for region in ["US", "Europe", "India"]:
        companies = groups.get(region, [])
        if not companies:
            continue
        emoji = region_emoji(region)
        lines.append(f"## {emoji} {region} ({len(companies)} companies)")
        lines.append("")

        for name, category, why in sorted(companies, key=lambda x: x[0].lower()):
            lines.append(f"### {name}")
            lines.append(f"- **List / Category:** {category}")
            lines.append(f"- **Why relevant for PM roles:** {why}")
            lines.append(f"- **Add to tracker:** `python3 add_companies.py \"{name}\"`")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines += [
        "## About this digest",
        "",
        f"- Master list size: **{total_master} companies** across US, Europe, and India",
        f"- Already in your tracker: **{total_tracked}**",
        f"- Shown this week: **{total_new}**",
        "",
        "Run again next week to see newly surfaced companies.",
        f"> Sources: Fortune 500, Forbes Global 2000, EU tech unicorn lists, Nasscom / Inc42 India rankings",
    ]

    return "\n".join(lines)


def generate_slack_summary(new_companies, week_str):
    total = len(new_companies)
    if total == 0:
        return f"*Company Discovery — {week_str}*\n\nNo new companies to surface this week. You're fully up to date! 🎉"

    lines = [
        f"*🔍 Company Discovery Digest — {week_str}*",
        f"_{total} companies you haven't tracked yet_",
        "",
    ]

    groups = group_by_region(new_companies)
    for region in ["US", "Europe", "India"]:
        companies = groups.get(region, [])
        if not companies:
            continue
        emoji = region_emoji(region)
        lines.append(f"*{emoji} {region}* ({len(companies)})")
        for name, category, _ in sorted(companies, key=lambda x: x[0].lower()):
            lines.append(f"  • {name} _{category}_")
        lines.append("")

    lines.append("_Add any company: `python3 add_companies.py \"Name\"`_")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if "--reset" in args:
        save_json(SEEN_FILE, {"seen": [], "last_run": None})
        print("Reset discovery history. Next run will show all untracked companies.")
        return

    if "--list" in args:
        already_tracked = tracked_names()
        already_seen    = seen_suggestions()
        print(f"\n{'COMPANY':<30} {'REGION':<8} {'STATUS'}")
        print("-" * 65)
        for name, region, category, _ in sorted(MASTER_COMPANIES, key=lambda x: (x[1], x[0])):
            if name.lower() in already_tracked:
                status = "✅ tracked"
            elif name.lower() in already_seen:
                status = "👀 shown"
            else:
                status = "🆕 new"
            print(f"  {name:<28} {region:<8} {status}  ({category})")
        return

    show_all = "--all" in args
    new_companies, already_tracked = discover(show_all=show_all)

    today    = datetime.now()
    week_str = today.strftime("Week %W, %Y")

    print(f"\n📋 Company Discovery — {week_str}")
    print(f"   Master list: {len(MASTER_COMPANIES)} companies")
    print(f"   Already tracked by you: {len(already_tracked)}")
    print(f"   New this week: {len(new_companies)}")

    if not new_companies:
        print("\n🎉 You're already tracking everything in the master list!")
        print("   Run with --reset to start fresh, or add more companies to the master list.")
        return

    # Save digest
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"discovery_{today.strftime('%Y_W%W')}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    digest = generate_digest(new_companies, already_tracked)
    with open(filepath, "w") as f:
        f.write(digest)
    print(f"\n✅ Digest saved: output/{filename}")

    # Send to Slack
    settings = load_json(SETTINGS_FILE, {})
    if os.environ.get("SLACK_WEBHOOK_URL"):
        settings["slack_webhook_url"] = os.environ["SLACK_WEBHOOK_URL"]
    webhook = settings.get("slack_webhook_url", "").strip()
    if webhook and webhook.startswith("https://"):
        print("   Sending Slack summary...", end=" ", flush=True)
        slack_msg = generate_slack_summary(new_companies, week_str)
        ok = send_slack(webhook, slack_msg)
        print("sent!" if ok else "failed.")
    else:
        print("   (Slack not configured — skipping notification)")

    # Mark as seen
    if not show_all:
        mark_seen([name for name, *_ in new_companies])
        print("   Discovery history updated (won't repeat these next week)")

    print(f"\nOpen the digest: output/{filename}")
    print("Add a company:  python3 add_companies.py \"Company Name\"")


if __name__ == "__main__":
    main()
