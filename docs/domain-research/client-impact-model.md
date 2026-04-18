# Client Impact Model - Domain Research

**Version:** 1.0  
**Date:** 2026-04-18  
**Status:** Research In Progress  
**Owner:** Product Research Team

---

## Overview

This document defines how client profiles are structured and how regulatory changes are mapped to specific clients. This is the foundation of ReguLens' "Context Catalogue" — the system that determines which clients are affected by which laws.

---

## Research Questions

- [ ] What client attributes are necessary to assess regulatory impact?
- [ ] How granular should activity tracking be?
- [ ] How do tax professionals currently perform client-to-law mapping mentally?
- [ ] What data is privacy-sensitive vs. safe to anonymize/store?
- [ ] How often do client profiles change?
- [ ] What's the acceptable false positive vs. false negative rate for alerts?
- [ ] How do you handle ambiguous cases (client might be affected)?
- [ ] What are the most common impact scenarios?

---

## Client Profile Data Model

### Core Attributes

#### 1. Identity & Classification
```
Client_ID: [Unique identifier, anonymized]
Client_Name: [For internal reference, encrypted]
Entity_Type: [C-Corp | S-Corp | LLC | Partnership | Sole Proprietor | Nonprofit]
Industry_Primary: [NAICS Code + Description]
Industry_Secondary: [If applicable]
Business_Model: [Product | Service | SaaS | Marketplace | Manufacturing | Retail | etc.]
```

**Why These Matter:**
- Entity type determines tax treatment (e.g., S-Corp vs. C-Corp franchise tax)
- Industry determines eligibility for credits (e.g., R&D, film, green energy)
- Business model affects nexus, apportionment, sales tax obligations

**Research Questions:**
- [ ] Is NAICS code granular enough or do we need custom classifications?
- [ ] How do multi-segment businesses get classified?

---

#### 2. Geographic Footprint
```
Headquarters_State: [State code]
Headquarters_City: [City name]
Nexus_States: [Array of states where nexus exists]
  - Physical_Presence: [States with offices/warehouses/employees]
  - Economic_Nexus: [States meeting sales/transaction thresholds]
  - Affiliate_Nexus: [States via related entities]
Remote_Employee_Locations: [Array of states with remote workers]
Sales_Territory: [States where sales occur]
International_Operations: [Y/N, countries if applicable]
```

**Why These Matter:**
- Determines which jurisdictions' regulations apply
- Remote workers can create unexpected nexus (TX guidance example)
- Sales territory affects sales tax obligations

**Research Questions:**
- [ ] How to handle clients with 20+ nexus states? (priority ranking needed?)
- [ ] How frequently does geographic footprint change?
- [ ] What level of detail on remote employees? (count, roles, revenue generated?)

---

#### 3. Financial Profile
```
Annual_Revenue: [Range or exact, for threshold tests]
  - CA_Revenue: [Apportioned]
  - TX_Revenue: [Apportioned]
  - FL_Revenue: [Apportioned]
  - Other_States: [...]
Employee_Count: [Total, FT/PT breakdown]
  - By_State: [For payroll tax, credits]
Gross_Receipts: [For franchise tax calculations]
Taxable_Income: [Estimated, for rate changes]
```

**Why These Matter:**
- Revenue thresholds trigger filing requirements, nexus, tax rates
- Employee count affects credits (hiring, training)
- Different jurisdictions use different metrics (gross receipts vs. net income)

**Research Questions:**
- [ ] How precise do financials need to be? (ranges ok or exact?)
- [ ] How often to update? (annually, quarterly?)
- [ ] Privacy considerations for storing financial data?

---

#### 4. Tax Activity Profile
```
Filing_Status_By_State:
  - CA: [Active filer | Non-filer | Exempt]
  - TX: [Active | No tax obligation | ...]
  - FL: [Active | ...]
Tax_Credits_Used: [Array]
  - R&D_Credit: [Federal, CA, TX, etc.]
  - Film_Production_Credit: [CA]
  - New_Hire_Credit: [...]
Previous_Tax_Positions: [Aggressive | Conservative | Standard]
Audit_History: [Recent audits, outcomes, areas of scrutiny]
Tax_Controversies: [Open issues, appeals]
Special_Elections: [Cost segregation, bonus depreciation, etc.]
```

**Why These Matter:**
- If client uses R&D credit, they care about R&D credit changes
- Audit history indicates areas of risk sensitivity
- Tax positions inform how to frame alerts (opportunities vs. risks)

