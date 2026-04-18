# MVP Requirements

**Version:** 1.0  
**Date:** 2026-04-18  
**Status:** Draft - Pending Research Completion  
**Owner:** Product Team

---

## Overview

This document defines the Minimum Viable Product (MVP) scope for ReguLens. The MVP is the smallest set of features that delivers core value to early adopters and enables learning.

**MVP Goal:** Prove that AI-powered, automated regulatory monitoring can eliminate the "manual discovery gap" for a single jurisdiction.

---

## MVP Scope Decision (Pending Research)

**After completing domain and user research, decide:**

### Option A: Single Jurisdiction MVP (Recommended)
- Focus on California only (largest market, most complex)
- Monitor CA FTB + CDTFA + CA Legislature
- Perfect the experience before expanding

**Pros:**
- Faster to market
- Easier to perfect monitoring logic
- Lower technical complexity
- Can iterate based on feedback

**Cons:**
- Limited addressable market
- Multi-state firms may not buy

---

### Option B: Multi-Jurisdiction MVP
- Cover CA, TX, FL from day one
- Full multi-state value proposition

**Pros:**
- Bigger market appeal
- True differentiation

**Cons:**
- 3x the effort
- Harder to perfect
- Longer time to launch

---

**Decision:** [To be made after research]

---

## MVP Feature Set (MoSCoW Method)

### MUST HAVE (Core MVP)

These features are non-negotiable for MVP launch.

#### 1. Automated Source Monitoring
**User Story:** As a tax partner, I want ReguLens to automatically monitor regulatory sources 24/7 so I don't have to manually check websites.

**Acceptance Criteria:**
- [ ] System monitors top 5 CA sources daily (FTB, CDTFA, Legislature, etc.)
- [ ] New publications detected within 24 hours of posting
- [ ] Publications stored and accessible in system

**Why Must-Have:** Core value proposition

---

#### 2. Client Profile Management
**User Story:** As a tax partner, I want to create and manage client profiles so ReguLens knows which regulations affect which clients.

**Acceptance Criteria:**
- [ ] Create client profile with key attributes (entity type, industry, nexus states, activities)
- [ ] Edit and update client profiles
- [ ] View list of all my client profiles
- [ ] Import profiles via CSV (for bulk setup)

**Why Must-Have:** Necessary for client matching

---

#### 3. AI-Powered Impact Analysis
**User Story:** As a tax partner, I want ReguLens to automatically identify which of my clients are affected by new regulations so I don't have to manually cross-reference.

**Acceptance Criteria:**
- [ ] System analyzes new publications for tax implications
- [ ] Matches publications to client profiles based on attributes
- [ ] Assigns impact score (High/Medium/Low)
- [ ] Shows reasoning: "Affects Client A because: CA nexus + uses R&D credit"

**Why Must-Have:** Key differentiation vs. manual monitoring

---

#### 4. Proactive Alerts
**User Story:** As a tax partner, I want to receive email alerts when a regulation affects my clients so I can act quickly.

**Acceptance Criteria:**
- [ ] Email alert sent within 24 hours of detection
- [ ] Alert includes: regulation summary, affected clients, impact level, action items
- [ ] Alert links to detailed analysis in web app
- [ ] User can configure alert frequency (immediate, daily digest, weekly)

**Why Must-Have:** Proactive value delivery

---

#### 5. Web Dashboard
**User Story:** As a tax partner, I want a web dashboard to view all alerts, client profiles, and regulatory updates in one place.

**Acceptance Criteria:**
- [ ] Login with email/password
- [ ] Dashboard shows: recent alerts, client count, sources monitored
- [ ] View all alerts (filterable by date, client, impact level)
- [ ] View alert details (regulation text, summary, affected clients, actions)
- [ ] Mark alerts as "reviewed" or "actioned"

**Why Must-Have:** Central hub for user interaction

---

#### 6. Audit Trail
**User Story:** As a compliance manager, I want a complete audit trail showing when regulations were detected and analyzed so I can prove we didn't miss anything.

**Acceptance Criteria:**
- [ ] Every alert shows: detected date, analyzed date, alerted date
- [ ] History of all publications monitored (not just alerted ones)
- [ ] Exportable report for auditors

**Why Must-Have:** Compliance and trust requirement

---

### SHOULD HAVE (Important but not MVP-blocking)

These features add significant value but can be deferred to post-MVP if needed.

#### 7. Mobile App (Notifications)
- Push notifications on mobile
- Quick view of alerts
- Mark as reviewed on mobile

**Why Should-Have:** Busy partners need on-the-go access

**Can defer if:** Email alerts + mobile-responsive web app sufficient for MVP

---

#### 8. Advanced Filters and Search
- Search alerts by keyword, client, date range
- Filter by jurisdiction, topic, impact level
- Saved searches

**Why Should-Have:** Usability for large alert volumes

**Can defer if:** MVP has limited alerts (single jurisdiction)

---

#### 9. Team Collaboration
- Assign alerts to team members
- Comment on alerts
- @mention colleagues

**Why Should-Have:** Firms have multiple stakeholders

**Can defer if:** MVP targets solo partners or small firms

---

### COULD HAVE (Nice-to-have)

