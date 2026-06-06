# Feature Spec: Tax Calculator

## Purchase Tax (מס רכישה) \+ Capital Gains Tax (מס שבח)

**Document version:** 1.2 **Phase:** 1 (Pre-Signing) **Status:** Ready for development **Estimated effort:** 1.5 sprints (3 weeks)

**Changelog v1.2:**

- **Added Section 1.5: Brand Transparency Principle** — a foundational requirement that affects every UI decision in this feature. The lawyer's brand depends on being able to show clients exactly how every number was derived. No miss-information, no shortcuts, no "trust us" — every result must be traceable to its source.  
- Changed Section 11.4 (Linear vs Real): Reverted to "use the simulator's default" (the system does not pick between methods — the official simulator decides)  
- Added Section 7.4: Client-Facing Transparency View — what the lawyer can show his client  
- Added Section 8.3: Provenance Requirements — every stored result must include traceable source data  
- Updated Section 10 (Risks): added "lawyer's brand exposure" as a critical risk category

**Changelog v1.1:**

- Resolved 6 open questions with product decisions (see Section 11\)  
- Added "Backoffice Configuration" requirements throughout (any value that may change is now configurable, not hardcoded)  
- Added Tax Authority login session persistence (decision: keep session warm for the work day)  
- Removed multiple-buyers complexity from scope (deferred to Phase 2\)  
- Removed improving-housing refund tracking from scope (deferred until lawyer requests it)

---

## 0\. Critical Reading Order

Before implementing this feature, the developer must:

1. Read the main `PRD_Phase1_Pre-Signing.md` first, especially:  
     
   - Section 0 (Language & Localization) — all UI in Hebrew RTL  
   - Section 0.5 (Production Environment) — Israeli IP required for scraping  
   - Section 5, Step 3 (Document Package Preparation) — tax calculation is part of this step

   

2. Read this document in full before writing any code  
     
3. The reference implementation `purchase_tax.py` (in the repo) is **deprecated** — it contained hardcoded tax brackets. This spec replaces it with a live-scraping approach.

---

## 1\. Why This Feature

### The Problem

Every residential real estate transaction in Israel involves two potential tax events:

- **Buyer** pays **Mas Rechisha (Purchase Tax)** based on property value and buyer classification  
- **Seller** may pay **Mas Shevach (Capital Gains Tax)** on the profit from the sale

Today Ron calculates these manually:

- He visits the Tax Authority's simulator  
- He fills in 10-20 fields per case  
- He copies the result into the case file  
- He repeats for both buyer and seller perspectives  
- Time per case: 15-30 minutes  
- Risk: errors when bracket updates occur, errors when typing the wrong figures

### The Solution

A unified Tax Calculator module that:

- Takes structured inputs from the Smart Intake Form  
- Automatically opens the relevant Israeli Tax Authority simulator  
- Fills in all fields  
- Reads back the result  
- Stores the calculation in the case record with a screenshot and timestamp for audit  
- Flags edge cases that require Ron's manual judgment

### Strategic Choice: Live Scraping Over Hardcoded Brackets

**Why we do NOT hardcode tax brackets in our code:**

- Brackets change at least annually (16.1 of each year)  
- Brackets can change mid-year by legislation (e.g., 2025 freeze until 2028\)  
- Hardcoded brackets mean we need to ship a new version every time the law changes  
- A bug in our bracket data could mean wrong tax advice to clients — legal exposure

**Why we use the Tax Authority's live simulator:**

- It's always up-to-date by definition  
- Government-validated calculation  
- No legal exposure for us — we just relay what the official calculator says  
- Trade-off: slower (10-30 seconds per calculation) and depends on the simulator being available

This is the strategic decision: **truth \> speed**. If we need a faster path, we can add caching later.

---

## 1.5. ⚠️ Foundational Principle: Brand Transparency

**This section is non-negotiable. Every UI decision, every code path, every data structure in this feature must respect this principle.**

### The Principle

**The lawyer's professional brand depends on being able to show clients exactly how every number was derived. There is no acceptable "miss-information" — every result must be traceable to an authoritative source the client can verify themselves.**

### Why This Matters

Ron and Lev are practicing real estate lawyers. Their clients trust them with transactions worth hundreds of thousands to millions of shekels. When a client asks "where does this ₪38,420 tax figure come from?", the lawyer must be able to answer with absolute confidence and provide proof.

If the system ever produces a number that the lawyer can't fully explain or that turns out to be wrong, it doesn't just hurt the client — it damages the firm's reputation in a market that runs on referrals and trust. This is an existential brand risk, not a technical concern.

### What This Means for Implementation

**1\. No silent calculations.** The system never produces a number "out of thin air." Every calculation must include:

- The exact source (e.g., "Israeli Tax Authority simulator, June 7, 2026 at 14:32")  
- The exact inputs that were submitted  
- A screenshot of the result page from the source  
- A timestamp  
- A unique identifier the lawyer can use to retrieve the proof later

**2\. No client-invisible optimizations.** If the system did anything that affected the result, the lawyer must be able to show the client what it did. Examples:

- "We ran the calculation for single-residence rate because you confirmed in the intake form that this is your only property"  
- "The simulator was queried at this date and time and returned these exact brackets"  
- We do NOT silently choose between calculation methods (e.g., linear vs real) — the simulator's default is used and the choice is visible

**3\. Always-on audit trail in the UI.** Every result card in the lawyer's view must include:

- "View source" button → opens the saved screenshot of the official simulator  
- "View inputs" button → shows what was submitted to the simulator  
- Timestamp of when the calculation was performed  
- Version number of the calculator logic  
- A unique calculation ID that can be referenced in client communications

