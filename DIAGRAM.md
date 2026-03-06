# PM Job Fetcher — System Diagram

Paste the Mermaid block below into any of these:
- **GitHub** — paste directly into any `.md` file
- **Notion** — create a Code block, select "Mermaid"
- **VS Code** — install "Markdown Preview Mermaid Support" extension
- **Live editor** — go to mermaid.live and paste

---

```mermaid
flowchart TD

    USER([👤 You]) --> SETUP
    USER --> RUN

    %% ── HUB 1: SETUP ──────────────────────────────────────────
    subgraph SETUP["🛠️  HUB 1 · Setup  (one-time)"]
        direction LR
        AC["add_companies.py\nauto-detect ATS"] --> CJ
        CJ[("companies.json\n83 companies\nGreenhouse · Lever · Ashby")]
        SE[("settings.json\nSlack webhook\nWhatsApp API")]
    end

    %% ── HUB 2: FETCH ──────────────────────────────────────────
    subgraph FETCH["🔍  HUB 2 · Fetch  (fetch_jobs.py)"]
        direction LR
        CJ --> ORCH["fetch_jobs.py\nOrchestrator"]
        ORCH --> GH["🟢 Greenhouse API\n~50 companies\nStripe · Coinbase · Brex…"]
        ORCH --> LV["🔵 Lever API\n~10 companies\nSpotify · Netflix · Plaid…"]
        ORCH --> AS["🟠 Ashby API\n~23 companies\nNotion · Ramp · Snowflake…"]
    end

    %% ── HUB 3: FILTER ─────────────────────────────────────────
    subgraph FILTER["🔎  HUB 3 · Filter Engine"]
        direction TB
        GH & LV & AS --> TK["① Title Keywords\nProduct Manager · TPM · PM…"]
        TK -->|"pass"| EX["② Exclude Keywords\nManufacturing · Property Mgr…"]
        EX -->|"pass"| EL["③ Experience Level\nsenior  ·  staff"]
        TK -->|"fail"| DROP1(["❌ Dropped"])
        EX -->|"fail"| DROP2(["❌ Dropped"])
        EL -->|"fail"| DROP3(["❌ Dropped"])
    end

    %% ── HUB 4: MEMORY ─────────────────────────────────────────
    subgraph MEMORY["🧠  HUB 4 · Memory  (dedup)"]
        direction LR
        EL -->|"pass"| CHECK{"seen_jobs.json\nAlready seen?"}
        CHECK -->|"Yes"| SKIP(["⏭️ Skip"])
        CHECK -->|"No"| NEW["✅ New Job\n(add to seen)"]
    end

    %% ── HUB 5: OUTPUT ─────────────────────────────────────────
    subgraph OUTPUT["📤  HUB 5 · Output"]
        direction LR
        NEW --> MD["📄 Markdown File\noutput/jobs_YYYY-MM-DD.md"]
        SE --> NEW
        NEW --> SL["💬 Slack\nnotification"]
        NEW --> WA["📱 WhatsApp\nnotification"]
    end

    %% ── STYLING ───────────────────────────────────────────────
    style SETUP  fill:#e8f4f8,stroke:#4a90d9,stroke-width:2px
    style FETCH  fill:#e8f8e8,stroke:#27ae60,stroke-width:2px
    style FILTER fill:#fff8e8,stroke:#f39c12,stroke-width:2px
    style MEMORY fill:#f8e8f8,stroke:#8e44ad,stroke-width:2px
    style OUTPUT fill:#f8e8e8,stroke:#e74c3c,stroke-width:2px
    style USER   fill:#2c3e50,color:#fff,stroke:#2c3e50
```

---

## Hub & Spoke Summary

| Hub | Role | Spokes |
|-----|------|--------|
| **Setup** | One-time config | companies.json · settings.json · add_companies.py |
| **Fetch** | Pull raw jobs from ATS APIs | Greenhouse · Lever · Ashby |
| **Filter** | Narrow to relevant roles | Title Keywords → Exclude Keywords → Experience Level |
| **Memory** | Avoid duplicate alerts | seen_jobs.json → new vs. already-seen |
| **Output** | Deliver results | Markdown file · Slack · WhatsApp |

## How to run

```bash
python3 fetch_jobs.py          # fetch new jobs only
python3 fetch_jobs.py --all    # ignore history, show everything
python3 fetch_jobs.py --reset  # clear history and start fresh
```
