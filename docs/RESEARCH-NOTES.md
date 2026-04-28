# ReguLens Research Notes

**Purpose:** Quick reference for domain research findings  
**Status:** Work in progress  
**Last Updated:** 2026-04-22

---

## Regulatory Sources - REAL FINDINGS ⚠️

### ✅ WORKING SOURCES (Scrapable)

**Research Date:** 2026-04-22 (Updated: 2026-04-24)  
**Finding:** Most government tax sites are NOT structured for easy monitoring. 4 viable sources found.

**1. California FTB - Newsroom**
- **URL:** https://www.ftb.ca.gov/about-ftb/newsroom/index.html
- **Status:** ✅ Scrapable
- **Focus:** Tax news, bulletins, updates
- **Format:** HTML list
- **Why it works:** Centralized newsroom feed

**2. Florida Department of Revenue - TIPs**
- **URL:** https://floridarevenue.com/taxes/tips/Pages/default.aspx
- **Status:** ✅ Scrapable
- **Focus:** Tax Information Publications
- **Format:** HTML list/table
- **Why it works:** Dedicated publications page

**3. Texas Comptroller - Publications**
- **URL:** https://comptroller.texas.gov/taxes/publications/
- **Status:** ✅ Scrapable
- **Focus:** Tax policy letters, bulletins
- **Format:** HTML list
- **Why it works:** Structured publications index

**4. Texas Comptroller - Taxes (General)**
- **URL:** https://comptroller.texas.gov/taxes/
- **Status:** ✅ Scrapable (may need exploration)
- **Focus:** General tax updates
- **Format:** HTML pages
- **Why it works:** Accessible structure

---

### ❌ DIFFICULT SOURCES (Explored but not viable for MVP)

**California Sources (excluding FTB Newsroom):**
- CA FTB Legal Rulings (ftb.ca.gov/tax-pros/law) - PDF-heavy, no central feed
- CA CDTFA (cdtfa.ca.gov) - Scattered updates, no central index
- CA Legislature (leginfo.legislature.ca.gov) - Complex, requires deep scraping
- CA EDD (edd.ca.gov) - Unstructured

**Other:**
- IRS (irs.gov) - Massive site, no simple feed

**Why these don't work:**
- No centralized "new publications" page
- Updates scattered across many pages
- Require complex navigation/search
- High risk of missing updates
- Too time-consuming for MVP

---

## MVP STRATEGY: FastAPI + 4 Working Sources

**Architecture Decision:** FastAPI backend (not Supabase)
- ReguLens is a **data processing pipeline** (scraping + AI + alerts)
- Not a CRUD app → Supabase doesn't fit well
- FastAPI allows scrapers + API + database in one service
- Better for background jobs, AI processing, batch operations
- No vendor lock-in, full control over business logic

**Source Strategy:** Focus on 4 working sources (CA FTB Newsroom + TX x2 + FL)

**Pros:**
- Can ship faster with reliable monitoring
- CA, TX, and FL cover major markets
- Proves the concept with real multi-state data
- CA FTB Newsroom provides critical CA coverage
- All scrapers in Python (unified codebase)

**MVP Simplifications:**
- No client management UI (use CSV data)
- No user management (single hardcoded alert recipient)
- No authentication (add in V2)
- Email alerts are primary deliverable (dashboard optional)

**Remaining Gaps:**
- Other CA sources (CDTFA, Legislature) still difficult - post-MVP
- May need different strategy for comprehensive CA coverage later
- Multi-user support deferred to V2

---

## Alternative Approaches for Difficult Sources

**For CA and other hard-to-monitor sources:**

1. **Email Subscriptions**
   - Many agencies offer email newsletters
   - Parse incoming emails instead of scraping
   - More reliable but delayed

2. **RSS Feeds**
   - Check if FTB/CDTFA have RSS (often hidden)
   - Use RSS aggregator approach

3. **Partnership/API**
   - Contact agencies about data feeds
   - Partner with Bloomberg/Thomson Reuters for data

4. **Manual Augmentation**
   - Automated for TX/FL
   - Manual upload for CA (interim solution)
   - User can paste CA updates into system

