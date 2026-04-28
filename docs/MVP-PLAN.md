# ReguLens MVP Plan

**Timeline:** 2-4 weeks  
**Status:** Planning → Build  
**Last Updated:** 2026-04-22

---

## What We're Building

**An AI-powered regulatory monitoring tool that:**
1. Monitors California tax agency websites daily
2. Identifies new regulations/bulletins
3. Matches them to client profiles automatically
4. Sends email alerts when clients are affected

**Core Value:** Eliminate the "manual discovery gap" - from weeks to minutes.

---

## Why This Matters

### The Problem
Tax professionals face a **Manual Discovery Gap**:
- Weeks-long delay between law passage and client impact analysis
- Can't manually track all government bulletins (too many, too scattered)
- Missed opportunities = lost client value
- Missed risks = compliance failures

### Target Users (MVP Focus)

**Primary: Sarah (Tax Partner)**
- Manages 80+ clients across multiple jurisdictions
- Drowning in tax update emails (90% noise)
- Needs: "Which of MY clients does this affect?"
- Current pain: Spends weekends reading government PDFs

**Secondary: Michael (Compliance Manager)**
- Manages 500+ client compliance
- Manual website monitoring (15+ hours/week)
- Needs: 100% coverage confidence + audit trails
- Current pain: Anxious about missed updates

---

## MVP Scope

### What's IN (Must-Have)

1. **Automated Monitoring** ⚠️ UPDATED BASED ON RESEARCH
   - **Focus:** Texas + Florida + California (scrapable sources)
   - Monitor 4 working sources:
     - ✅ California FTB - Newsroom
     - ✅ Texas Comptroller - Publications
     - ✅ Texas Comptroller - Tax Updates
     - ✅ Florida DOR - TIPs (Tax Information Publications)
   - Detect new publications within 24 hours
   - **Why the expansion:** CA FTB Newsroom provides structured publication feed (now viable for MVP)

2. **Client Data (CSV-Based)** ⚠️ NO UI NEEDED FOR MVP
   - Use existing `client_profiles_mvp.csv` (100 sample clients)
   - One-time CSV import via script or API endpoint
   - Read-only client data for matching
   - Key attributes used for AI matching:
     - Entity type (C-Corp, S-Corp, LLC, etc.)
     - Industry (NAICS code)
     - **State nexus:** CA nexus (Y/N), TX nexus (Y/N), FL nexus (Y/N)
     - Revenue range (<1M, 1-10M, 10-50M, 50M+)
     - Tax credits used (R&D, Film, Other)
   - **Scope:** No client creation/edit UI in MVP - just use CSV data

3. **AI Impact Analysis**
   - Use LLM (Claude/GPT) to:
     - Summarize new publications
     - Identify tax implications
     - Match to client profiles
     - Assign impact level (High/Medium/Low)
     - Explain reasoning

4. **Email Alerts**
   - Send email when regulation affects client
   - Include: summary, affected clients, action items
   - Daily digest option (not real-time spam)

5. **Minimal Dashboard (Read-Only)**
   - Single page: recent alerts feed (last 30 days)
   - No authentication (direct access for MVP)
   - Display: publication details, affected clients, impact levels
   - Mark alerts as "reviewed" via button or magic link
   - Basic stats: total alerts, clients, publications scraped
   - Simple HTML/CSS (FastAPI + Jinja2 templates)

### What's OUT (Post-MVP)

- ❌ Client profile UI (create/edit/delete clients) - using CSV data only
- ❌ User authentication/login (dashboard is publicly accessible for MVP)
- ❌ User management (multi-user support) - single user MVP
- ❌ Additional states beyond CA/TX/FL
- ❌ Advanced dashboard features (filters, search, charts)
- ❌ Mobile app - simple responsive web is enough
- ❌ Team collaboration features
- ❌ Integrations with tax software
- ❌ API access for external tools
- ❌ White-label/multi-tenant

---

## Technical Stack

### Frontend (Minimal Dashboard)
- **Framework:** FastAPI + Jinja2 templates (server-side rendering)
- **Architecture:** No separate frontend app - HTML rendered by FastAPI backend
- **Templates:** Jinja2 (like Django templates) - `templates/` folder
- **Static Assets:** CSS, JS, images - `static/` folder
- **UI:** Simple HTML/CSS (Tailwind CSS CDN or plain CSS)
- **Hosting:** Same service as backend (Railway - single deployment)
- **No JavaScript framework needed** (keep it simple)