**4\. Client-facing transparency view.** The lawyer must be able to generate a client-facing report (PDF or shareable link) that includes:

- All inputs that were submitted (client can verify they are correct)  
- The official simulator screenshot (client sees this is government data, not ours)  
- The result and how it was derived  
- The legal basis with section references where applicable  
- Generated date and case ID

**5\. No "cleverness" that the lawyer can't explain.** If a developer wants to add a feature like "automatically choose the cheaper calculation method," they must first ensure the lawyer can defend that choice to a client. The default answer is: don't — use the official simulator's default behavior.

**6\. Error visibility, not error hiding.** When the system fails (simulator down, network error, parsing failure), the lawyer sees a clear error message — never a fallback calculation that might be wrong. Better to say "calculation unavailable, please try again" than to show a number that wasn't validated.

**7\. Documented uncertainty.** Where the system is uncertain (e.g., "this might be eligible for an exemption but the rules are complex"), the UI must say so explicitly with a clear recommendation to verify manually.

### What This Rules Out

- ❌ Caching tax results "to save time" — the client needs to see a fresh calculation  
- ❌ Running our own tax math in parallel and showing whichever matches — we use the official source exclusively  
- ❌ "Smart" features that pre-select options for the client without their knowledge  
- ❌ Estimates or approximations presented as final figures  
- ❌ Any "trust the system" UI without showing the underlying proof  
- ❌ Hiding the source of a number behind UI complexity

### Test for Every Feature

Before any feature ships, the developer must ask:

"If Ron's client asked him to explain exactly how this number was derived, could Ron pull up our system, show the audit trail, and prove the result against the official government source — in under 30 seconds?"

If the answer is no, the feature is not ready.

---

## 2\. Two Sub-Features

### 2.1 Purchase Tax (מס רכישה) — `purchase_tax`

**Simulator:** `https://www.misim.gov.il/svsimurechisha/startPage.aspx` **Authentication required:** No — anonymous, public access **Typical run time:** 5-15 seconds end-to-end **Cost per calculation:** Zero **Source of truth:** The official government simulator **Buyer pays:** Yes, always (if value \> 0 for additional residence; or value \> threshold for single residence)

### 2.2 Capital Gains Tax (מס שבח) — `capital_gains_tax`

**Two-stage approach:**

**Stage A: Exemption Check** (\~80% of cases end here)

- Determine if the seller qualifies for an exemption based on intake form answers  
- If yes, no calculation is needed — output "פטור" (Exempt) with the relevant law section  
- No external service needed

**Stage B: Live Calculation** (\~20% of cases)

- Only invoked when no exemption applies  
- Opens the official **שומה עצמית** (Self-Assessment) simulator  
- Requires Ron's smart card (Comsign) for authentication  
- This is a higher-friction flow — but the volume is low