5. **Hybrid Approach**
   - Monitor what's scrapable (TX/FL)
   - Email subscription + parsing for CA
   - Build both capabilities

---

## Additional States (Post-MVP)

### Texas Sources
- Comptroller of Public Accounts: https://comptroller.texas.gov/
  - Publications: https://comptroller.texas.gov/taxes/publications/
- Focus: Franchise tax, sales tax (no state income tax)
- Note: Legislature meets biennially (every 2 years)

### Florida Sources
- Dept of Revenue: https://floridarevenue.com/
  - Tax law library: https://floridarevenue.com/taxes/lawlibrary/
  - TIPs: https://floridarevenue.com/taxes/tips/Pages/default.aspx
- Focus: Corporate income tax, sales tax, property tax
- What to monitor: Technical Assistance Advisements (TAAs), Tax Information Publications (TIPs)

---

## Client Profile Model (Simplified)

### Client Profile Model (MVP - CSV Based)

**Data Source:** Pre-existing `client_profiles_mvp.csv` (100 clients)

**SQLAlchemy Model Attributes:**

**Identity:**
- id: UUID (generated)
- name: Client code (e.g., TECH_001, MFG_002)
- entity_type: C-Corp | S-Corp | LLC | Partnership | Sole Proprietor

**Geographic:**
- ca_nexus: Boolean (California nexus)
- tx_nexus: Boolean (Texas nexus)
- fl_nexus: Boolean (Florida nexus)

**Industry:**
- industry: Text (e.g., "Software Publishing")
- industry_naics: Text (e.g., "511210")

**Financial:**
- revenue_range: <1M | 1-10M | 10-50M | 50M+
- Why: Threshold tests for applicability

**Tax Activity:**
- tax_credits_used: Array (R&D | Film | Other)
- Why: Alert about credit changes

**Timestamps:**
- created_at, updated_at

**Note:** No user_id in MVP - all clients managed by single hardcoded recipient
**Note:** No email field - clients don't receive alerts (tax professional does)

### Example Client Profiles

**Tech Startup (SaaS):**
- Entity: C-Corp
- Industry: Software
- CA Nexus: Yes (HQ in SF)
- TX Nexus: Yes (remote workers)
- FL Nexus: No
- Revenue: $10-50M
- Credits: Federal + CA R&D
- Activities: AI/ML development, cloud-based

**Impact scenarios:**
- CA R&D credit expansion → HIGH impact
- TX franchise tax apportionment changes → MEDIUM impact
- SaaS apportionment rule changes → MEDIUM impact
- Remote worker nexus guidance → MEDIUM impact

**Manufacturing Company:**
- Entity: C-Corp
- Industry: Manufacturing (auto parts)
- CA Nexus: Yes (warehouse)
- TX Nexus: Yes (operations)
- FL Nexus: Yes (distribution center)
- Revenue: $100M+
- Credits: None
- Activities: Multi-state distribution

**Impact scenarios:**
- CA/TX/FL manufacturing exemptions → MEDIUM impact
- Multi-state sales tax nexus changes → HIGH impact

---

## Domain Insights

### How Tax Pros Currently Monitor
- Manual website checking (15+ hours/week)
- Email subscriptions (high noise-to-signal ratio)
- Professional association newsletters (delayed, generic)
- Commercial services (Bloomberg Tax, Checkpoint) - expensive, still manual search

### Key Pain Points
1. **Information overload:** 90% of alerts not relevant
2. **Client-specificity missing:** "Which of MY 80 clients does this affect?"
3. **Time scarcity:** No time for comprehensive monitoring
4. **Coverage anxiety:** Fear of missing critical updates

### What Makes an Alert Relevant?
- Jurisdiction match (CA nexus)
- Entity type match (affects C-Corps but not partnerships)
- Activity match (uses R&D credit, so cares about R&D changes)
- Revenue threshold (small business exemptions, large filer rules)

### False Positives vs False Negatives
- Tax professionals prefer more alerts (high recall) over missing something (false negative)
- But too many irrelevant alerts = ignored (noise problem)
- Sweet spot: 75-85% precision, >95% recall