**Research Questions:**
- [ ] How to track "interest areas" without overwhelming data entry?
- [ ] Should this be explicitly tagged or inferred from past filings?

---

#### 5. Business Activities (Detailed)
```
Revenue_Streams:
  - Product_Sales: [% of revenue]
  - Service_Revenue: [%]
  - Subscription_SaaS: [%]
  - Licensing: [%]
  - Marketplace_Fees: [%]
  
Operations:
  - Manufacturing: [Y/N, location]
  - R&D_Activities: [Y/N, spend amount, CA-based?]
  - Software_Development: [Y/N, AI/ML focus?]
  - Cloud_Infrastructure: [Y/N, AWS/Azure/GCP?]
  - Film_Production: [Y/N, CA-based?]
  
Sales_Channels:
  - Direct_Sales: [Y/N]
  - E-Commerce: [Y/N, platform used]
  - Marketplace_Facilitator: [Amazon/eBay/Etsy/Shopify]
  - Distributor_Network: [Y/N]
  
Workforce:
  - Remote_First: [Y/N]
  - Contractor_Heavy: [% 1099 vs W2]
  - Seasonal_Workforce: [Y/N]
```

**Why These Matter:**
- SaaS revenue has specific apportionment rules
- Marketplace facilitator rules shift sales tax obligations
- R&D activities = R&D credit eligibility
- Remote workforce triggers new nexus considerations

**Research Questions:**
- [ ] How detailed should activity tracking be?
- [ ] What activities are most commonly linked to regulatory changes?
- [ ] Can some of this be inferred from industry code?

---

#### 6. Compliance Posture
```
Risk_Tolerance: [Conservative | Moderate | Aggressive]
Compliance_Priority: [High | Medium | Low]
Response_Time_Expectation: [Immediate | 1-week | 1-month]
Preferred_Communication: [Email | Phone | Dashboard | All]
Decision_Maker: [CFO | Tax Director | Outside CPA | ...]
```

**Why These Matter:**
- Determines alert urgency and framing
- Risk-averse clients want to know about risks; aggressive clients want opportunities
- Response time affects alerting strategy

---

### Example Client Profiles

#### Example 1: Tech Startup (SaaS)
```
Client_ID: TECH_001
Entity_Type: C-Corp
Industry: Software Publishing (NAICS 511210)
Business_Model: SaaS (B2B)

Geographic:
  HQ: San Francisco, CA
  Nexus_States: [CA, TX, NY, WA]
  Remote_Employees: 15 states
  Sales_Territory: All 50 states + international

Financial:
  Annual_Revenue: $12M
  CA_Revenue: $3M (25%)
  TX_Revenue: $2M (16%)
  Employee_Count: 85 (70 remote)

Tax_Activity:
  Filing_Status: CA (Active), TX (Active - economic nexus)
  Credits_Used: [Federal R&D, CA R&D]
  
Activities:
  R&D: Y (AI/ML development, $3M annual spend)
  Software_Dev: Y (100% of operations)
  Cloud_Infrastructure: Y (AWS)
  Sales_Channel: Direct + Marketplace (AWS Marketplace)

Compliance_Posture:
  Risk_Tolerance: Moderate
  Priority: High
```

**Regulatory Impact Scenarios:**

1. **CA R&D Credit Expansion for AI/ML**
   - **Match:** Industry=Software ✅, CA nexus ✅, R&D activities ✅, AI/ML ✅, Uses R&D credit ✅
   - **Impact:** HIGH - Likely increased credit eligibility
   - **Alert:** "New CA R&D credit expansion applies to your AI development activities"

2. **TX Remote Worker Nexus Guidance**
   - **Match:** Has TX remote employees ✅, Currently filing TX ✅
   - **Impact:** MEDIUM - May affect apportionment
   - **Alert:** "TX clarifies remote worker nexus rules affecting your workforce"

3. **FL Marketplace Facilitator Rule Change**
   - **Match:** Sells on AWS Marketplace ✅, Has FL sales ✅
   - **Impact:** LOW-MEDIUM - Check if AWS remits on their behalf
   - **Alert:** "FL updates marketplace facilitator rules - verify AWS compliance"

---

