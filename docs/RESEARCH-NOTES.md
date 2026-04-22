# ReguLens Research Notes

**Purpose:** Quick reference for domain research findings  
**Status:** Work in progress  
**Last Updated:** 2026-04-22

---

## Regulatory Sources - REAL FINDINGS ⚠️

### ✅ WORKING SOURCES (Scrapable)

**Research Date:** 2026-04-22  
**Finding:** Most government tax sites are NOT structured for easy monitoring. Only 3 viable sources found.

**1. Florida Department of Revenue - TIPs**
- **URL:** https://floridarevenue.com/taxes/tips/Pages/default.aspx
- **Status:** ✅ Scrapable
- **Focus:** Tax Information Publications
- **Format:** Likely HTML list/table
- **Why it works:** Dedicated publications page

**2. Texas Comptroller - Publications**
- **URL:** https://comptroller.texas.gov/taxes/publications/
- **Status:** ✅ Scrapable
- **Focus:** Tax policy letters, bulletins
- **Format:** HTML list
- **Why it works:** Structured publications index

**3. Texas Comptroller - Taxes (General)**
- **URL:** https://comptroller.texas.gov/taxes/
- **Status:** ✅ Scrapable (may need exploration)
- **Focus:** General tax updates
- **Format:** HTML pages
- **Why it works:** Accessible structure

---

### ❌ DIFFICULT SOURCES (Explored but not viable for MVP)

**California Sources:**
- CA Franchise Tax Board (ftb.ca.gov) - No clear publications feed
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

## MVP PIVOT: Start with What Works

**New Strategy:** Focus on the 3 working sources (TX + FL) instead of forcing CA.

**Pros:**
- Can ship faster with reliable monitoring
- TX and FL are still valuable markets
- Proves the concept with real data
- Can add CA later with different approach

**Cons:**
- CA is largest market (we deprioritized it)
- May need different strategy for CA (email subscriptions, API partnerships?)

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

### Minimum Attributes for MVP

**Identity:**
- Client name (internal use only)
- Entity type: C-Corp | S-Corp | LLC | Partnership | Sole Proprietor

**Geographic:**
- Has California nexus? (Y/N)
- Other states? (for future expansion)

**Financial:**
- Revenue range: <$1M | $1-10M | $10-50M | $50M+
- Why: Threshold tests for applicability

**Tax Activity:**
- Tax credits used: R&D | Film | Other
- Why: Alert about credit changes

**Optional (nice to have):**
- Industry (NAICS code or dropdown)
- Number of employees
- Key business activities (SaaS, manufacturing, etc.)

### Example Client Profiles

**Tech Startup (SaaS):**
- Entity: C-Corp
- Industry: Software
- CA Nexus: Yes (HQ in SF)
- Revenue: $10-50M
- Credits: Federal + CA R&D
- Activities: AI/ML development, cloud-based

**Impact scenarios:**
- CA R&D credit expansion → HIGH impact
- SaaS apportionment rule changes → MEDIUM impact
- Remote worker nexus guidance → MEDIUM impact

**Manufacturing Company:**
- Entity: C-Corp
- Industry: Manufacturing (auto parts)
- CA Nexus: Yes (warehouse)
- Revenue: $100M+
- Credits: None
- Activities: Multi-state distribution

**Impact scenarios:**
- CA manufacturing exemptions → MEDIUM impact
- Sales tax nexus changes → HIGH impact

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
- CA government sites: Generally accessible (no login walls)
- RSS feeds: Some available (FTB newsroom likely has RSS)
- PDF bulletins: Need OCR/text extraction
- Rate limiting: Be respectful, cache appropriately
- Legal/TOS: Review each site's terms

### AI/LLM Approach
- **Summarization:** Extract key points from dense legal text
- **Classification:** Tax topic categorization
- **Matching:** Client attributes → regulation applicability
- **Reasoning:** Explain WHY a client is affected

**Prompt engineering critical:**
- Domain-specific instructions (tax expertise)
- Structured output (JSON for matching)
- Examples/few-shot learning

**Model options:**
- Claude (Anthropic): Good reasoning, long context
- GPT-4: Strong performance, widely used
- Cost: ~$0.01-0.03 per analysis (acceptable for MVP)

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

- [ ] Tax pros will trust AI-generated analysis (with audit trail)
- [ ] CA-only is sufficient for initial value (or need multi-state?)
- [ ] Email alerts preferred over dashboard-only
- [ ] Client profile data entry not too burdensome
- [ ] $200-500/month pricing is acceptable
- [ ] Daily monitoring frequency is sufficient (vs real-time)

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

**Week 1 (Planning):**
- [x] Define MVP scope
- [ ] Set up project infrastructure
- [ ] Manual scraping test (visit 5 CA sources, extract sample publications)

**Week 2 (Build):**
- [ ] Build scrapers for top 3 CA sources
- [ ] Test AI analysis on 10 real publications
- [ ] Create client profile schema

**Week 3 (Polish):**
- [ ] Matching engine + alerts
- [ ] Dashboard + basic UX
- [ ] End-to-end testing

**Week 4 (Launch):**
- [ ] Beta with 3-5 users
- [ ] Collect feedback
- [ ] Iterate

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
- Decided: CA-only for MVP (not multi-state)
- Decided: 2-4 week sprint timeline
- Decided: Focus on Tax Partner + Compliance Manager personas
- Decided: Supabase + Next.js stack
- Open: Which LLM (Claude vs GPT)?
- Open: Email provider (Resend vs SendGrid)?

---

**End of research notes - keep updating as you learn!**