**Note:** This is NOT a React/Next.js SPA. FastAPI renders HTML server-side and returns complete pages to the browser. Think of it like traditional PHP or Django, not modern SPA architecture.

### Backend
- **Framework:** FastAPI + Python 3.11+
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy + Alembic (migrations)
- **Auth:** FastAPI-Users or JWT tokens
- **API Docs:** Auto-generated OpenAPI (built-in FastAPI)

### Background Jobs & Processing
- **Scheduler:** APScheduler (cron jobs for daily scraping)
- **Web Scraping:** Playwright + BeautifulSoup4
- **AI Processing:** Anthropic Python SDK (Claude API)
- **Email:** Resend or SendGrid Python SDK
- **Async Tasks:** FastAPI BackgroundTasks + asyncio

### Storage & Deployment
- **File Storage:** Local filesystem or S3-compatible storage
- **Deployment:** Railway or Render (single service)
- **Database Hosting:** Railway PostgreSQL or Render PostgreSQL

---

## Core Features Detail

### 1. Source Monitoring

**MVP Sources to Monitor:**

| Source | URL | Check Frequency | Format |
|--------|-----|-----------------|--------|
| CA FTB Newsroom | ftb.ca.gov/about-ftb/newsroom | Daily | HTML |
| TX Comptroller Publications | comptroller.texas.gov/taxes/publications/ | Daily | HTML |
| TX Comptroller Taxes | comptroller.texas.gov/taxes/ | Daily | HTML |
| FL DOR TIPs | floridarevenue.com/taxes/tips/Pages/default.aspx | Daily | HTML |

**Detection Logic:**
- Scrape each source daily
- Compare to previous version (hash/diff)
- Extract new publications
- Store in database with metadata

---

### 2. Database Models (MVP Schema)

**Client Model:**

```python
# models/client.py
from sqlalchemy import Column, String, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # Client code (e.g., TECH_001)
    entity_type = Column(String, nullable=False)  # C-Corp, S-Corp, LLC, Partnership, Sole Prop
    industry = Column(String, nullable=False)
    industry_naics = Column(String, nullable=True)
    ca_nexus = Column(Boolean, default=False)
    tx_nexus = Column(Boolean, default=False)
    fl_nexus = Column(Boolean, default=False)
    revenue_range = Column(String, nullable=False)  # <1M, 1-10M, 10-50M, 50M+
    tax_credits_used = Column(ARRAY(String), default=[])  # [R&D, Film, Other]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Note: No user_id for MVP - all clients managed by single hardcoded user
    # V2: Add user_id foreign key for multi-user support
```

**Publication Model:**

```python
# models/publication.py
class Publication(Base):
    __tablename__ = "publications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    state = Column(String, nullable=False)  # CA, TX, FL
    source = Column(String, nullable=False)  # e.g., "CA FTB Newsroom"
    url = Column(String, nullable=False)
    content = Column(Text)  # Full text or summary
    published_date = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)  # Has AI processing completed?
```

**Alert Model:**

```python
# models/alert.py
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id = Column(UUID, ForeignKey('publications.id'), nullable=False)
    client_id = Column(UUID, ForeignKey('clients.id'), nullable=False)
    
    # AI analysis results
    summary = Column(Text)  # 2-3 sentence summary
    affects_client = Column(String)  # YES, MAYBE, NO
    impact_level = Column(String)  # HIGH, MEDIUM, LOW
    explanation = Column(Text)  # Why this affects the client
    action_items = Column(ARRAY(String))  # What client should do
    reasoning = Column(Text)  # AI reasoning
    
    # Status tracking
    email_sent = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    publication = relationship("Publication", back_populates="alerts")
    client = relationship("Client", back_populates="alerts")
```

**Why these attributes?**
- Entity type → determines tax treatment
- State nexus (CA/TX/FL) → filters regulations by jurisdiction
- Revenue → threshold tests for applicability
- Tax credits → alerts about credit changes
- Alert tracks AI analysis and delivery status

---

### 3. Alert Workflow (MVP)

**The User Model:**
- ReguLens is for **tax professionals** who manage multiple clients
- Sarah (Tax Partner) manages 80+ clients
- When a regulation affects ANY client, Sarah gets ONE email

**MVP Simplification:**
- Single hardcoded recipient (configured in `.env`)
- All 100 CSV clients "belong" to this recipient
- No user management, no auth needed