**Simulator:** `https://www.misim.gov.il/svtsvazmitnew/FrmHadrachaRashit.aspx` **Authentication required:** Yes — smart card or username/password **Typical run time:** 30-60 seconds end-to-end (includes Ron's authentication) **Cost per calculation:** Zero **Source of truth:** The official government simulator **Seller pays:** Only if there's a taxable profit and no exemption applies

---

## 3\. Detailed Spec: Purchase Tax

### 3.1 Inputs

These come from the Smart Intake Form (Step 2 in main PRD) and the case record:

PurchaseTaxInput {

  property\_value: number          // ILS \- the agreed purchase price

  buyer\_type: BuyerType           // see enum below

  is\_israeli\_resident: boolean    // critical — non-residents pay more

  has\_disability: boolean         // 19%+ disability has reduced rates

  has\_inheritance\_property: boolean  // doesn't disqualify single-residence if ≤ 50% share

  property\_share\_being\_purchased: number  // typically 1.0; can be 0.5 for partial purchases

  transaction\_date: Date          // bracket selection depends on the date

  is\_new\_construction: boolean    // new construction has slightly different timing rules

  oleh\_immigration\_date?: Date    // required if buyer\_type \= NEW\_IMMIGRANT

}

enum BuyerType {

  SINGLE\_RESIDENCE        // דירת מגורים יחידה \- Israeli resident, no other property

  ADDITIONAL\_RESIDENCE    // דירה נוספת / השקעה \- additional property

  IMPROVING\_HOUSING       // משפר דיור \- replacing current single residence within 18 months

  NEW\_IMMIGRANT          // עולה חדש \- within 1 year before to 7 years after aliyah

  FOREIGN\_RESIDENT       // תושב חוץ

  DISABLED               // נכה \- has special reduced brackets

  // Note: COMBINED\_BUYERS (multiple buyers with different statuses) is deferred to Phase 2\.

  // For MVP, the lawyer selects ONE classification per case.

}

### 3.2 Process Flow

1\. User initiates purchase tax calculation from case detail view

2\. System loads inputs from intake form

3\. System validates inputs

4\. Open Playwright headless browser pointing to Israeli IP

5\. Navigate to https://www.misim.gov.il/svsimurechisha/startPage.aspx

6\. Click through to the actual calculator form

7\. Fill in fields based on buyer\_type and inputs

8\. Submit form

9\. Wait for results page to render

10\. Take screenshot for audit trail

11\. Parse the resulting tax amount and breakdown

12\. Store in case record

13\. Display unified summary to lawyer

### 3.3 Output Structure

PurchaseTaxResult {

  total\_tax\_ils: number                    // final amount in ILS

  effective\_rate\_percent: number           // total\_tax / property\_value

  breakdown: Array\<{                       // bracket-by-bracket

    from\_amount: number

    to\_amount: number

    rate\_percent: number

    amount\_in\_this\_bracket: number

    tax\_from\_this\_bracket: number

  }\>

  warnings: string\[\]                       // e.g. "Confirm immigration date for oleh status"

  notes: string\[\]                          // e.g. "Improving housing \- file refund claim within 18 months"

  source: 'live\_scrape'                    // never anything else

  scraped\_at: Date

  screenshot\_url: string                   // R2 URL to the proof screenshot

  simulator\_html\_snapshot?: string         // HTML at time of scraping (for debugging)

}

### 3.4 Edge Cases the Code Must Handle

1. **Improving housing refund**  
     
   - Buyer pays full additional-residence rate now  
   - Gets refund if previous residence is sold within 18 months  
   - Output should flag: "Refund opportunity — track sale of previous property"  
   - Note: Active tracking deferred to Phase 2 (see Section 11\)

   

2. **Inheritance carve-out**  
     
   - Buyer inherited ≤50% of another property \= still qualifies as single residence  
   - Must be modeled in the input form

   

3. **Disability discount stacking**  
     
   - Disabled buyer with single residence gets EVEN BETTER rate  
   - Up to 2 transactions per lifetime for this benefit

   

4. **Property under construction**  
     
   - Tax brackets are determined by the **contract signing date**, not handover date  
   - Important when transitioning between bracket update periods

### 3.5 Failure Modes

| Failure | Detection | Response |
| :---- | :---- | :---- |
| Simulator site is down | HTTP timeout / 5xx | Retry 3x with exponential backoff. If still failing, raise alert and prompt lawyer to retry later. Do not provide a fallback calculation. |
| Simulator HTML structure changed | Selector not found | Log to Sentry with high priority. Lawyer sees: "המערכת זיהתה שינוי בסימולטור — נדרשת בדיקת מפתח". Halt the calculation. |
| Browser crash | Playwright exception | Restart browser, retry once, then escalate |
| Result parsing failure | Regex doesn't match | Store the screenshot for manual review; lawyer enters result manually as fallback |
| Network blocked (non-Israeli IP) | Specific error pattern | Show clear error: "Backend must run from Israeli IP. Check Kamatera connection." |

---

## 4\. Detailed Spec: Capital Gains Tax (Two-Stage)

### 4.1 Stage A — Exemption Check

This stage runs WITHOUT any external service. It's pure business logic.

**Inputs from intake form:**

CapitalGainsExemptionInput {

  // Property history

  purchase\_date: Date            // when seller acquired this property

  purchase\_price: number         // historical purchase price

  sale\_price: number             // current sale price

  // Seller status

  seller\_owns\_other\_property: boolean

  seller\_owns\_other\_property\_share\_percent: number  // 0-100; ≤33% may still qualify for single

  is\_inherited\_property: boolean

  inheritance\_date?: Date

  deceased\_was\_single\_property\_eligible?: boolean

  // Recent transactions

  sold\_other\_property\_with\_exemption\_in\_last\_18\_months: boolean

  date\_of\_previous\_exempt\_sale?: Date

  // Special cases

  is\_gift\_from\_relative: boolean

  gift\_date?: Date

  is\_urban\_renewal: boolean        // התחדשות עירונית

  urban\_renewal\_type?: 'tama\_38\_1' | 'tama\_38\_2' | 'pinui\_binui'

}

**Decision tree** (run in order; first matching rule wins):

1\. If sale\_price \< purchase\_price (loss): → NO TAX, log "אין שבח"

2\. If is\_urban\_renewal: → CHECK SPECIFIC EXEMPTION

   \- TAMA 38/1 (חיזוק): Often fully exempt

   \- TAMA 38/2 (פינוי-בינוי): Fully exempt under section 49(כב)

   \- PINUI\_BINUI: Fully exempt under section 49(כב)

   → Output: EXEMPT with section reference

3\. If seller\_owns\_other\_property and other share \> 33%:

   → NOT eligible for single-residence exemption

   → Skip to Stage B (calculation)

4\. If is\_inherited\_property:

   \- If deceased was eligible for single-residence exemption at time of death:

     → Seller inherits the exemption status (section 49ב(5))

     → Output: EXEMPT

   \- Else: Skip to Stage B

5\. If sold\_other\_property\_with\_exemption\_in\_last\_18\_months and not improving housing:

   → NOT eligible for second exemption

   → Skip to Stage B

6\. If property is the seller's single residence in Israel:

   \- Default rule (section 49ב(2)): EXEMPT up to luxury cap (\~₪4.6M, 2026 — verify live)

   \- If sale\_price exceeds the luxury cap:

     → Partial exemption — Skip to Stage B for proportional calculation

7\. Default: → Skip to Stage B (no exemption found)

**Output of Stage A:**

ExemptionCheckResult {

  is\_exempt: boolean

  exemption\_section?: string       // e.g., "49ב(2)", "49(כב)"

  exemption\_reason?: string        // human-readable Hebrew explanation

  partial\_exemption?: {            // for above-luxury-cap cases

    exempt\_portion: number

    taxable\_portion: number

  }

  requires\_stage\_b: boolean        // true if Stage B should run

  warnings: string\[\]

  notes: string\[\]

}

### 4.2 Stage B — Live Calculation

**Only runs if Stage A returns `requires_stage_b: true`.**

**Authentication challenge:**

The simulator at `misim.gov.il/svtsvazmitnew` requires authentication via:

- Smart card (Comsign) — Ron has one  
- OR username/password — Ron has this for the Tax Authority

**Session persistence (decided per Section 11.3):**

The system keeps Ron's Tax Authority authentication alive for the entire work day:

- When Ron first runs a capital gains calculation, the system opens a browser, prompts Ron to authenticate, and stores the authenticated session  
- Subsequent calculations during the same work day reuse the session — Ron doesn't re-authenticate  
- The session is held in a persistent Playwright browser context on the backend  
- Session auto-expires after 30 minutes of inactivity (Tax Authority's policy)  
- When expired, Ron is prompted to re-authenticate on the next calculation  
- At end of day or on explicit logout, the session is cleared

**Dual calculation strategy:**

Per Section 11.4, the system does NOT run multiple calculation methods. It runs ONE calculation using the simulator's default behavior. The simulator chooses linear or real automatically based on the property's purchase date and other factors — whatever the simulator decides is what we report.

The screenshot shows clearly which method was applied. If the lawyer wants to compare methods manually, they can use the manual override flow.

**MVP approach:**

1. The system prepares all the data to be entered  
2. Check if there's an active authenticated session in the backend  
3. If no active session: opens a **visible** browser window on Ron's machine and prompts for authentication  
4. If active session: reuses it silently  
5. Ron physically inserts his smart card OR types his credentials (only if needed)  
6. The system continues automatically once logged in (or immediately if session was already active)  
7. The system fills in all the form fields using simulator defaults  
8. Submits and reads the result  
9. Stores the result \+ screenshot  
10. Returns the official result

This is the same Strategy A pattern as Taboo extracts: **system does the heavy lifting, human authorizes once**.

**Inputs to the simulator (collected from intake \+ property history):**

CapitalGainsCalculationInput {

  // Basic

  property\_address: string

  block: string

  parcel: string

  sub\_parcel?: string

  // Sale

  sale\_date: Date

  sale\_price: number

  // Purchase

  purchase\_date: Date

  purchase\_price: number

  purchase\_tax\_paid: number       // can be deducted

  // Improvements (each entry deductible)

  improvements: Array\<{

    description: string

    date: Date

    amount: number

    has\_receipt: boolean

  }\>

  // Other deductible expenses

  legal\_fees\_purchase: number

  legal\_fees\_sale: number

  broker\_fees\_purchase: number

  broker\_fees\_sale: number

}

// Note: We do NOT specify use\_linear\_calculation. The simulator uses its default behavior.

// Per Section 1.5 (Brand Transparency), we do not make calculation method choices on the lawyer's behalf.

**Process flow:**

1\. Stage A returned requires\_stage\_b: true

2\. System prepares all simulator inputs

3\. System checks if authenticated session exists in backend cache

4\. If no session:

   a. Opens visible browser window on Ron's machine (NOT headless)

   b. Navigates to https://www.misim.gov.il/svtsvazmitnew/

   c. Ron sees prompt: "אנא הזדהה עם הכרטיס החכם / סיסמה כדי להמשיך"

   d. Ron authenticates (smart card insertion or password entry)

   e. System detects successful login (URL change or specific element appears)

   f. System stores the authenticated context in backend for reuse

5\. If session exists: silently reuses it

6\. System fills in all form fields using prepared inputs (using simulator defaults)

7\. System submits the form

8\. System reads result and takes screenshot

9\. System closes browser (or hides it for session reuse)

10\. System stores result \+ screenshot in case record

11\. Returns the official calculation

**Output structure:**

CapitalGainsResult {

  // Stage A result

  exemption\_check: ExemptionCheckResult

  // Stage B result (only if Stage A didn't fully exempt)

  calculation?: {

    method\_used: 'linear' | 'real'   // which method the simulator applied

    profit\_ils: number              // sale \- purchase \- deductibles

    indexed\_profit\_ils: number      // adjusted for CPI inflation

    tax\_amount\_ils: number          // final tax

    effective\_rate\_percent: number

    breakdown: {

      sale\_price: number

      purchase\_price: number

      indexed\_purchase\_price: number

      total\_deductions: number

      taxable\_profit: number

    }

    excess\_tax\_applicable: boolean   // מס יסף — high earners pay 5% extra

    screenshot\_url: string

  }

  // Summary

  total\_tax\_ils: number             // 0 if fully exempt, else calculation.tax\_amount\_ils

  source: 'exemption\_check' | 'live\_scrape'

  warnings: string\[\]

  notes: string\[\]

  calculated\_at: Date

}

---

## 5\. Data Model Updates

Add this to the main PRD's Section 8 (Data Models):

// Tax calculation entity — separate from Case for audit history

TaxCalculation {

  id: UUID

  case\_id: UUID (FK Case)

  type: 'purchase' | 'capital\_gains'

  // Inputs (JSONB \- varies by type)

  inputs: jsonb

  // Outputs

  total\_tax\_ils: number

  effective\_rate\_percent: number

  breakdown: jsonb

  warnings: string\[\]

  notes: string\[\]

  // Provenance

  source: 'live\_scrape' | 'exemption\_check' | 'manual\_entry'

  simulator\_url?: string

  screenshot\_storage\_path?: string

  scraped\_at?: timestamp

  scraper\_version: string    // increment when scraper logic changes

  // For multiple-buyer cases

  buyer\_breakdown?: jsonb

  // Lawyer override

  was\_manually\_overridden: boolean

  manual\_override\_amount?: number

  manual\_override\_reason?: string

  overridden\_by\_user\_id?: UUID (FK User)

  created\_at: timestamp

}

---

## 6\. API Endpoints

Add these to the main PRD's Section 9 (API Design):

\# Purchase Tax

POST   /api/cases/:id/tax/purchase                  → Job

GET    /api/cases/:id/tax/purchase                  → PurchaseTaxResult

POST   /api/cases/:id/tax/purchase/override         → PurchaseTaxResult (lawyer override)

\# Capital Gains Tax

POST   /api/cases/:id/tax/capital-gains/exemption-check  → ExemptionCheckResult (synchronous, fast)

POST   /api/cases/:id/tax/capital-gains/calculate        → Job (opens browser)

GET    /api/cases/:id/tax/capital-gains                  → CapitalGainsResult

POST   /api/cases/:id/tax/capital-gains/override         → CapitalGainsResult (lawyer override)

---

## 7\. UI Specifications

### 7.1 Purchase Tax Card on Case Detail

Shown as a card in the case detail view (similar to other Step cards). All UI in Hebrew RTL.

The card displays:

- Property value (in ILS with currency symbol)  
- Buyer type (Hebrew label)  
- Total purchase tax in ILS  
- Effective rate as percentage  
- Notes (e.g., "פטור מלא — מתחת לתקרת ₪1,978,745")  
- Last calculated timestamp \+ source (e.g., "Last calculated 12 minutes ago via official simulator")  
- View screenshot button (links to stored R2 image)  
- Run button (re-runs the calculation)  
- Edit/Override button

### 7.2 Capital Gains Tax Card on Case Detail

When Stage A only:

- Stage A result heading  
- Exemption status badge (פטור / חייב במס)  
- If exempt: section of law reference (e.g., "49ב(2) — דירת מגורים יחידה")  
- Reasoning in Hebrew  
- "Verify with live simulator" button (triggers Stage B)  
- Override button

When Stage B has run:

- Full calculation breakdown:  
  - Sale price  
  - Original purchase price  
  - Indexed purchase price (CPI-adjusted)  
  - Total deductible expenses  
  - Taxable profit  
  - Tax amount and rate  
- Authentication context (who logged into the simulator)  
- View screenshot button  
- Override button

### 7.3 Manual Override Modal

For cases where Ron disagrees with the calculation or knows of factors not captured.

- Shows the system's calculation prominently  
- Has a numeric input for the manual amount  
- Has a required text field for the reason  
- Saves an audit trail entry with timestamp and lawyer's name

### 7.4 Client-Facing Transparency View

Per Section 1.5 (Brand Transparency), the lawyer must be able to show the client exactly how every result was derived.

**Trigger:** Lawyer clicks "ייצוא דוח ללקוח" (Export Client Report) on any tax calculation card.

**Output:** A PDF report (in Hebrew) that includes:

**Page 1 — Executive Summary:**

- Firm logo and case identifier  
- Calculation type (Purchase Tax or Capital Gains Tax)  
- Property identification (address, block/parcel)  
- Final tax amount with date of calculation  
- The lawyer's signature line (manually signed after generation)

**Page 2 — Inputs Used:**

- Every input that was fed into the simulator, presented in clear Hebrew  
- Source of each input (e.g., "From your intake form submitted on 5.6.2026")  
- Client can verify each input is correct

**Page 3+ — Official Source Proof:**

- Full screenshot of the official Tax Authority simulator showing our submission  
- Full screenshot of the official Tax Authority simulator showing the result  
- Timestamp on every screenshot  
- URL of the official source clearly visible

**Page Last — Legal Basis (where applicable):**

- For exemption cases: the section of law that applies, quoted directly  
- Caveats: "This calculation reflects current law and the inputs provided. Changes to law, inputs, or transaction details may change the final tax. Your lawyer's signed advice is the authoritative document."

**Audit fields in PDF metadata:**

- Calculation ID (unique)  
- Generated timestamp  
- Generated by (lawyer name)  
- System version

**This PDF is the artifact the lawyer hands to the client.** The client can take it to a different lawyer, accountant, or directly to the Tax Authority for verification — and every number will check out against the official sources.

---

## 8\. Scraper Implementation Details

### 8.1 Resilience Requirements

These are **must-have**, not optional:

1. **Versioned selectors**  
     
   - Each Playwright selector must be defined as a constant at the top of the scraper file  
   - When a selector breaks, only that constant needs to change  
   - Example: `INPUT_PROPERTY_VALUE = "input[name='nochechiSchum']"` (verify actual name when implementing)

   

2. **Screenshot before and after**  
     
   - Screenshot the form after filling (proves we entered correct data)  
   - Screenshot the result page (proves what the simulator said)  
   - Both stored in R2 for audit

   

3. **Result validation**  
     
   - Before returning, verify the result is numeric and within sane bounds  
   - "Sane bounds" for purchase tax: 0% to 10% of property value (no edge case should exceed this)  
   - "Sane bounds" for capital gains: 0% to 50% of profit  
   - If outside bounds → store result but flag for manual review

   

4. **Retry logic**  
     
   - Retry 3 times with exponential backoff (1s, 3s, 9s)  
   - On 3rd failure, queue for manual processing and notify Ron

   

5. **Browser context isolation**  
     
   - Each scrape uses a fresh browser context (no cookies/storage from previous runs)  
   - This prevents accidentally using authenticated state for anonymous calculations

   

6. **Recording mode for debugging**  
     
   - Set `HEADLESS=false` in development to watch the scraper work  
   - Default: headless in production

### 8.2 Test Cases to Validate

The scraper must pass these tests on first implementation:

**Purchase Tax (2026 brackets):** | Test Case | Property Value | Buyer Type | Expected Tax | |-----------|---------------|------------|--------------| | 1 — small single residence | ₪1,900,000 | single | ₪0 | | 2 — small additional residence | ₪1,900,000 | additional | ₪152,000 | | 3 — mid-range single residence | ₪2,500,000 | single | ₪20,538 | | 4 — large single residence | ₪7,000,000 | single | \~₪319,790 | | 5 — foreign resident | ₪2,000,000 | foreign | ₪160,000 |

Verify each result against the live simulator when implementing. If the simulator returns different numbers, **the simulator wins** — never the hardcoded expectation. The expectations above are sanity checks based on current law.

**Capital Gains Stage A (Exemption logic):** | Test Case | Inputs | Expected Result | |-----------|--------|-----------------| | 1 — single residence | owns\_other=false, sale=2M | EXEMPT (49ב(2)) | | 2 — additional property | owns\_other=true | requires Stage B | | 3 — recent exemption | sold\_with\_exemption\_18mo=true | requires Stage B | | 4 — inheritance | is\_inherited=true, deceased eligible | EXEMPT (49ב(5)) | | 5 — luxury cap | single residence, sale=10M | partial — requires Stage B for excess |

### 8.3 Provenance Requirements (Brand Transparency Implementation)

Per Section 1.5, every calculation must be fully traceable. The scraper must capture and store:

**Pre-submission state:**

- All inputs that will be submitted to the simulator (structured data)  
- Timestamp of when inputs were prepared  
- Source of each input (e.g., "case.intake.section\_a.field\_3")  
- Screenshot of the input form FILLED but BEFORE submission

**Post-submission state:**

- Screenshot of the result page (full page, not just the result)  
- Raw HTML of the result page (for re-parsing if needed)  
- Any URLs visited during the scrape (navigation chain)  
- Timestamps for each navigation step

**Audit metadata:**

- Unique calculation ID (UUID, never reused)  
- User who initiated the calculation  
- Backend session ID (to correlate with logs)  
- Scraper version number (so we can verify which logic was used)  
- Source simulator URL with the date checked  
- Total scrape duration

**Storage policy:**

- Screenshots stored in R2 with infinite retention  
- Public URL with expiring tokens (for sharing in client PDFs)  
- Database row for each calculation with all metadata  
- Never delete provenance data, even if the calculation is overridden

**Retrieval requirements:**

- The lawyer can retrieve the full provenance chain for ANY past calculation in under 5 seconds  
- Even calculations from 5 years ago must be retrievable  
- This is non-negotiable for legal defensibility

**Implementation hint:** Create a `Provenance` table separate from `TaxCalculation`. Every TaxCalculation has a one-to-many relationship with Provenance entries (one per stored artifact: input screenshot, result screenshot, HTML, etc.). This structure also supports our other scrapers (Taboo, Identity Check) using the same provenance model.

---

## 9\. Development Plan

### Sprint Allocation

This feature spans **1.5 sprints** within the main PRD's Sprint 3 (Document Generation).

### Week 1: Purchase Tax Scraper

- Set up Playwright infrastructure  
- Build the purchase tax scraper with all 6 buyer types  
- Implement screenshot capture and storage  
- Build the result parser  
- Write the 5 validation test cases  
- UI: Purchase tax card on case detail

### Week 2: Capital Gains Stage A (Exemption Engine)

- Build the exemption decision tree  
- All 7 decision rules implemented and tested  
- Pure business logic — no external calls  
- UI: Stage A result card

### Week 3: Capital Gains Stage B (Live Calculation)

- Build the authenticated scraper for שומה עצמית  
- Smart card prompt UX  
- Form filling and result extraction  
- Manual override flow  
- UI: Stage B card and screenshots

---

## 10\. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
| :---- | :---- | :---- | :---- |
| **Wrong tax calculation shown to client** | Low | **Existential (brand)** | All calculations include screenshot proof from official source; lawyer review required; client PDF shows the official source so client can verify; manual override flow for edge cases |
| **Lawyer cannot explain how a number was derived** | Low | **Existential (brand)** | Full audit trail in UI (Section 7.4); every calculation has provenance metadata (Section 8.3); test from Section 1.5 must pass before ship |
| **System produces a result that contradicts the official simulator** | Very Low | Critical | We exclusively use the official simulator — no parallel logic; sanity bounds validation flags any anomaly |
| Government simulator HTML changes | High | High | Selectors as constants; daily health-check test; Sentry alerts |
| Government simulator down | Low | Medium | Retry logic; queue for later; notify lawyer. Never substitute with our own calculation. |
| Smart card authentication fails | Medium | Medium | Clear error message; fallback to username/password; manual entry option |
| Bracket changes mid-development | Low | Low | We don't hardcode brackets, so this is automatically handled |
| Capital gains exemption logic outdated | Medium | High | Code each rule with its source law reference; legal review at MVP launch and yearly; uncertainty surfaced explicitly in UI |
| Provenance data lost (storage failure) | Low | High | Daily R2 backups; database has metadata even if screenshots lost; recovery procedure documented |

---

## 11\. Resolved Product Decisions

These were open questions in v1.0; v1.1 has product decisions for all of them.

### 11.1 Improving housing refund tracking

**Decision: NOT in scope for MVP.** The system will flag the eligibility ("Refund opportunity — 18-month deadline") in the calculation result but will not actively track or remind the lawyer. If lawyer requests this feature based on real-world usage, we add it in Phase 2\.

### 11.2 Multiple buyers with different statuses

**Decision: NOT in scope for MVP.** The `COMBINED_BUYERS` buyer type is removed from the initial implementation. If the case has multiple buyers, the lawyer enters them as a single combined buyer with one classification. Phase 2 will add proper per-buyer breakdown.

This simplifies the implementation significantly and covers \~90% of real cases (most transactions are couples in identical legal status).

### 11.3 Tax Authority login session persistence

**Decision: YES, keep session warm for the entire work day.**

When Ron authenticates to the שומה עצמית simulator with his smart card or password, the system should:

1. Store the authenticated browser context (cookies, session storage) in memory  
2. Reuse the same context for subsequent capital gains calculations during the same work session  
3. Detect when the session expires (typical: 30 minutes of inactivity) and prompt Ron to re-authenticate  
4. Clear the session at end of day or when Ron logs out

**Implementation note:** The Tax Authority session lives on the backend, not the browser. The backend uses Playwright with persistent context.

**Security note:** This means the backend holds an authenticated Tax Authority session for Ron during work hours. This is acceptable because:

- The backend is on Israeli hosting (Kamatera) — same jurisdiction as the data  
- Ron explicitly initiates the session (active consent)  
- Session auto-expires  
- All actions are logged in the audit trail

### 11.4 Linear vs Real calculation choice

**Decision: Use the simulator's default behavior. The system does NOT pick between methods.**

For properties bought before 1.1.2014 (eligible for linear calculation):

1. The system fills the simulator form using the simulator's default settings  
2. Whatever calculation method the official simulator uses is what we report  
3. The result shows clearly which method was used (visible in the screenshot)  
4. The lawyer can manually request a re-calculation with a different method if needed (manual override flow)

**Why this approach:**

- Aligns with the Brand Transparency principle (Section 1.5): we don't make choices the lawyer would have to explain  
- The official simulator's choice is the legally-correct default  
- Eliminates risk of the system picking a method that turns out to be wrong in the client's specific situation  
- Simpler implementation: one calculation per case, not two

**Future enhancement:** If the lawyer requests it (based on real-world usage), we can add an explicit "compare both methods" button — but the default behavior remains "use the simulator's default."

### 11.5 Excess tax (מס יסף) threshold

**Decision: Verify live with each calculation AND display the threshold in the backoffice for transparency.**

The Tax Authority simulator will apply the correct threshold automatically. Our system should:

1. Display the current excess tax threshold prominently in the backoffice (Section 16\)  
2. Read the threshold from the backoffice config when generating the input form for the simulator  
3. Flag in the result if excess tax was applied  
4. Show educational tooltip to lawyer: "מס יסף הופעל — הלקוח חויב ב-5% נוספים מעל ההכנסה השנתית של ₪X"

The threshold for 2026 is approximately ₪721,000 of annual income but must be verified live.

### 11.6 Audit retention

**Decision: Retain forever — until the lawyer's archive system stores them.**

All calculation screenshots, input data, and results are retained indefinitely in R2 storage until the lawyer's own archive system (Legal CRM or future archival system) takes ownership. The system never auto-deletes calculation history.

Implementation:

- No automated cleanup jobs  
- No retention policy in the database  
- Backoffice exposes a "Export all data" function for the lawyer to download everything when they wish to migrate  
- A future "archive to Legal CRM" integration (Phase 2\) can move old data out

---

## 12\. Out of Scope

These are explicitly NOT part of this feature spec (deferrable to later phases):

- **Tax filing automation** — calculating and reporting are different. Filing the שומה עצמית digitally with the Tax Authority is Phase 2\.  
- **Linear calculation optimizer** — finding the optimal year-split for linear calculation is a Phase 2 enhancement  
- **Historical CPI lookups** — for now, we trust the Tax Authority simulator's indexing  
- **Multi-property packages** — selling 2 apartments in one transaction has complex rules; not in scope  
- **Commercial real estate** — different tax brackets entirely; not in scope (residential only per main PRD)  
- **Trust / Inheritance complex structures** — beyond simple individual inheritance; require manual lawyer judgment

---

## 13\. Acceptance Criteria

This feature is ready to ship when:

**Functional:**

- [ ] Purchase tax scraper runs successfully on the 5 test cases above  
- [ ] Each test case result matches the simulator output exactly (verified manually 3 times)  
- [ ] Capital gains Stage A (exemption check) handles all 7 decision rules with the 5 test cases  
- [ ] Capital gains Stage B opens a visible browser for authentication, then automates the rest  
- [ ] The smart card prompt UX works on Windows (Ron's environment)  
- [ ] Session persistence works (Ron authenticates once per day, not per case)

**Brand Transparency (per Section 1.5 — non-negotiable):**

- [ ] Every calculation result includes a visible "View Source" button that opens the saved simulator screenshot  
- [ ] Every calculation result shows the timestamp of when it was performed  
- [ ] Every calculation has a unique ID that's visible and copyable  
- [ ] Client-facing PDF report can be generated for any calculation (Section 7.4)  
- [ ] Client PDF includes inputs, official simulator screenshots, and result  
- [ ] All provenance data (Section 8.3) is captured and retrievable for at least 5 years  
- [ ] The "30-second test" passes: a lawyer can explain any historical number's derivation within 30 seconds using the UI  
- [ ] Error states never show fallback numbers — only "calculation unavailable, please try again"

**Quality:**

- [ ] All UI is in Hebrew RTL with proper Israeli number/currency formatting  
- [ ] Manual override flow works and writes an audit trail entry  
- [ ] Sentry alerts are configured for selector failures  
- [ ] Lawyer can view the full calculation history per case

**Performance:**

- [ ] Purchase tax completes in \< 15 seconds  
- [ ] Capital gains Stage A in \< 1 second  
- [ ] Capital gains Stage B in \< 60 seconds (excluding lawyer authentication time)  
- [ ] Provenance retrieval from past calculations in \< 5 seconds

---

## 14\. Reference Materials

For implementing developers:

- **Main PRD:** `PRD_Phase1_Pre-Signing.md`  
- **PRD Delta v1.1:** `PRD_DELTA_v1.0_to_v1.1.md`  
- **Tax Authority — Purchase Tax simulator:** `https://www.misim.gov.il/svsimurechisha/startPage.aspx`  
- **Tax Authority — Capital Gains simulator:** `https://www.misim.gov.il/svtsvazmitnew/FrmHadrachaRashit.aspx`  
- **Gov.il guidance page (Purchase Tax):** `https://www.gov.il/he/service/real_eatate_taxsimulator`  
- **Gov.il guidance page (Capital Gains):** `https://www.gov.il/he/service/real_estate_selfshuma`  
- **Israeli Land Taxation Law (חוק מיסוי מקרקעין):** Section 9 for purchase tax, Sections 47-49 for capital gains

---

## 15\. Glossary

For developers unfamiliar with Israeli tax terminology:

| Hebrew | Transliteration | English |
| :---- | :---- | :---- |
| מס רכישה | Mas Rechisha | Purchase Tax (paid by buyer) |
| מס שבח | Mas Shevach | Capital Gains Tax on real estate (paid by seller) |
| שומה עצמית | Shuma Atzmit | Self-Assessment (the tax return form) |
| דירת מגורים יחידה | Dirat Megurim Yechida | Single Residence (preferential tax treatment) |
| דירה נוספת | Dira Nosefet | Additional Residence (higher tax) |
| משפר דיור | Meshaper Diyur | Housing Improver (selling primary to buy new primary) |
| עולה חדש | Oleh Chadash | New Immigrant (special tax discounts within 8-year window) |
| תושב חוץ | Toshav Chutz | Foreign Resident |
| פטור | Patur | Exempt |
| שבח | Shevach | Capital Gain (the profit being taxed) |
| תיקון 76 | Tikkun 76 | Amendment 76 — introduced linear calculation for properties bought before 2014 |
| מס יסף | Mas Yesef | Excess Tax — additional 5% for high-income individuals |
| תקרת פטור | Tikrat Petur | Exemption Cap (currently \~₪4.6M for single residence luxury threshold) |
| חישוב לינארי | Chishuv Linari | Linear Calculation — taxes only the period since 2014 reform at full rate |
| התחדשות עירונית | Hithadshut Ironit | Urban Renewal (TAMA 38, Pinui-Binui) |

---

## 16\. Backoffice Configuration Requirements

This feature has values that should NEVER be hardcoded in the source code. These values must be exposed through the **Backoffice Admin Panel** (see separate document: `BACKOFFICE_SPEC.md`).

### Why this matters

Tax laws and thresholds change. Every value below has changed at least once in the last 5 years. If they're hardcoded, every change requires a developer deploy. If they're configurable, Ron or Lev can update them in 30 seconds.

### Values that MUST be configurable

For the Tax Calculator feature specifically:

| Config Key | Description | Current Value (2026) | Frequency of Change |
| :---- | :---- | :---- | :---- |
| `purchase_tax_simulator_url` | URL of the purchase tax simulator | misim.gov.il/svsimurechisha | Rarely |
| `capital_gains_simulator_url` | URL of the capital gains simulator | misim.gov.il/svtsvazmitnew | Rarely |
| `excess_tax_annual_income_threshold` | Income threshold above which מס יסף applies | ₪721,000 | Annual |
| `excess_tax_additional_rate_percent` | Extra rate for high earners | 5% | Rarely |
| `single_residence_luxury_cap` | Above this sale price, partial exemption only | ₪4,603,000 | Annual |
| `linear_calculation_cutoff_date` | Properties bought before this date can use linear | 1.1.2014 | Never (legal anchor) |
| `improving_housing_grace_period_months` | Time to sell previous residence for refund | 18 months | Rarely |
| `oleh_eligibility_window_years_before` | How long before aliyah Oleh status counts | 1 year | Rarely |
| `oleh_eligibility_window_years_after` | How long after aliyah Oleh status counts | 7 years | Rarely |
| `disability_minimum_percent` | Minimum disability % for tax discount | 19% | Rarely |
| `inheritance_max_share_percent_for_single_residence` | Max share of inherited property to still qualify | 50% | Never (legal anchor) |
| `session_timeout_minutes` | Tax Authority session expiry | 30 minutes | Tracks Tax Authority policy |
| `scraper_retry_max_attempts` | How many times to retry on failure | 3 | Tunable based on observed reliability |
| `scraper_retry_backoff_seconds` | Initial backoff for retries | 1, 3, 9 | Tunable |
| `result_sanity_bounds_purchase_max_percent` | Max plausible tax rate for purchase | 10% | Rarely |
| `result_sanity_bounds_capital_gains_max_percent` | Max plausible tax rate for capital gains | 50% | Rarely |

### How the developer should implement this

1. Create a `system_config` table in the database (key/value/description schema)  
2. On application startup, load all config values into memory  
3. The Tax Calculator module reads from this in-memory config — never from constants  
4. The Backoffice exposes a UI to view and edit each value  
5. When a value is changed in the backoffice, the in-memory cache is invalidated and reloaded  
6. Every config change is logged in an audit trail (who, when, old value, new value, reason)

### Default values

The database migration that creates the `system_config` table should also seed it with all the values above as defaults. This way, on first deploy, the system has sane defaults that can be tweaked later.

---

## 17\. Backoffice Read-Only Data

Some data is also exposed in the Backoffice for monitoring (read-only):

| Data | Purpose | Source |
| :---- | :---- | :---- |
| Last 50 purchase tax calculations | Monitor scraper health | TaxCalculation table |
| Last 50 capital gains calculations | Monitor scraper health | TaxCalculation table |
| Scraper failure log (last 7 days) | Detect site changes | Sentry \+ DB logs |
| Average calculation time (rolling 7 days) | Detect degradation | DB queries |
| Total calculations this month | Usage metrics | DB queries |
| Active Tax Authority sessions | Security monitoring | In-memory state |

These are detailed in the `BACKOFFICE_SPEC.md` document.

---

**End of Feature Spec**

This spec, combined with the main PRD, the delta document, and the backoffice spec, contains everything needed to implement the Tax Calculator feature.  
