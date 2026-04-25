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

2. **Client Profile Management** ⚠️ UPDATED FOR CA/TX/FL FOCUS
   - Simple web form to create client profiles
   - Key attributes:
     - Entity type (C-Corp, S-Corp, LLC, etc.)
     - Industry
     - **State nexus:** CA nexus (Y/N), TX nexus (Y/N), FL nexus (Y/N)
     - Revenue range
     - Tax credits used (R&D, franchise tax deductions, other)
   - CSV import for bulk setup (20+ clients)

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

5. **Simple Dashboard**
   - Login (email/password)
   - View: recent alerts, client count, sources monitored
   - Mark alerts as "reviewed"
   - Basic audit trail (when detected, when alerted)

### What's OUT (Post-MVP)

- ❌ Additional states beyond CA/TX/FL
- ❌ Mobile app - email + web is enough
- ❌ Team collaboration features
- ❌ Advanced search/filters
- ❌ Integrations with tax software
- ❌ API access
- ❌ White-label/multi-tenant

---

## Technical Stack (Proposed)

### Frontend
- **Framework:** Next.js + React + TypeScript
- **UI:** Tailwind CSS + shadcn/ui
- **Hosting:** Vercel

### Backend
- **Platform:** Supabase (auth + database + API)
- **Database:** PostgreSQL
- **AI:** Claude API (Anthropic) for analysis
- **Email:** Resend or SendGrid

### Monitoring/Scraping
- **Web Scraping:** Playwright or Puppeteer
- **Scheduling:** Cron jobs (Vercel/Railway)
- **Storage:** Supabase Storage for PDFs

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

### 2. Client Profile Schema (Simplified for MVP)

```
Client:
  - id (UUID)
  - name (encrypted)
  - entity_type (enum: C-Corp, S-Corp, LLC, Partnership, Sole Prop)
  - industry (NAICS code or simple dropdown)
  - ca_nexus (boolean)
  - tx_nexus (boolean)
  - fl_nexus (boolean)
  - revenue_range (enum: <1M, 1-10M, 10-50M, 50M+)
  - tax_credits_used (array: R&D, Film, Other)
  - created_at
  - updated_at
```

**Why these attributes?**
- Entity type → determines tax treatment
- State nexus (CA/TX/FL) → filters regulations by jurisdiction
- Revenue → threshold tests for applicability
- Tax credits → alerts about credit changes

---

### 3. AI Matching Logic

**Prompt Template (for Claude API):**
```
You are a multi-state tax expert analyzing a new regulatory publication.

PUBLICATION:
[Title, Date, Full Text, Source State]

CLIENT PROFILE:
- Entity Type: [C-Corp]
- Industry: [Software/SaaS]
- State Nexus: CA - Yes, TX - Yes, FL - No
- Revenue: $10-50M
- Tax Credits: R&D

TASK:
1. Summarize the regulation in 2-3 sentences
2. Determine if this affects the client (YES/NO/MAYBE)
3. If YES or MAYBE:
   - Impact level: HIGH/MEDIUM/LOW
   - Explanation: Why this affects the client
   - Action items: What the client should do
4. Provide your reasoning

Output JSON format:
{
  "summary": "...",
  "affects_client": "YES/NO/MAYBE",
  "impact_level": "HIGH/MEDIUM/LOW",
  "explanation": "...",
  "action_items": ["...", "..."],
  "reasoning": "..."
}
```

---

### 4. User Flows

**Onboarding:**
1. Sign up (email + password)
2. Create first client profile (web form)
3. Or upload CSV with 20+ clients
4. Configure alert preferences (immediate vs daily digest)
5. Done - monitoring starts automatically

**Daily Use:**
1. Receive email: "ReguLens Alert: TX Franchise Tax Update affects 2 clients"
2. Click link → dashboard
3. Review: summary, affected clients, action items
4. Mark as "reviewed"
5. Take action (outside ReguLens for MVP)

---

## 2-4 Week Build Plan

### Week 1: Core Infrastructure
- [ ] Set up Next.js + Supabase project
- [ ] Auth: email/password login
- [ ] Database schema (clients, publications, alerts)
- [ ] Simple dashboard shell (login, nav)
- [ ] Client CRUD: create/edit/list profiles

### Week 2: Monitoring + AI
- [ ] Build scrapers for 4 sources (CA FTB, TX Comptroller x2, FL DOR)
- [ ] Cron job to run daily
- [ ] Store publications in database
- [ ] Integrate Claude API for summarization
- [ ] Test AI matching on 10 real examples

### Week 3: Alerts + Dashboard
- [ ] Build matching engine (publications → clients)
- [ ] Email alert system (Resend/SendGrid)
- [ ] Dashboard: view alerts, client list
- [ ] Mark alerts as reviewed
- [ ] Basic audit trail

### Week 4: Polish + Test
- [ ] CSV import for client profiles
- [ ] Alert preferences (immediate vs digest)
- [ ] Error handling and edge cases
- [ ] Test with 5-10 real client profiles
- [ ] Deploy to production
- [ ] Share with 2-3 beta users

---

## Success Metrics (MVP)

**Product:**
- Detect new publications within 24 hours across all 4 sources (target: >90%)
- Alert precision: >75% of alerts are actually relevant
- System uptime: >95%

**User:**
- 5 beta users onboarded
- 20+ client profiles created
- 10+ alerts delivered
- Positive feedback from 3+ users

**Business:**
- Validate: "Would you pay for this?"
- Target: 2-3 users willing to pay $200-500/month

---

## Open Questions / Decisions Needed

- [ ] Which LLM? Claude vs GPT-4? (Cost vs quality)
- [ ] Email provider? Resend vs SendGrid?
- [ ] How to handle ambiguous matches (MAYBE impact)?
- [ ] Scraping legal/TOS concerns for government sites?
- [ ] Pricing model thinking: per-user? per-client? flat?
- [ ] Multi-state matching complexity - prioritize by state nexus?

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

## Key Files to Build

```
src/
├── app/
│   ├── login/
│   ├── dashboard/
│   ├── clients/
│   │   ├── new/
│   │   ├── [id]/edit/
│   └── alerts/
├── components/
│   ├── ClientForm.tsx
│   ├── AlertCard.tsx
│   └── DashboardStats.tsx
├── lib/
│   ├── scrapers/
│   │   ├── ca-ftb-newsroom.ts
│   │   ├── tx-comptroller-publications.ts
│   │   ├── tx-comptroller-taxes.ts
│   │   └── fl-dor-tips.ts
│   └── ai/
│       ├── claude.ts
│       └── matcher.ts
└── cron/
    └── daily-monitor.ts
```

---

## Notes

- Focus: Ship fast, learn fast
- Don't over-engineer
- Manual fallbacks OK for MVP (e.g., manual scraper runs if cron fails)
- AI doesn't have to be perfect - 75% accuracy + human review is fine
- Get it in users' hands ASAP

---

**Next Step:** Start Week 1 build → Set up infrastructure