**Alert Flow:**

```
1. Scraper finds new publication
   └─> Store in database (publications table)

2. AI Processing Job triggers
   ├─> For each client (filtered by state nexus):
   │   ├─> Call Claude API to analyze match
   │   ├─> If affects_client = YES or MAYBE:
   │   │   └─> Create Alert record
   │   └─> Continue to next client
   └─> Mark publication as processed

3. If any alerts created:
   └─> Send ONE email to configured recipient
       ├─> Include publication summary
       ├─> List all affected clients with impact levels
       ├─> Include action items per client
       └─> Mark alerts as email_sent = True

4. Store alerts for audit trail / dashboard
```

**Configuration (`.env`):**

```bash
# Alert recipient (hardcoded for MVP)
ALERT_RECIPIENT_EMAIL=your-email@example.com
ALERT_RECIPIENT_NAME="Tax Professional (MVP)"

# Anthropic API for AI matching
ANTHROPIC_API_KEY=sk-ant-...

# Email service (Resend or SendGrid)
RESEND_API_KEY=re_...
```

**Email Template Example:**

```
Subject: 🚨 ReguLens Alert: TX Franchise Tax Apportionment Rule Change

Hi Tax Professional,

A new regulation has been detected that affects 3 of your clients.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PUBLICATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Title: Franchise Tax Apportionment Formula Update
Source: Texas Comptroller - Publications
State: Texas
Date: April 29, 2026
URL: https://comptroller.texas.gov/taxes/publications/...

Summary: Texas Comptroller announces changes to franchise tax 
apportionment rules for multi-state businesses, effective Q3 2026.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AFFECTED CLIENTS (3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. TECH_002 - Software Publishing (Austin, TX)
   Impact: HIGH
   Reason: C-Corp with multi-state nexus (TX, CA, FL, NY). Revenue 
   $5-10M. Uses franchise tax deductions. Apportionment formula 
   change will directly affect tax calculation.
   
   Action Items:
   • Review current apportionment methodology
   • Recalculate Q3 franchise tax estimates
   • Consult with client on multi-state activity changes

2. MFG_001 - Automotive Parts Manufacturing (Austin, TX)
   Impact: MEDIUM
   Reason: Large C-Corp ($100M+) with TX/CA/FL/MI/OH nexus. High 
   revenue means material dollar impact from formula changes.
   
   Action Items:
   • Assess impact of new formula on tax liability
   • Update quarterly estimates if needed

3. RETAIL_002 - Specialty Retail (Dallas, TX)
   Impact: LOW
   Reason: LLC with TX/CA/FL nexus but primarily TX-based revenue. 
   Apportionment changes may have minimal impact.
   
   Action Items:
   • General awareness, monitor for further guidance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View full details: [Dashboard URL]

This alert was generated by ReguLens AI monitoring.
```

---

### 4. AI Matching Logic

**Python Implementation:**

```python
# ai/matcher.py
from anthropic import AsyncAnthropic
import json

async def match_publication_to_client(publication, client):
    """Use Claude to determine if publication affects client."""
    
    anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    prompt = f"""You are a multi-state tax expert analyzing a new regulatory publication.

PUBLICATION:
Title: {publication.title}
Date: {publication.date}
State: {publication.state}
Content: {publication.content}

CLIENT PROFILE:
- Entity Type: {client.entity_type}
- Industry: {client.industry}
- State Nexus: CA={client.ca_nexus}, TX={client.tx_nexus}, FL={client.fl_nexus}
- Revenue: {client.revenue_range}
- Tax Credits: {', '.join(client.tax_credits_used)}

TASK:
1. Summarize the regulation in 2-3 sentences
2. Determine if this affects the client (YES/NO/MAYBE)
3. If YES or MAYBE:
   - Impact level: HIGH/MEDIUM/LOW
   - Explanation: Why this affects the client
   - Action items: What the client should do
4. Provide your reasoning

Output ONLY valid JSON in this format:
{{
  "summary": "...",
  "affects_client": "YES/NO/MAYBE",
  "impact_level": "HIGH/MEDIUM/LOW",
  "explanation": "...",
  "action_items": ["...", "..."],
  "reasoning": "..."
}}"""

    message = await anthropic.messages.create(
        model="claude-sonnet-4",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(message.content[0].text)
```

---

### 4. User Flows