---

## Competitive Landscape (Quick Notes)

### Existing Solutions

**Bloomberg Tax / Thomson Reuters Checkpoint:**
- Comprehensive legal research databases
- Generic alerts (not client-specific)
- Expensive (enterprise pricing)
- Still manual search/triage required
- **Gap:** No AI-powered client matching

**Manual Processes:**
- Free but time-consuming
- Incomplete coverage
- Human error risk
- **Gap:** Needs automation

**ReguLens Differentiation:**
- Automated 24/7 monitoring
- AI-powered client matching
- Proactive push alerts (not search)
- Mid-market pricing (not enterprise)

---

## Technical Research

### Web Scraping Considerations
- CA/TX/FL government sites: Generally accessible (no login walls)
- Tools: Playwright (JS-heavy sites) + BeautifulSoup4 (HTML parsing)
- Rate limiting: Be respectful, cache appropriately
- Legal/TOS: Review each site's robots.txt
- Scheduling: APScheduler for daily cron jobs (8 AM)
- Error handling: Retry logic, alert if scraper fails

### AI/LLM Approach
- **Chosen:** Claude (Anthropic) - better reasoning for tax analysis
- **SDK:** Anthropic Python SDK (async support)
- **Summarization:** Extract key points from dense legal text
- **Classification:** Tax topic categorization
- **Matching:** Client attributes → regulation applicability
- **Reasoning:** Explain WHY a client is affected

**Prompt engineering critical:**
- Domain-specific instructions (act as tax expert)
- Structured output (JSON for matching)
- Include client context (entity type, nexus, revenue, credits)
- Request explanation + action items

**Cost estimate:**
- ~$0.01-0.03 per client analysis
- 100 clients × 5 publications/week = 500 analyses
- ~$5-15/week API costs (acceptable for MVP)

### FastAPI Architecture
- **Framework:** FastAPI (async, auto-docs, type safety)
- **Database:** PostgreSQL (Railway) + SQLAlchemy ORM
- **Migrations:** Alembic
- **Background Jobs:** APScheduler (no Redis needed for MVP)
- **Email:** Resend (simpler API than SendGrid)
- **Deployment:** Railway (single service, includes PostgreSQL)

---

## User Research (Informal)

### Persona: Sarah (Tax Partner)
- Manages 80+ clients
- Pain: Information overload, reactive posture
- Need: Contextual alerts ("affects YOUR clients")
- Success: Proactive client service, time reclaimed

### Persona: Michael (Compliance Manager)
- Manages 500+ clients
- Pain: Coverage anxiety, manual monitoring gaps
- Need: 100% coverage confidence, audit trails
- Success: Zero missed changes, scalable operations

### Jobs-to-be-Done
- **Job:** "Keep clients compliant and identify opportunities"
- **Current solution:** Manual monitoring (inadequate)
- **Desired outcome:** Automated, complete, client-specific intelligence
- **Switching barriers:** Trust in AI, data privacy concerns

---

## MVP Assumptions to Validate

- [ ] Tax pros will trust AI-generated analysis (with audit trail + reasoning)
- [ ] CA/TX/FL coverage is sufficient for initial value
- [ ] Email alerts are valuable enough (without dashboard)
- [ ] CSV-based client data is acceptable (no manual data entry UI needed)
- [ ] Daily monitoring frequency is sufficient (vs real-time)
- [ ] Single recipient model works for testing (multi-user not needed yet)
- [ ] >70% alert precision is acceptable (with human review)
- [ ] FastAPI backend can handle daily scraping + AI processing reliably

---

## Open Research Questions

**Domain:**
- [ ] How frequently do CA sources publish? (daily, weekly, monthly?)
- [ ] What % of publications are actually relevant to tax compliance?
- [ ] What are real examples of "missed updates" and their cost?

**User:**
- [ ] Would tax pros onboard 50+ client profiles manually?
- [ ] CSV import sufficient or need tax software integration?
- [ ] Daily digest vs immediate alerts - which preferred?