#### Example 2: Manufacturing Company
```
Client_ID: MFG_001
Entity_Type: C-Corp
Industry: Automotive Parts Manufacturing (NAICS 3363)
Business_Model: Product manufacturing + distribution

Geographic:
  HQ: Austin, TX
  Nexus_States: [TX, CA, FL, MI, OH]
  Manufacturing_Facilities: [TX, MI]
  Warehouses: [CA, FL, OH]
  Sales_Territory: US + Canada/Mexico

Financial:
  Annual_Revenue: $150M
  TX_Revenue: $45M (30%)
  Employee_Count: 450

Tax_Activity:
  Filing_Status: TX (Active), CA (Active), FL (Active)
  Credits_Used: [Federal R&D, TX franchise tax deductions]
  
Activities:
  Manufacturing: Y (automotive parts)
  R&D: Y (product development, $5M spend)
  Distribution: Y (multi-state warehouses)
  Export: Y (NAFTA partners)

Compliance_Posture:
  Risk_Tolerance: Conservative
  Priority: High
```

**Regulatory Impact Scenarios:**

1. **TX Franchise Tax Rate Change**
   - **Match:** TX nexus ✅, Significant TX revenue ✅
   - **Impact:** HIGH - Direct tax liability impact
   - **Alert:** "TX franchise tax rate increase affects your $45M TX revenue"

2. **CA Manufacturing Equipment Exemption**
   - **Match:** Has CA warehouse ✅, Manufacturing ❌ (not in CA)
   - **Impact:** LOW - Warehouse doesn't qualify
   - **Alert:** [Filtered out - not relevant]

3. **Multi-State Apportionment Rule Changes**
   - **Match:** Multi-state operations ✅, High revenue ✅
   - **Impact:** MEDIUM-HIGH - Could affect state tax allocation
   - **Alert:** "New multi-state apportionment rules may affect your 5-state footprint"

---

#### Example 3: Professional Services Firm
```
Client_ID: PROF_001
Entity_Type: Partnership
Industry: Accounting Services (NAICS 541211)
Business_Model: Professional services

Geographic:
  HQ: Miami, FL
  Nexus_States: [FL, NY, TX]
  Remote_Employees: 25% of workforce
  Sales_Territory: National

Financial:
  Annual_Revenue: $8M
  Employee_Count: 60
  
Tax_Activity:
  Filing_Status: FL (Active), Partnership returns
  Credits_Used: None
  
Activities:
  Service_Revenue: 100%
  Remote_Workforce: Y (post-COVID shift)

Compliance_Posture:
  Risk_Tolerance: Conservative (accounting firm)
  Priority: High
```

**Regulatory Impact Scenarios:**

1. **FL Corporate Income Tax Rate Change**
   - **Match:** FL nexus ✅, Entity type = Partnership ❌
   - **Impact:** NONE - Partnerships not subject to corporate tax
   - **Alert:** [Filtered out - not applicable to entity type]

2. **Remote Worker Withholding Rules**
   - **Match:** Has remote employees ✅, Multi-state ✅
   - **Impact:** HIGH - Payroll tax compliance
   - **Alert:** "New multi-state withholding guidance for remote employees"

---

## Impact Mapping Logic

### Matching Rules Framework

**Rule Structure:**
```
IF [Client Attribute Conditions]
  AND [Regulatory Change Attributes]
  THEN [Impact Level] + [Alert Action]
```

### Example Rules

#### Rule 1: R&D Credit Changes
```
IF Client.Tax_Credits_Used contains "R&D Credit"
  AND Client.Nexus_States contains Regulation.Jurisdiction
  AND Client.R&D_Activities = TRUE
  AND Client.Revenue > Regulation.Threshold
THEN Impact = HIGH
  Alert = "New R&D credit expansion may increase your benefit"
```

#### Rule 2: Sales Tax Nexus Changes
```
IF Client.Sales_Territory contains Regulation.Jurisdiction
  AND Client.Revenue_In_State > Regulation.Economic_Nexus_Threshold
  AND Client.Filing_Status != "Active" in that state
THEN Impact = HIGH
  Alert = "New economic nexus threshold creates filing obligation"
```

#### Rule 3: Entity-Specific Changes
```
IF Regulation.Entity_Type_Affected = Client.Entity_Type
  AND Client.Nexus_States contains Regulation.Jurisdiction
THEN Impact = MEDIUM-HIGH
  Alert = "New rule affects [Entity Type] in [State]"
```

### Impact Scoring

**Impact Levels:**
- **CRITICAL:** Immediate compliance obligation, deadline, or high-dollar opportunity
- **HIGH:** Significant financial impact or risk (>$50K or >5% tax change)
- **MEDIUM:** Moderate impact, may require planning or review
- **LOW:** Informational, affects edge cases or future years
- **NONE:** No impact (filtered out)