These features are valuable but low priority for MVP.

#### 10. AI Chat Interface
- Ask questions like "Which clients are affected by CA R&D credit changes?"
- Conversational interface for exploring regulations

**Why Could-Have:** Cool but not essential, adds complexity

---

#### 11. Custom Client Tags
- Tag clients with custom labels (e.g., "High Risk", "Opportunity Focus")
- Filter alerts by tags

**Why Could-Have:** Advanced organization, not needed initially

---

#### 12. Integration with Tax Software
- Sync client data from UltraTax, CCH Axcess, etc.
- Push alerts to tax software workflow

**Why Could-Have:** Partnership deals take time, manual CSV import works for MVP

---

### WON'T HAVE (Out of Scope for MVP)

These features are explicitly excluded from MVP to maintain focus.

#### Multi-Jurisdiction (If Option A chosen)
- Texas, Florida monitoring
- Multi-state apportionment analysis

**Why Won't-Have:** Focus on perfecting single jurisdiction first

---

#### White-Label / Multi-Tenant SaaS
- Firm branding
- Client portal for end clients
- Sub-user management

**Why Won't-Have:** MVP targets direct use by tax professionals, not end clients

---

#### Advanced Analytics
- Trends over time
- Predictive analytics
- Benchmarking

**Why Won't-Have:** Needs data history, not day-one feature

---

#### API Access
- RESTful API for integrations
- Webhooks

**Why Won't-Have:** Adds complexity, no demand validated yet

---

## MVP User Journey

**Primary Persona:** Sarah Chen (Tax Partner)

**Onboarding:**
1. Sign up for ReguLens (email + password)
2. Import 20 client profiles via CSV
3. Review profile setup and make edits
4. Configure alert preferences (email, daily digest)

**Daily Use:**
5. Receive email: "ReguLens Alert: CA R&D Credit Expansion affects 3 clients"
6. Click link, opens web dashboard
7. Review summary and affected clients
8. Mark as "reviewed" and assign follow-up task (outside ReguLens for MVP)

**Weekly Use:**
9. Log into dashboard to review all alerts from past week
10. Export audit report for internal records

---

## Success Metrics (MVP)

**Product Metrics:**
- Time from publication to alert: <24 hours
- Alert precision: >75% of alerts are actionable
- Alert recall: >90% of relevant publications detected

**User Metrics:**
- Time saved per week: >5 hours per user
- User retention: >80% active after 30 days
- NPS (Net Promoter Score): >50

**Business Metrics:**
- 10 paying customers within 3 months of launch
- Conversion rate (trial to paid): >30%
- Churn rate: <10% monthly

---

## MVP Technical Architecture (High-Level)

**[To be detailed in technical design docs]**

**Components:**
1. **Source Monitors** - Crawlers for CA FTB, CDTFA, Legislature
2. **AI Analysis Engine** - LLM-based impact analysis
3. **Matching Engine** - Client profile to regulation matching
4. **Alert Service** - Email notifications
5. **Web App** - React/Next.js dashboard
6. **Database** - PostgreSQL (Supabase) for profiles and alerts
7. **Auth** - Supabase Auth

---

## MVP Development Phases

### Phase 1: Core Monitoring (Weeks 1-3)
- Build source monitors for top 5 CA sources
- Store publications in database
- Manual review of detections (validate accuracy)

### Phase 2: AI Analysis (Weeks 4-6)
- Integrate LLM for publication summarization
- Build impact scoring logic
- Test on 50 historical publications

### Phase 3: Client Matching (Weeks 7-9)
- Build client profile CRUD
- Build matching algorithm
- Test matching accuracy

### Phase 4: Alerts & Dashboard (Weeks 10-12)
- Email alert system
- Web dashboard (login, view alerts, manage profiles)
- Audit trail

### Phase 5: Testing & Launch (Weeks 13-14)
- Beta testing with 5 users
- Bug fixes and refinements
- Public launch

**Total MVP Timeline:** ~14 weeks (3.5 months)

---

## Post-MVP Roadmap (V2 Features)

After MVP validation and initial traction:

**V2 (Months 4-6):**
- Multi-jurisdiction (TX, FL)
- Mobile app
- Team collaboration features

**V3 (Months 7-9):**
- Integration with tax software
- Advanced analytics
- API access

---

## Open Questions (To Be Resolved)

- [ ] Single jurisdiction vs. multi-jurisdiction for MVP?
- [ ] What's the minimum number of CA sources to monitor?
- [ ] What LLM to use for analysis? (OpenAI, Claude, custom fine-tuned?)
- [ ] How to handle ambiguous cases where impact is unclear?
- [ ] Mobile app in MVP or post-MVP?
- [ ] Pricing model: per user, per firm, per client profile?

---

## Next Steps

1. **Complete research** (domain, user, competitive)
2. **Validate feature priorities** with user interviews
3. **Finalize MVP scope** (single vs. multi-jurisdiction)
4. **Create detailed user stories** for each feature
5. **Technical design** (architecture, tech stack decisions)
6. **Development kickoff**

---

**Document Owner:** Product Team  
**Status:** Draft - pending research completion  
**Next Review:** After user interviews complete