**Initial Setup (One-Time):**
1. Deploy backend + dashboard to Railway
2. Configure alert recipient email in `.env`
3. Run CSV import script to load 100 sample clients
4. Verify scrapers are running (manual trigger or check logs)
5. Access dashboard at `https://your-app.railway.app/`
6. Monitoring starts automatically (daily cron at 8 AM)

**Daily Automated Flow:**
1. **8:00 AM:** Scrapers run automatically (4 sources)
2. **8:05 AM:** AI processing starts for new publications
   - Matches against 100 clients
   - Creates alerts for affected clients
3. **8:10 AM:** Email sent if any alerts generated
   - One email with all affected clients
   - Sent to configured recipient
4. **Anytime:** View alerts in dashboard at `/`

**User Interaction:**
1. **Via Email:**
   - Receive email: "ReguLens Alert: TX Franchise Tax Update affects 3 clients"
   - Read summary and affected client list
   - Click "View in Dashboard" link → opens dashboard
   - Click "Mark as Reviewed" magic link → marks alert reviewed

2. **Via Dashboard:**
   - Visit `https://your-app.railway.app/`
   - See feed of all recent alerts (last 30 days)
   - Click alert to see full details
   - Click "Mark as Reviewed" button
   - See which alerts are pending vs reviewed

**Note:** No user signup/login - dashboard is publicly accessible for MVP

---

## 2-4 Week Build Plan

### Week 1: Core Infrastructure + Database
- [ ] Set up FastAPI project structure (`backend/` directory)
- [ ] Environment configuration (`.env` file)
  - [ ] Database connection string
  - [ ] Alert recipient email
  - [ ] API keys placeholders
- [ ] Database setup: PostgreSQL + SQLAlchemy models
  - [ ] Client model (with nexus, entity type, revenue, etc.)
  - [ ] Publication model (title, source, state, URL, content)
  - [ ] Alert model (links publication → client, stores AI results)
- [ ] Alembic migrations setup (`alembic init`)
- [ ] Create initial migration, run on Railway PostgreSQL
- [ ] CSV import script: `scripts/import_clients.py`
  - [ ] Read `client_profiles_mvp.csv`
  - [ ] Transform and insert into database
- [ ] Test: Import 100 clients successfully
- [ ] Basic API endpoints (FastAPI routes)
  - [ ] GET /clients (list all)
  - [ ] GET /publications (list recent)
  - [ ] GET /alerts (list recent)
- [ ] Deploy skeleton to Railway (backend + database)

### Week 2: Scraping + Storage
- [ ] Build scrapers for 4 sources (CA FTB, TX Comptroller x2, FL DOR)
  - [ ] CA FTB Newsroom scraper (Playwright/BeautifulSoup)
  - [ ] TX Comptroller Publications scraper
  - [ ] TX Comptroller Taxes scraper
  - [ ] FL DOR TIPs scraper
- [ ] Publication storage: database model + API endpoints
- [ ] APScheduler setup: daily cron jobs
- [ ] Test scraping locally + manual run endpoint
- [ ] Store scraped publications in database

### Week 3: AI Matching + Alerts + Dashboard
- [ ] Claude API integration (Anthropic SDK)
  - [ ] Environment variable for API key
  - [ ] Test basic Claude API call
- [ ] AI matching function: `ai/matcher.py`
  - [ ] Match one publication to one client
  - [ ] Parse JSON response from Claude
  - [ ] Handle errors/retries
- [ ] Background job: Process new publications
  - [ ] For each unprocessed publication:
    - [ ] Filter clients by state nexus (only match TX clients to TX pubs)
    - [ ] Call AI matcher for each relevant client
    - [ ] Create Alert records for YES/MAYBE matches
    - [ ] Mark publication as processed
- [ ] Email alert system
  - [ ] Resend or SendGrid integration
  - [ ] Email template builder: format publication + affected clients
  - [ ] Include "View in Dashboard" and "Mark as Reviewed" magic links
  - [ ] Send one email per publication (with all affected clients)
  - [ ] Mark alerts as email_sent=True
- [ ] Minimal dashboard (FastAPI + Jinja2)
  - [ ] Setup Jinja2 templates
  - [ ] Homepage: `/` - alert feed (last 30 days, newest first)
  - [ ] Alert detail: `/alerts/{id}` - full publication + clients
  - [ ] Magic link endpoint: `/alerts/{id}/reviewed` - mark as reviewed
  - [ ] Basic CSS styling (clean, simple, mobile-friendly)