**Factors in Scoring:**
- Financial magnitude ($ impact)
- Compliance urgency (deadline proximity)
- Risk level (penalty exposure)
- Opportunity value (tax savings potential)
- Client priority level

---

## Privacy & Data Handling

### Sensitivity Levels

**High Sensitivity (Encrypt/Anonymize):**
- Client name
- Exact financial figures
- Specific client identities
- Proprietary business strategies

**Medium Sensitivity (Protected):**
- Revenue ranges
- General activities
- Geographic footprint
- Tax positions

**Low Sensitivity (Safe for Analysis):**
- Industry codes
- Entity types
- General activity categories
- State presence (binary Y/N)

### Anonymization Strategy

**Option 1: Client ID Hashing**
- Replace client names with hashed IDs
- Firm maintains mapping (not stored in ReguLens)
- ReguLens only sees: `CLIENT_A3F9D2` with attributes

**Option 2: Profile Templating**
- Store generalized profiles, not specific clients
- Example: "SaaS company, $10-20M, CA/TX nexus, uses R&D credits"
- Firm maps their clients to profile templates

**Question for Research:**
- [ ] How do tax firms currently protect client data in their systems?
- [ ] What's acceptable for cloud-based AI analysis?
- [ ] Can we use differential privacy or federated learning?

---

## Data Collection & Maintenance

### Initial Profile Creation

**Data Sources:**
- Client intake forms
- Tax return data (prior years)
- Engagement letters
- Financial statements
- Direct client interviews

**Question:**
- [ ] How much of this can be auto-populated from existing tax software?
- [ ] What integrations exist (QuickBooks, Thomson Reuters, CCH)?

### Profile Updates

**Triggers for Update:**
- Annual tax filing (refresh financials)
- Geographic expansion (new nexus)
- Business model changes (new revenue streams)
- Significant events (M&A, new funding)

**Frequency:**
- Minimum: Annually
- Ideal: Quarterly or event-driven
- Critical attributes (nexus, revenue): Real-time updates

---

## Expert Interview Questions

### For Tax Partners/Directors:

1. **Mental Model:**
   - "When you hear about a new CA tax law, how do you decide which clients it affects?"
   - "What's your mental checklist of client attributes you consider?"

2. **Data Availability:**
   - "What client data do you have readily available vs. hard to access?"
   - "Which attributes change most frequently?"

3. **False Positives vs. Negatives:**
   - "Would you rather get 10 alerts where 8 are relevant, or miss 2 relevant ones?"
   - "How do you currently handle uncertainty (client might be affected)?"

4. **Privacy:**
   - "What client data are you comfortable storing in a cloud AI system?"
   - "How do you currently protect client confidentiality in your systems?"

5. **Real Examples:**
   - "Tell me about a time you discovered a client should have been alerted about a law change but wasn't."
   - "What made that situation painful or costly?"

---

## Next Steps

- [ ] Interview 3-5 tax professionals about their client profiling approach
- [ ] Analyze 20 real regulatory changes and manually map to sample client profiles
- [ ] Define minimum viable client profile (MVP attributes)
- [ ] Create privacy/security framework for client data handling
- [ ] Test matching logic with real scenarios (precision/recall testing)
- [ ] Determine data freshness requirements
- [ ] Research integration opportunities with existing tax software

---

## Appendix: Sample Client Profile Template (For Interviews)

Use this template during expert interviews to validate attributes:

```
CLIENT PROFILE WORKSHEET

Basic Info:
- Entity Type: ___________
- Industry (NAICS): ___________
- Business Model: ___________

Geographic:
- HQ State/City: ___________
- States with physical presence: ___________
- States with economic nexus only: ___________
- Remote employee states: ___________

Financial (ranges OK):
- Annual revenue: $___________
- Employees: ___________

Tax Activity:
- States where filing: ___________
- Tax credits used: ___________

Key Activities:
- [ ] Manufacturing
- [ ] R&D / Product development
- [ ] Software / SaaS
- [ ] E-commerce
- [ ] Marketplace seller
- [ ] Remote workforce
- [ ] International operations
- Other: ___________

Compliance:
- Risk tolerance: Conservative / Moderate / Aggressive
- Priority level: High / Medium / Low
```

**During interview:** Ask expert to fill this out for 2-3 real clients (anonymized), then walk through recent regulatory changes and discuss which would have triggered alerts.

---

**Document Status:** Template created, research in progress  
**Last Updated:** 2026-04-18  
**Next Review:** After initial expert interviews complete
