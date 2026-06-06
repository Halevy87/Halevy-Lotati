# PRD Changes — Delta Document

## Updates to PRD v1.0 → v1.1 (Phase 1\)

**Document purpose:** This document contains ONLY the changes to the original PRD. Apply these on top of `PRD_Phase1_Pre-Signing.md`. Each change is self-contained and can be applied independently.

**Change reason:** Discoveries made during live workflow validation on a real Bat Yam property:

1. The lawyer receives only an address from the client, not block/parcel — a missing step (Address Resolver) needs to be added before Step 6\.  
2. Pulling Taboo extracts does NOT require a lawyer's digital signature. This removes the biggest technical blocker from Phase 1 and simplifies Step 6 significantly.  
3. Hosting must be in Israel — government sites block foreign IPs.  
4. Payment automation becomes the new bottleneck (Strategy A — pause-for-approval — chosen for MVP).

---

## Change Summary

| \# | Section | Change Type | Severity |
| :---- | :---- | :---- | :---- |
| 1 | New section 0.5 — Production Environment Requirements | ADD | High |
| 2 | Section 5 — Step renumbering: Insert new Step 5.5 (Address Resolver) | ADD | High |
| 3 | Section 5, Step 6 (Taboo Extracts) | REWRITE | High |
| 4 | Section 5, Step 7 (Condo File) | MINOR UPDATE | Low |
| 5 | Section 7 — Tech Stack: Hosting | UPDATE | High |
| 6 | Section 8 — Data Models: Add `address_resolution` table | ADD | Medium |
| 7 | Section 9 — API Design: Add address resolution endpoints | ADD | Medium |
| 8 | Section 11 — Security: Payment flow and PCI considerations | ADD | Medium |
| 9 | Section 12 — Development Roadmap: Sprint reordering | UPDATE | High |
| 10 | Section 14 — Risks: Remove digital signature risk, add payment risk | UPDATE | Medium |
| 11 | Section 15 — Out of Scope: Move digital signature to Phase 2 | UPDATE | Low |
| 12 | Appendix C — Open Questions: Remove resolved questions | UPDATE | Low |

---

## CHANGE 1 — Add Production Environment Requirements

### Where to add

After Section 0 (Critical: Language & Localization), before Section 1 (Executive Summary).

### Add this new section

\#\# 0.5. ⚠️ Critical: Production Environment Requirements

\> \*\*This section is non-negotiable and overrides any default hosting recommendations.\*\*

\#\#\# The backend must run from an Israeli IP address.

Through live validation, we confirmed that Israeli government services apply IP-based restrictions that affect any backend hosted outside Israel:

1\. \*\*Some government endpoints block non-Israeli IPs entirely\*\* (HTTP 403\)

2\. \*\*Aggressive rate limiting from foreign IPs\*\* — even when access is allowed

3\. \*\*Cloudflare and similar protections flag data-center IPs from non-Israeli regions\*\* as suspicious traffic

4\. \*\*Some payment processors require an Israeli billing address\*\*, which is harder to maintain credibly from a foreign IP

\#\#\# Mandatory hosting choice

| Component | Required Location | Recommended Provider |

|-----------|-------------------|----------------------|

| Frontend | Anywhere (global CDN is fine) | Vercel |

| Backend API | \*\*Israel\*\* | Kamatera (Tel Aviv data center) |

| Background workers (scrapers) | \*\*Israel\*\* | Same Kamatera VPS |

| Database (PostgreSQL) | Israel or EU | Neon (EU region) or self-hosted on Kamatera |

| Document storage | Israel or EU | Cloudflare R2 (EU region) |

| Redis | Israel or EU | Self-hosted on the same Kamatera VPS |

\#\#\# Cost implications

A Kamatera Israel VPS suitable for MVP costs \~$30-50/month (4 vCPU, 8GB RAM, 50GB SSD). This is more expensive than Fly.io or Railway but is non-negotiable for reliability with government scraping.

\#\#\# Network access list

The backend will need outbound network access to:

\- \`\*.justice.gov.il\` (Land Registry portal)

\- \`\*.gov.il\` (Various government services)

\- \`www.govmap.gov.il\` (Mapping service)

\- \`api.govmap.gov.il\` (GovMap API)

\- \`mekarkein-online.justice.gov.il\` (Online land registry)

\- \`api.anthropic.com\` (AI calls)

\- \`vision.googleapis.com\` (OCR)

\- Standard infrastructure endpoints (S3/R2, Stripe, email provider)

Most Israeli VPS providers allow all outbound traffic by default.

---

## CHANGE 2 — Insert New Step 5.5 (Address Resolver)

### Where to add

In Section 5 ("The 10 Pre-Signing Steps — Detailed Specs"), insert AFTER Step 5 (Identity & Risk Check) and BEFORE Step 6 (Land Registry Extracts).

### Note on numbering

The original PRD has steps 1-10. We're inserting a new step between 5 and 6\. To preserve the original numbering for backward compatibility, this new step is called **Step 5.5**. Alternatively, the entire numbering can be shifted (5.5 → 6, 6 → 7, etc.) — recommend keeping 5.5 for clarity.

### Add this new step

\#\#\# Step 5.5: Address Resolver

\*\*Trigger:\*\* Automatic — fires when Step 2 (intake form) completes, or manually when the lawyer creates a case with address but no block/parcel info.

\*\*Why this step exists:\*\* The client provides an address ("Bar Yehuda 33, Bat Yam apartment 13") but NOT block/parcel/sub-parcel numbers. The Taboo extract system requires block/parcel. We need an intermediate step to convert one to the other.

\*\*Inputs:\*\*

\- Property city

\- Property street name

\- Property number

\- Apartment number (if condo)

\*\*Automated Actions:\*\*

\- Call GovMap's official searchAndLocate JS API via Playwright headless browser

\- Pass \`type: govmap.locateType.lotParcelToAddress\` and the full address

\- Extract returned block (gush) and parcel (chelka) from the response

\- Store the resolution in the case record

\- Note: GovMap does NOT return sub-parcel (tat-chelka). Sub-parcel must be identified later from the consolidated Taboo extract (Step 6).

\*\*Manual Actions:\*\*

\- Lawyer reviews resolved block/parcel for plausibility

\- If resolution fails or returns multiple candidates, lawyer enters manually

\*\*Outputs:\*\*

\- Resolved gush \+ chelka stored in case record

\- Confidence score from GovMap (if available)

\- Coordinates (ITM — Israeli Transverse Mercator grid) for downstream mapping

\- Status flag: \`auto\_resolved\` / \`manual\_entry\_required\` / \`multi\_candidate\`

\*\*Acceptance Criteria:\*\*

\- Resolution completes in \< 15 seconds for a valid address

\- Address resolution success rate ≥ 90% for valid Israeli addresses

\- When resolution fails, the lawyer sees a clear error message and can enter manually

\- The resolved gush/chelka is validated against expected format (numeric, plausible range)

\*\*External Dependencies:\*\*

\- GovMap API token (free, requires one-time registration at api.govmap.gov.il)

\- Playwright headless Chromium

\- Israeli IP for the backend (see Section 0.5)

\*\*Notes:\*\*

\- GovMap is the official Israeli government mapping platform. Its data comes from the Survey of Israel (mapi).

\- The JS API is stable but periodically updated. Monitor for breakage via Sentry alerts.

\- For addresses where GovMap fails (rare cases, very new constructions), the lawyer can fallback to manual entry, OR the system can try alternative providers (gov.il/apps/mapi, nadlan.gov.il) as Phase 2 enhancement.

\*\*Code reference:\*\*

The reference implementation is in \`address\_resolver.py\` (see project repo). Key function:

\`\`\`python

async def resolve\_address(city: str, street: str, number: str, api\_token: str) \-\> AddressResolutionResult

\---

\#\# CHANGE 3 — Rewrite Step 6 (Land Registry Extracts)

\#\#\# Where to replace

In Section 5, find Step 6 (Land Registry (Taboo) Extracts) and \*\*replace the entire step\*\* with the version below.

\#\#\# Reason for rewrite

The original Step 6 assumed digital signature was required. Live research with the Israeli Ministry of Justice's portal (mekarkein-online.justice.gov.il) confirmed that \*\*pulling Taboo extracts does not require a lawyer's digital signature\*\*. This significantly simplifies the implementation.

\#\#\# New Step 6 text

\`\`\`markdown

\#\#\# Step 6: Land Registry (Taboo) Extracts

\*\*Trigger:\*\* Automatic — fires when Step 5.5 (Address Resolver) completes successfully; manual re-run available.

\*\*IMPORTANT — Digital signature is NOT required for pulling Taboo extracts.\*\* Research confirmed (June 2026\) that the Ministry of Justice's online portal (mekarkein-online.justice.gov.il) allows anyone with the block/parcel and a credit card to pull official, digitally-signed extracts. The lawyer's digital signature is only required for FILING actions (registering cautionary notes, mortgages, sale transactions) — all of which happen in Phase 2 (post-signing).

\*\*Inputs:\*\*

\- Resolved block \+ parcel (from Step 5.5)

\- Sub-parcel (if known; otherwise pull consolidated first to identify it)

\- Firm's payment method

\- Firm's email address for receipts

\*\*Automated Actions:\*\*

The fetcher runs three sequential operations:

1\. \*\*Pull consolidated extract first\*\* (\`nesach merukaz\` — \~₪14)

   \- Shows all sub-parcels in the building, their owners, sizes

   \- Used to identify which sub-parcel corresponds to "apartment 13" of the client

   \- PDF is saved \+ parsed for structured data

2\. \*\*Match sub-parcel to client's apartment\*\*

   \- Claude Vision analyzes the condo plan (PDF from Step 7\) alongside the consolidated extract

   \- Matches "apartment 13" claim from intake form to actual sub-parcel number

   \- Confidence score returned; if low, lawyer reviews manually

3\. \*\*Pull detailed (per-apartment) extract\*\* (\`nesach pratani\` — \~₪14)

   \- Now with the correct sub-parcel, pull the apartment-specific extract

   \- This has the actual mortgages, cautionary notes, and rights for the apartment

\*\*Parse extracted PDFs\*\* to extract structured data:

\- Current owner(s) with ID numbers

\- Property dimensions

\- Active mortgages with creditor names and amounts

\- Cautionary notes (\`he'arot azhara\`)

\- Liens

\- Attached units (parking, storage)

\- Leasehold vs freehold status

\*\*Payment handling (Strategy A — MVP):\*\*

The fetcher fills out the entire request form automatically. When it reaches the payment page, the workflow PAUSES:

\- The lawyer receives a push notification (web \+ mobile)

\- The notification includes case ID, parcel info, fee amount, and a one-click "Approve payment" button

\- On approval, the system continues automatically (credit card details filled, payment submitted, PDF downloaded)

\- This typically takes the lawyer \< 10 seconds of attention per extract

\*\*Future enhancement (Strategy B — Phase 2):\*\*

Store the firm's credit card in a PCI-compliant vault (Stripe or similar) and inject card details automatically into the payment form. Removes lawyer involvement entirely. Will be developed only after Strategy A is proven in production for at least 4 weeks.

\*\*Manual Actions:\*\*

\- Lawyer approves each payment via push notification (5-10 seconds)

\- Lawyer reviews parsed data for any mismatches with intake claims (auto-flagged)

\*\*Outputs:\*\*

\- 2 PDF extracts in case folder (consolidated \+ detailed)

\- Structured property data in database

\- Side-by-side comparison: client claims vs Taboo reality

\- Flags for any mismatches (e.g., client said "no mortgage" but Taboo shows one)

\- Audit trail with transaction IDs from the government portal

\*\*Acceptance Criteria:\*\*

\- Form auto-fill completes successfully in 95%+ of cases

\- Payment approval flow takes lawyer \< 10 seconds per extract

\- PDF parsing extracts owner names with 99%+ accuracy (via Claude Vision)

\- All Hebrew characters correctly extracted

\- Round-trip (request → approval → PDF → parsed data) completes in \< 3 minutes including lawyer approval time

\- Failed scraping is detected and the lawyer is notified within 60 seconds with a clear error message

\*\*External Dependencies:\*\*

\- mekarkein-online.justice.gov.il (Ministry of Justice portal)

\- Firm's credit card (used via push notification approval flow in MVP)

\- Playwright headless Chromium

\- Anthropic Claude Vision for PDF parsing

\- Push notification service (web push \+ native)

\*\*Cost per case:\*\*

\- Consolidated extract: ₪14

\- Detailed extract: ₪14

\- Total per case: \~₪28-30 (vs ₪15 estimated in original PRD; updated based on actual current fees)

\*\*Code reference:\*\*

The reference implementation is in \`taboo\_fetcher.py\` (see project repo). Key class:

\`\`\`python

class TabooFetcher:

    async def fetch(self, parcel: ParcelIdentifier, extract\_type: ExtractType, case\_id: str) \-\> TabooExtractResult

\---

\#\# CHANGE 4 — Minor Update to Step 7 (Condo File)

\#\#\# Where to update

In Section 5, find Step 7 (Condominium File Retrieval). Update the digital signature note.

\#\#\# Find and replace

\*\*Find this text:\*\*

**External Dependencies:**

- Same as Step 6  
- Anthropic Claude Vision for floor plan analysis

\*\*Replace with:\*\*

**External Dependencies:**

- Same as Step 6 — including the push-notification payment approval flow  
- Anthropic Claude Vision for floor plan analysis

**Note:** No digital signature required, identical to Step 6\.

\#\#\# Also update the cost estimate

\*\*Find:\*\*

- Total cost ≤ ₪45 per case (3 documents × ₪15)

\*\*Replace with:\*\*

- Total cost \~₪42 per case (3 documents × \~₪14)

\---

\#\# CHANGE 5 — Update Tech Stack: Hosting

\#\#\# Where to update

Section 7, "Infrastructure & DevOps" table.

\#\#\# Find and replace the Backend hosting row

\*\*Find:\*\*

\`\`\`markdown

| Fly.io OR Railway | Backend hosting | Container-based; good Docker support; affordable |

**Replace with:**

| Kamatera (Israel) | Backend hosting | \*\*REQUIRED\*\* — Israeli IP needed for government scraping (see Section 0.5). Tel Aviv data center. \~$30-50/mo for MVP. |

### Also update the Compliance Note

**Find:**

\*\*Compliance Note on Hosting:\*\*

For Israeli compliance with the Privacy Protection Law, document storage must remain in Israel or an "adequate" jurisdiction (EU). Cloudflare R2 with EU region selected satisfies this. If we later need pure Israeli hosting, Kamatera is the standard option.

**Replace with:**

\*\*Compliance Note on Hosting:\*\*

The backend MUST be hosted in Israel (Kamatera) — see Section 0.5 for the operational reasoning. This also satisfies the Israeli Privacy Protection Law data residency requirement. Document storage uses Cloudflare R2 with EU region (also compliant). The frontend can be hosted globally on Vercel; only the backend has the Israeli IP requirement.

---

## CHANGE 6 — Add Data Model: address\_resolution

### Where to add

Section 8 (Data Models). Add a new entity AFTER the `Case` entity.

### Add this new model

// Address resolution attempts (stored separately for audit \+ retry analysis)

AddressResolution {

  id: UUID

  case\_id: UUID (FK Case)

  // Input

  city: string

  street: string

  number: string

  apartment\_number\_claimed: string?    // what the client said (e.g., "13")

  // Output

  status: 'success' | 'failed' | 'manual\_entry' | 'multi\_candidate'

  resolved\_gush: string?

  resolved\_chelka: string?

  resolved\_tat\_chelka: string?         // populated later from Taboo Step 6

  coordinates: jsonb?                  // {x, y} in ITM

  // Metadata

  method: 'govmap\_js' | 'govmap\_rest' | 'manual'

  raw\_response: jsonb?

  resolution\_time\_ms: integer

  resolved\_at: timestamp

  resolved\_by\_user\_id: UUID? (FK User) // null if automatic

}

### Also update the Case model

In the `Case` entity, add these fields after `property_city`:

  // Resolved property identifiers (from Step 5.5)

  resolved\_gush: string?

  resolved\_chelka: string?

  resolved\_tat\_chelka: string?

  apartment\_number\_claimed: string?    // raw client claim, e.g., "13"

  property\_coordinates: jsonb?

---

## CHANGE 7 — Add API Endpoints: Address Resolution

### Where to add

Section 9 (API Design), under "Steps (one endpoint per step's actions)".

### Add this new section (after Step 2 endpoints, before Step 3 endpoints)

\# Step 5.5 — Address Resolution

POST   /api/cases/:id/resolve-address                  → Job

GET    /api/cases/:id/address-resolution               → AddressResolution

PATCH  /api/cases/:id/address-resolution/manual        → AddressResolution (lawyer manual entry)

---

## CHANGE 8 — Add Security: Payment Flow

### Where to add

Section 11 (Security, Privacy & Compliance). Add new subsection at the end of "Technical Security".

### Add this new subsection

\#\#\# Payment Approval Flow (Strategy A — MVP)

Since Phase 1 MVP uses lawyer-approved payments (not stored cards), the security model is:

1\. \*\*Lawyer pre-loads payment intent\*\* when starting a case

2\. When the system reaches a payment step, it generates a one-time approval link

3\. The link is sent via push notification (signed with HMAC, single-use, expires in 5 minutes)

4\. On approval, the system uses a server-side stored card (Israeli compliance) ONLY for that specific transaction

5\. Full audit log: every approval recorded with timestamp, IP, transaction ID

\*\*PCI compliance approach:\*\*

\- Card data NEVER stored in our database

\- Card details held in a PCI-DSS Level 1 vault (recommend: Tranzila or Hyp for Israeli market)

\- Each transaction generates a tokenized request

\- We store only the transaction ID and last 4 digits

\*\*For Strategy B (Phase 2):\*\*

\- Card stored as token in the vault from day 1

\- Approval flow becomes optional (firm setting)

\- Audit trail extends to capture which transactions ran fully automated vs lawyer-approved

\- Additional safeguards needed: spending limits, anomaly detection, daily transaction caps

---

## CHANGE 9 — Update Development Roadmap

### Where to update

Section 12 (Development Roadmap). Reorder and renumber sprints.

### Replace the entire sprint section

**Find:** All text starting with "\#\#\# Sprint Structure" and ending before "\#\#\# Post-Launch Phase 1"

**Replace with:**

\#\#\# Sprint Structure

\- 2-week sprints

\- Sprint 0: Foundation (1 sprint)

\- Phase 1 MVP: 5 sprints (10 weeks total) — down from 6 sprints in v1.0

\- Each sprint targets ONE complete module to enable continuous feedback

\#\#\# Sprint 0 (Foundation) — 2 weeks

\- Project setup (FE \+ BE \+ DB \+ deployment pipeline)

\- \*\*Backend deployed to Kamatera Israel from Day 1\*\* (do not develop locally only; validate Israeli IP works with government sites)

\- \*\*Hebrew/RTL foundation set up from day one:\*\*

  \- \`\<html dir="rtl" lang="he"\>\` configured globally

  \- \`tailwindcss-rtl\` plugin installed and configured

  \- \`next-intl\` set up with \`messages/he.json\`

  \- Hebrew fonts (Frank Ruhl Libre \+ Heebo) loaded with Hebrew subset

  \- Israeli locale (\`he-IL\`) configured for dates, numbers, currency

  \- shadcn/ui base components installed and RTL-validated

  \- Test page proving end-to-end RTL works correctly on all target browsers

\- Authentication (magic link \+ 2FA) — all UI in Hebrew

\- Base data models (User, Case, Party, Document, Activity, AddressResolution)

\- Empty dashboard \+ case detail shell with Hebrew labels

\- Basic case CRUD

\- \*\*Acceptance:\*\* Ron can log in (Hebrew UI), create a case manually (Hebrew form), see it in the dashboard. All Hebrew renders correctly RTL on Chrome, Safari, iOS Safari, Android Chrome. Backend responds from an Israeli IP.

\#\#\# Sprint 1 (Address Resolver \+ Identity Check) — 2 weeks

This sprint combines the two simplest scraping modules to validate the scraping infrastructure end-to-end.

\- \*\*Address Resolver (Step 5.5):\*\*

  \- GovMap API integration via Playwright

  \- Reference: \`address\_resolver.py\`

  \- GovMap free token registration (one-time)

\- \*\*Identity & Risk Check (Step 5):\*\*

  \- 5-source identity check

  \- Playwright scrapers for: Bailiff, Insolvency, Bank Israel, Liens, MoJ Publications

\- Background job orchestration (Celery)

\- Per-party report generation

\- \*\*Acceptance:\*\*

  \- Ron enters an address, gets back gush/chelka within 15 seconds

  \- Ron enters 2 Israeli IDs, gets back unified identity reports within 60 seconds

\- \*\*Why first:\*\* Both modules have zero authentication dependencies and validate the scraping infrastructure that all later sprints depend on.

\#\#\# Sprint 2 (Client Intake Form) — 2 weeks

\- Step 2 implementation

\- Public form with branching logic

\- Auto-save mechanism

\- Mobile-responsive design (60% will use phones)

\- Magic link delivery (email)

\- Lawyer-side form review screen

\- \*\*Acceptance:\*\* Ron sends link to a test client; client completes 15-question form on phone; data appears in case

\#\#\# Sprint 3 (Document Generation) — 2 weeks

\- Step 3 implementation

\- Tax calculator (2026 brackets, all scenarios)

\- Word template engine (docxtpl)

\- Template management UI

\- Generated documents stored in case folder

\- \*\*Acceptance:\*\* After intake submission, system auto-generates 5 documents within 10 seconds

\#\#\# Sprint 4 (Taboo \+ Condo Fetch with Payment Approval) — 2 weeks

The most critical sprint — now significantly simpler than v1.0 since no digital signature is required.

\- Steps 6 \+ 7 implementation

\- \*\*mekarkein-online.justice.gov.il scraping\*\* (no digital signature)

\- \*\*Push notification system for payment approval (Strategy A)\*\*

  \- Web push setup

  \- Mobile push (Capacitor or native iOS/Android wrapper)

  \- One-click approval flow with HMAC-signed links

\- \*\*Tranzila/Hyp payment vault integration\*\* (server-side card storage)

\- PDF parsing with Claude Vision

\- Cross-reference with intake data; flag mismatches

\- Sub-parcel matching using consolidated extract \+ condo plan

\- \*\*Acceptance:\*\* Ron triggers Taboo fetch; approves payment from push notification; PDFs \+ parsed data returned within 3 minutes total.

\*\*Reference implementation:\*\* \`taboo\_fetcher.py\`

\#\#\# Sprint 5 (Contract Review AI \+ Remaining Steps \+ Polish) — 2 weeks

Combined sprint to cover everything that remains.

\- \*\*Step 8 — Contract Review AI:\*\*

  \- Firm checklist configuration UI

  \- Contract upload \+ parsing

  \- Claude analysis against checklist

  \- Annotated Word output with tracked changes

\- \*\*Step 4 — Municipal check\*\* (manual checklist \+ GovMap)

\- \*\*Step 9 — Addenda tracking\*\*

\- \*\*Step 10 — Signing scheduling \+ calendar integration\*\*

\- Final polish, performance, bug fixes

\- Production deployment

\- Ron & Lev onboarding

\- \*\*Acceptance:\*\* Ron runs a real case end-to-end on the new platform

\#\#\# Post-Launch Phase 1

\- 4 weeks of intensive feedback iteration

\- Daily check-ins with Ron \+ Lev

\- Bug fixes and small improvements

\- \*\*Strategy B development decision point:\*\* After 4 weeks of Strategy A (push approval), assess whether full automation is worth the additional PCI compliance investment

\- Decision point: proceed to Phase 2 (post-signing) or expand Phase 1 features

---

## CHANGE 10 — Update Risks Table

### Where to update

Section 14 (Risks & Mitigations). Replace the digital signature risk and add a new payment risk.

### Find and replace

**Find:**

| Digital signature flow (Comsign) is complex | High | High | Spike sprint to validate approach; have phone-based approval as backup |

**Replace with:**

| Payment approval flow (Strategy A) creates friction | Medium | Medium | Track lawyer approval times; if \> 30 seconds avg or \> 10% missed approvals, accelerate Strategy B development |

| Government portal changes selectors/HTML | High | High | Comprehensive Sentry alerts on scraper failures; weekly automated health check tests; modular scrapers with clear failure modes |

### Also remove (find and delete this line):

| Government sites change HTML/break scrapers | High | High | Monitoring \+ Sentry alerts; modular scrapers; manual fallback always available |

(It's replaced by the more specific version above.)

---

## CHANGE 11 — Update Out of Scope

### Where to update

Section 15 (Out of Scope \- Phase 2+). Move digital signature from being implicit to explicit Phase 2 work.

### Find the Phase 2 section and update

**Find:**

\#\#\# Phase 2 (Post-Signing Workflow)

\- Steps 11–23: post-signing tasks (scanning to Legal, Landbit sync, cautionary note registration, tax filing, mortgage handling, payment tracking, handover)

\- Integration with Legal SQL Server

\- Integration with Landbit

\- Cautionary note submission to Taboo

\- Tax filing via Israeli Tax Authority's \`mereyatzaim\` system

**Replace with:**

\#\#\# Phase 2 (Post-Signing Workflow)

\- Steps 11–23: post-signing tasks (scanning to Legal, Landbit sync, cautionary note registration, tax filing, mortgage handling, payment tracking, handover)

\- \*\*Digital signature integration (Comsign/PersonalID smart card)\*\* — required for filing actions (cautionary notes, mortgage registration, sale transactions)

\- Integration with Legal SQL Server

\- Integration with Landbit

\- Cautionary note submission to Taboo

\- Tax filing via Israeli Tax Authority's \`mereyatzaim\` system

\- \*\*Strategy B — Full payment automation\*\* (replacing Strategy A push approval with stored-card vault)

---

## CHANGE 12 — Update Open Questions

### Where to update

Appendix C — Open Questions Requiring Ron's Input.

### Remove these questions (now resolved):

- Question 1: Digital signature method — RESOLVED (Ron has smart card on USB, but Phase 1 doesn't need it)

### Update Question 7

**Find:**

7\. \*\*Hosting jurisdiction:\*\* Strong preference for Israeli hosting (Kamatera) vs EU (cheaper, more reliable)?

**Replace with:**

7\. \*\*Payment processor preference:\*\* Tranzila vs Hyp vs other Israeli PCI-compliant vault? Ron's accountant may have a preference based on existing firm relationships.

### Add new question

9\. \*\*GovMap API token:\*\* Ron needs to register at https://api.govmap.gov.il and obtain a free API token before Sprint 1\. This is a one-time, 5-minute task.

10\. \*\*Firm's payment card:\*\* Which card will be used for Taboo extracts (\~₪30 per case)? Should it be a dedicated business card with appropriate spending limits, or the firm's primary card? Accountant input recommended.

---

## How to Apply These Changes

### Option 1: Manual edits to PRD.md

Open `PRD_Phase1_Pre-Signing.md` and apply each change in order. Most changes are explicit find-and-replace; some are additions.

### Option 2: Feed delta to Claude Code

Give Claude Code both files:

- The original `PRD_Phase1_Pre-Signing.md`  
- This delta document

Then instruct: *"Apply all changes from the delta document to PRD\_Phase1\_Pre-Signing.md. After applying, increment the document version from 1.0 to 1.1 and update the date to today."*

### Option 3: Apply only specific changes

If you want to roll out changes incrementally, apply by severity:

- **High severity first:** Changes 1, 2, 3, 5, 9  
- **Medium severity next:** Changes 6, 7, 8, 10  
- **Low severity last:** Changes 4, 11, 12

---

## Sanity Check After Applying

After all changes are applied, verify:

- [ ] Section 0.5 exists and explains Israeli hosting requirement  
- [ ] Step 5.5 (Address Resolver) is between Steps 5 and 6  
- [ ] Step 6 makes no mention of digital signature (mentioned only in Phase 2 context)  
- [ ] Sprint count is now 5 sprints (was 6\) \+ Sprint 0 \= 6 total  
- [ ] Sprint 1 is "Address Resolver \+ Identity Check" combined  
- [ ] Data model includes `AddressResolution` entity  
- [ ] API design includes `/api/cases/:id/resolve-address`  
- [ ] Risks table mentions payment approval flow, not digital signature  
- [ ] Out of Scope explicitly mentions digital signature as Phase 2  
- [ ] Open Questions include GovMap token and payment processor selection

---

**End of Delta Document**

Document version: 1.0 (this delta) Applies to: PRD v1.0 → v1.1 Author: Generated from live discovery session, June 2026  