- [ ] Test end-to-end: Scrape → AI → Store → Email → Dashboard

### Week 4: Polish, Test, Deploy
- [ ] Error handling + logging (for scrapers and AI failures)
- [ ] Retry logic for failed scrapes/AI calls
- [ ] Audit trail: track when publications detected/processed
- [ ] Test end-to-end with real client data (100 profiles from CSV)
- [ ] Manual scraper trigger endpoint (for testing/debugging)
- [ ] Dashboard polish:
  - [ ] Add stats: total alerts, pending vs reviewed, sources monitored
  - [ ] Show last scraper run time + status
  - [ ] Add simple filters (show pending only, show by impact level)
  - [ ] Mobile-responsive styling
- [ ] Production deployment to Railway
  - [ ] Backend + database + dashboard (single service)
  - [ ] Configure environment variables
  - [ ] Test scraper cron jobs work on Railway
- [ ] Run for 1 week, monitor daily:
  - [ ] Check email alerts arrive
  - [ ] Check dashboard shows alerts correctly
  - [ ] Monitor scraper logs for failures
- [ ] Share dashboard URL + email alerts with 1-2 tax professionals
- [ ] Collect feedback on alert quality and UI

---

## Success Metrics (MVP)

**Product:**
- Detect new publications within 24 hours across all 4 sources (target: >90%)
- Alert precision: >75% of alerts are actually relevant to matched clients
- System uptime: >95% (daily scraper runs without failure)
- AI matching completes within 5 minutes of publication detection