**Technical:**
- [ ] Can we reliably scrape CA government sites?
- [ ] How to handle PDF-only publications?
- [ ] What's acceptable AI matching accuracy? (75%? 85%? 95%?)

**Business:**
- [ ] Who's the buyer? (Partner vs Compliance Manager vs Managing Partner)
- [ ] Pricing: per-user, per-client, or flat firm rate?
- [ ] What's willingness to pay? ($100/mo? $500/mo? $2000/mo?)

---

## Next Steps

**Week 1: Core Infrastructure + Database**
- [x] Define MVP scope
- [ ] Set up FastAPI project structure
- [ ] Database setup: PostgreSQL + SQLAlchemy models
  - [ ] Client model (with ca/tx/fl nexus fields)
  - [ ] Publication model
  - [ ] Alert model (links publication → client)
- [ ] Alembic migrations setup
- [ ] CSV import script to load 100 client profiles
- [ ] Basic API endpoints (read-only: clients, publications, alerts)
- [ ] Deploy skeleton to Railway (backend + database)

**Week 2: Scraping + Storage**
- [ ] Build scrapers for 4 sources (Python + Playwright/BeautifulSoup)
  - [ ] CA FTB Newsroom scraper
  - [ ] TX Comptroller Publications scraper
  - [ ] TX Comptroller Taxes scraper
  - [ ] FL DOR TIPs scraper
- [ ] APScheduler setup for daily cron jobs (8 AM)
- [ ] Store scraped publications in database
- [ ] Manual scraper trigger endpoint for testing
- [ ] Test: Run all scrapers, verify data quality

**Week 3: AI Matching + Alerts**
- [ ] Claude API integration (Anthropic Python SDK)
- [ ] AI matching function (match publication to client)
- [ ] Background job: Process new publications through AI
  - [ ] Filter clients by state nexus first
  - [ ] Create Alert records for matches
- [ ] Email alert system (Resend/SendGrid)
  - [ ] Email template: publication + affected clients + actions
  - [ ] Send to configured recipient email
- [ ] Test end-to-end: Scrape → AI → Email

**Week 4: Polish + Validation**
- [ ] Error handling + logging for scrapers and AI
- [ ] Retry logic for failures
- [ ] Audit trail (track when publications detected/processed)
- [ ] Test with full 100 client dataset
- [ ] Production deployment to Railway
- [ ] Run for 1 week, monitor daily
- [ ] Share alerts with 1-2 tax professionals for feedback

---

## Useful Links

**Product Inspiration:**
- Site reliability monitoring (PagerDuty, Datadog) → but for regulations
- Legal research (Westlaw, LexisNexis) → but proactive, not search

**Technical References:**
- Playwright docs (web scraping)
- Anthropic Claude API docs
- Supabase docs (auth, database, cron)

---

## Decision Log

**2026-04-22:**
- Decided: Multi-state MVP (CA/TX/FL) with 4 working sources
- Decided: 2-4 week sprint timeline
- Decided: Focus on Tax Partner + Compliance Manager personas
- Initial: Considered Supabase + Next.js stack
- Open: Which LLM (Claude vs GPT)?
- Open: Email provider (Resend vs SendGrid)?

**2026-04-24:**
- Added: CA FTB Newsroom as 4th working source
- Updated: MVP now covers CA/TX/FL (expanded from TX/FL only)

**2026-04-28:**
- Pivoted: FastAPI backend instead of Supabase
- Rationale: ReguLens is data pipeline (scraping + AI), not CRUD app
- FastAPI better for background jobs, AI processing, unified Python codebase
- Decided: Claude API (better reasoning for tax analysis)
- Decided: Resend for email (simpler than SendGrid)

**2026-04-29:**
- Simplified: No client management UI in MVP (use CSV data)
- Simplified: No user management (single hardcoded alert recipient)
- Simplified: No auth system (defer to V2)
- Focus: Core automation (scrape → AI → email alerts)
- Data: Use existing 100 client profiles from CSV
- Alert workflow: All alerts go to one configured email address
- Validation goal: Prove automation works, then add product wrapper in V2

---

**End of research notes - keep updating as you learn!**