**Data:**
- 100 client profiles loaded from CSV successfully
- Successfully scrape 4 sources daily (100% uptime for 1 week)
- Generate 5-10+ real alerts in first week
- Zero false negatives (don't miss any publications)
- Email delivery success rate >95%

**Alert Quality:**
- >70% of alerts are HIGH or MEDIUM impact
- <30% false positives (alerts not actually relevant)
- AI reasoning is understandable and accurate

**Validation:**
- Run for 1-2 weeks with real data
- Share alerts with 1-2 tax professionals
- Validate: "Is this alert relevant? Would you act on it?"
- Target: >70% of alerts are deemed actionable
- Collect feedback on false positives

---

## Open Questions / Decisions Needed

- [ ] Which LLM? Claude vs GPT-4? (Cost vs quality) → **Leaning Claude (better reasoning)**
- [ ] Email provider? Resend vs SendGrid? → **Resend (simpler API)**
- [ ] How to handle ambiguous matches (MAYBE impact)? → **Show to user with explanation**
- [ ] Scraping legal/TOS concerns for government sites? → **Check robots.txt, respectful rate limits**
- [ ] Pricing model thinking: per-user? per-client? flat? → **Post-MVP decision**
- [ ] Multi-state matching complexity - prioritize by state nexus? → **Filter by nexus first**
- [x] Frontend: Build or skip? → **Minimal dashboard (FastAPI + Jinja2, read-only)**
- [x] Auth: FastAPI-Users vs simple JWT? → **Skip for MVP (dashboard publicly accessible)**
- [ ] Task queue: APScheduler vs Celery? → **APScheduler for MVP (simpler), Celery if scale**
- [ ] CSS framework: Tailwind vs plain CSS? → **Plain CSS or Tailwind CDN (no build step)**

---

## Post-MVP Roadmap (Future)

**V2 (Month 2-3):**
- Add more CA sources (CDTFA, Legislature)
- Add NY, IL, and other high-priority states
- Mobile-responsive improvements
- Advanced filters

**V3 (Month 4-6):**
- Mobile app (iOS/Android)
- Team collaboration
- Integration with tax software

---

## Project Structure

```
ReguLens/
├── backend/                          # FastAPI application (backend + frontend)
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── config.py                 # Settings (env vars, secrets)
│   │   ├── database.py               # Database connection
│   │   ├── dependencies.py           # Jinja2 templates setup
│   │   ├── models/
│   │   │   ├── client.py             # Client SQLAlchemy model
│   │   │   ├── publication.py        # Publication model
│   │   │   ├── alert.py              # Alert model
│   │   │   └── user.py               # User model (auth)
│   │   ├── schemas/
│   │   │   ├── client.py             # Pydantic schemas for validation
│   │   │   ├── publication.py
│   │   │   └── alert.py
│   │   ├── api/
│   │   │   ├── clients.py            # Client API endpoints (read-only)
│   │   │   ├── publications.py       # Publication API endpoints
│   │   │   └── alerts.py             # Alert API endpoints
│   │   ├── routes/
│   │   │   ├── dashboard.py          # Dashboard HTML routes (/)
│   │   │   └── actions.py            # Magic link actions (/alerts/{id}/reviewed)
│   │   ├── scrapers/
│   │   │   ├── base.py               # Base scraper class
│   │   │   ├── ca_ftb_newsroom.py    # CA FTB scraper
│   │   │   ├── tx_comptroller_pubs.py
│   │   │   ├── tx_comptroller_tax.py
│   │   │   └── fl_dor_tips.py
│   │   ├── ai/
│   │   │   ├── matcher.py            # AI matching logic (Claude)
│   │   │   └── summarizer.py         # Summarization
│   │   ├── jobs/
│   │   │   ├── scheduler.py          # APScheduler setup
│   │   │   ├── scrape_job.py         # Daily scraping job (8 AM)
│   │   │   └── process_job.py        # AI processing + email alerts
│   │   └── utils/
│   │       ├── email.py              # Email sending (Resend/SendGrid)
│   │       └── formatting.py         # Format email templates
│   ├── alembic/                      # Database migrations
│   │   └── versions/
│   ├── tests/
│   └── requirements.txt
│
│   ├── templates/                    # HTML templates (the "frontend")
│   │   ├── base.html                 # Base template with common layout/navigation
│   │   ├── index.html                # Homepage: alerts feed (extends base.html)
│   │   ├── alert_detail.html         # Alert detail page (extends base.html)
│   │   └── reviewed.html             # "Marked as reviewed" confirmation page
│   │
│   ├── static/                       # Static files (CSS, JS, images)
│   │   ├── css/
│   │   │   └── style.css             # Dashboard styles
│   │   ├── js/
│   │   │   └── main.js               # Optional: minimal JS for interactivity
│   │   └── favicon.ico               # Site icon
│   │
│
├── scripts/
│   └── import_clients.py             # Import CSV to database
│
├── data/
│   └── sample/
│       └── client_profiles_mvp.csv   # 100 MVP-ready client profiles
│
├── docs/
├── .env.example                      # Environment variables template
├── .env                              # Actual config (not committed)
├── pyproject.toml                    # Python dependencies (uv/poetry)
└── README.md

# .env.example contents:
# DATABASE_URL=postgresql://user:pass@localhost:5432/regulens
# ALERT_RECIPIENT_EMAIL=your-email@example.com
# ALERT_RECIPIENT_NAME=Tax Professional
# ANTHROPIC_API_KEY=sk-ant-...
# RESEND_API_KEY=re_...
```

---

## Implementation Notes

### Architecture Decisions

**Why FastAPI over Supabase:**
- ReguLens is a **data processing pipeline**, not a CRUD app
- Core features (scraping, AI processing, alerts) are **background jobs**
- Single deployment: scrapers + API + database in one service
- Direct database access (no API overhead for batch operations)
- Better for concurrent AI processing with asyncio
- Full control over business logic

**Technology Choices:**
- **FastAPI:** Async support, auto-generated docs, modern Python
- **SQLAlchemy:** Mature ORM, great for complex queries
- **APScheduler:** Simple cron jobs, no Redis needed for MVP
- **Playwright:** Handles JavaScript-heavy sites if needed
- **Railway/Render:** Simple deployment, PostgreSQL included

### Development Principles

- **Focus: Ship fast, learn fast**
- **Core MVP:** Automated scraping + AI matching + email alerts (that's it!)
- Don't over-engineer - no client UI, no user management, no auth
- Manual fallbacks OK for MVP (manual scraper trigger endpoint)
- AI doesn't have to be perfect - 75% accuracy + human review is fine
- Test with real government sources early (Week 2)
- Email alerts are the primary MVP deliverable (not dashboard)
- Use existing CSV data (100 clients) - no data entry needed
- Can add UI/auth/multi-user in V2 after validating core value

### Scaling Considerations (Post-MVP)

- Switch to Celery + Redis if background jobs become complex
- Add caching (Redis) for frequently accessed data
- Consider separating scraper service if it becomes resource-heavy
- Add monitoring (Sentry, DataDog) for production

---

**Next Step:** Start Week 1 build → Set up FastAPI + Database infrastructure
