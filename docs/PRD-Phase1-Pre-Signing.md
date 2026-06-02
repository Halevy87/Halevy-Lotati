# Product Requirements Document

## Pre-Contract Real Estate Due Diligence Platform

### For Halevi-Luttati Law Office

**Document Version:** 1.0 **Date:** May 2026 **Phase:** Phase 1 — Pre-Signing Workflow (Steps 1–10) **Status:** Ready for development

## Table of Contents

0.  [<u>⚠️ Critical: Language & Localization</u>](#0-critical-language--localization)

1.  [<u>Executive Summary</u>](#1-executive-summary)

2.  [<u>Product Vision & Goals</u>](#2-product-vision--goals)

3.  [<u>Users & Personas</u>](#3-users--personas)

4.  [<u>Scope: What's In, What's Out</u>](#4-scope-whats-in-whats-out)

5.  [<u>The 10 Pre-Signing Steps — Detailed Specs</u>](#5-the-10-pre-signing-steps--detailed-specs)

6.  [<u>System Architecture</u>](#6-system-architecture)

7.  [<u>Tech Stack</u>](#7-tech-stack)

8.  [<u>Data Models</u>](#8-data-models)

9.  [<u>API Design</u>](#9-api-design)

10. [<u>UI/UX Specifications</u>](#10-uiux-specifications)

11. [<u>Security, Privacy & Compliance</u>](#11-security-privacy--compliance)

12. [<u>Development Roadmap</u>](#12-development-roadmap)

13. [<u>Success Metrics</u>](#13-success-metrics)

14. [<u>Risks & Mitigations</u>](#14-risks--mitigations)

15. [<u>Out of Scope (Phase 2+)</u>](#15-out-of-scope-phase-2)

## 0. ⚠️ Critical: Language & Localization

> **This section is non-negotiable and overrides any defaults the developer might apply.**

### The product is a Hebrew-first application built for an Israeli law firm.

This PRD is written in English so the developer (or AI coding assistant) can read it. **The product itself is entirely in Hebrew, RTL.** This is not a feature, it is the foundational assumption that drives every UI, content, and infrastructure decision.

### Language Rules

| **Surface** | **Language** |
|----|----|
| All user-facing UI text (labels, buttons, headings, menus) | **Hebrew** |
| All form labels, placeholders, validation messages | **Hebrew** |
| All toast notifications, error messages, confirmations | **Hebrew** |
| All email templates sent to clients | **Hebrew** |
| All WhatsApp/SMS messages to clients | **Hebrew** |
| All generated documents (Word, PDF) | **Hebrew** |
| All date/time formats | Israeli locale (he-IL) — DD/MM/YYYY |
| All currency formats | Israeli Shekel with proper formatting (₪1,234,567) |
| All number formats | Israeli locale (comma thousands, period decimal) |
| Activity log display strings | **Hebrew** |
| AI prompts for analyzing Hebrew documents | English instructions, Hebrew content |
| AI output to be shown to lawyer | **Hebrew** |
| Code, comments, variable names, commit messages | English (developer-facing) |
| API field names | English (developer-facing) |
| Database column names | English (developer-facing) |
| Internal logs and error tracing | English (developer-facing) |
| Documentation (README, internal docs) | English (developer-facing) |

### RTL (Right-to-Left) Requirements

**Every screen, every component, every interaction must work natively in RTL.** This is not an afterthought.

1.  **HTML root must declare dir="rtl" and lang="he"**

2.  **Tailwind CSS must use the official RTL plugin** (tailwindcss-rtl) OR use logical properties (ms-\*, me-\*, ps-\*, pe-\*) instead of directional ones (ml-\*, mr-\*, pl-\*, pr-\*)

3.  **shadcn/ui components must be RTL-tested** — many components need adjustment. Specifically validate:

    - Dropdowns and select menus (chevron direction, alignment)

    - Date pickers (calendar layout)

    - Sliders and progress bars (direction of fill)

    - Tooltips (positioning)

    - Toast notifications (slide-in direction)

    - Dialog/modal close buttons (positioning)

4.  **Icons that imply direction must flip** — back arrows, chevrons, "next/previous" indicators

5.  **Numbers and Latin text within Hebrew strings** must use proper bidi handling (use \<bdi\> element or CSS unicode-bidi: isolate where needed)

6.  **Mixed-direction content** (e.g., "<span dir="rtl">תיק</span> \#2026-0042" or "<span dir="rtl">כתובת</span>: 5 Rothschild Ave") needs careful handling — numbers and English should not break the Hebrew flow

7.  **Form layouts** — labels right-aligned, fields right-aligned, required indicators (\*) on the left of the label visually

8.  **Tables** — first column on the right, last column on the left

9.  **Sidebar/drawer panels** — slide in from the right by default (not left)

10. **Breadcrumbs** — read right to left: <span dir="rtl">דשבורד ← תיק 2026-0042 ← שלב</span> 5

### Font Requirements

**Primary fonts (must be loaded with Hebrew subsets):**

- **Display font:** Frank Ruhl Libre (Hebrew serif) — for headings and brand

- **Body font:** Heebo (Hebrew sans-serif) — for body text and UI

Both available via Google Fonts. Must explicitly include Hebrew character subset:

\<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&family=Frank+Ruhl+Libre:wght@400;500;700&display=swap&subset=hebrew" rel="stylesheet"\>

**Fallback stack:** System Hebrew fonts ('Segoe UI', 'Arial Hebrew', sans-serif)

**Do NOT use:** Arial, Inter, Roboto, Times New Roman, or other generic Latin-first fonts as primary — they handle Hebrew but look generic and unprofessional in an Israeli legal context.

### Content Creation Workflow

Since the developer building this may not be a native Hebrew speaker:

1.  **All Hebrew copy must be sourced from the firm or stored in a strings file** — never machine-translated on the fly

2.  **Create a centralized messages/he.json file** with all UI strings, indexed by key

3.  **Use a Hebrew-aware i18n library** — recommended: next-intl for Next.js

4.  **Reference the demo HTML file** (halevi_luttati_demo.html) for the exact Hebrew copy already approved — reuse these strings verbatim

5.  **When in doubt, leave a placeholder and ask the firm** — never guess Hebrew copy

### Examples of Approved Hebrew Copy (from the demo)

| **English**                 | **Hebrew**                                  |
|-----------------------------|---------------------------------------------|
| Dashboard                   | <span dir="rtl">לוח עבודה</span>            |
| Active Cases                | <span dir="rtl">תיקים פעילים</span>         |
| New Case                    | <span dir="rtl">תיק חדש</span>              |
| Open case                   | <span dir="rtl">פתיחת תיק</span>            |
| Client                      | <span dir="rtl">לקוח</span>                 |
| Counterparty                | <span dir="rtl">צד שני</span>               |
| Status                      | <span dir="rtl">סטטוס</span>                |
| Progress                    | <span dir="rtl">התקדמות</span>              |
| Next action                 | <span dir="rtl">הפעולה הבאה</span>          |
| Pre-signing phase           | <span dir="rtl">שלב 1 · לפני החתימה</span>  |
| Block / Parcel / Sub-parcel | <span dir="rtl">גוש / חלקה / תת חלקה</span> |
| Property value              | <span dir="rtl">שווי העסקה</span>           |
| Purchase tax                | <span dir="rtl">מס רכישה</span>             |
| Mortgage                    | <span dir="rtl">משכנתא</span>               |
| Handover date               | <span dir="rtl">מסירת חזקה</span>           |
| Red flag                    | <span dir="rtl">דגל אדום</span>             |
| Requires attention          | <span dir="rtl">דורש עיון</span>            |
| Completed                   | <span dir="rtl">הושלם / בוצע</span>         |
| Pending                     | <span dir="rtl">ממתין</span>                |
| In progress                 | <span dir="rtl">פעיל / בביצוע</span>        |
| Clean                       | <span dir="rtl">תקין / נקי</span>           |
| Warning                     | <span dir="rtl">אזהרה</span>                |
| Automatic                   | <span dir="rtl">אוטומטי</span>              |
| Manual                      | <span dir="rtl">ידני</span>                 |
| Recent activity             | <span dir="rtl">פעילות אחרונה</span>        |
| Document                    | <span dir="rtl">מסמך</span>                 |
| Land registry (Taboo)       | <span dir="rtl">טאבו / נסח טאבו</span>      |
| Identity check              | <span dir="rtl">בדיקת זהות</span>           |
| Buyer                       | <span dir="rtl">קונה / רוכש</span>          |
| Seller                      | <span dir="rtl">מוכר</span>                 |
| Save                        | <span dir="rtl">שמירה</span>                |
| Cancel                      | <span dir="rtl">ביטול</span>                |
| Send                        | <span dir="rtl">שליחה</span>                |
| Upload                      | <span dir="rtl">העלאה</span>                |
| Download                    | <span dir="rtl">הורדה</span>                |
| View                        | <span dir="rtl">צפייה</span>                |
| Edit                        | <span dir="rtl">עריכה</span>                |
| Delete                      | <span dir="rtl">מחיקה</span>                |

### Testing Requirement

**A native Hebrew speaker (Ron) must review every UI screen before that screen ships.** No "we'll fix the Hebrew later" — Hebrew is a Day-1 requirement, not a translation pass.

### Browser Testing Matrix

All UI must be validated on:

- **Chrome Desktop** (primary lawyer browser)

- **Safari Desktop** (some lawyers use Mac)

- **Mobile Safari iOS** (60%+ of clients fill intake form on iPhone)

- **Mobile Chrome Android** (remaining client mobile traffic)

Each browser has different Hebrew font rendering quirks. The intake form especially needs careful validation on mobile Safari, where text-input direction can flip unexpectedly.

## 1. Executive Summary

### The Problem

Real estate lawyers in Israel manually perform 10+ pre-contract due diligence checks for every property transaction. Each transaction requires 2–4 hours of repetitive work: pulling Land Registry (Taboo) extracts, checking liens and bankruptcy registries, calculating purchase tax, generating templated documents, and reviewing draft contracts. This work is delegated across multiple government websites with no unified workflow, no audit trail, and high error potential — yet errors can cost clients hundreds of thousands of shekels.

### The Solution

A web platform that automates the pre-contract due diligence workflow end-to-end. The lawyer opens a new case, enters minimal property and party details, and the system:

- Sends an intake form to the client to collect 15+ structured details

- Automatically pulls Taboo extracts, liens registry, bankruptcy, restricted-debtor, and bank-Israel records

- Calculates purchase tax based on the client's situation

- Generates the document package (KYC, intake checklist, calculations)

- Runs AI-powered review of incoming contract drafts against firm checklists

- Flags red flags and tracks each step with full audit trail

### Phase 1 Scope (This PRD)

Build the pre-signing workflow only — the 10 steps that happen *before* the parties sign. This is the highest-value, lowest-risk slice of the full transaction lifecycle. Phase 2 (post-signing) and Phase 3 (post-handover) are out of scope here.

### Why Phase 1 First

1.  **Highest ROI per step** — pre-signing has the most repetitive checks and the strongest automation potential (8 of 10 steps are fully or partially automatable)

2.  **Lowest legal risk** — outputs are reports and drafts that the lawyer reviews before any binding action

3.  **No Legal (CRM) integration required initially** — phase 1 sits *next to* the Legal system, not inside it

4.  **Faster time-to-value** — first 3 modules can deliver value within 4 weeks

### Success Definition

A successful Phase 1 lets Ron complete the pre-signing checklist for a typical residential purchase in **30 minutes of his time** instead of **3–4 hours**, while producing a more thorough and consistently formatted output than the manual process.

### Critical Reminder

**This PRD is in English. The product is in Hebrew (RTL). See Section 0 for non-negotiable localization requirements that apply throughout the build.**

## 2. Product Vision & Goals

### Vision Statement

The pre-contract due diligence platform becomes the lawyer's command center for every real estate transaction at Halevi-Luttati. Instead of juggling government websites, Word templates, and email threads, the lawyer drives the entire pre-signing workflow from a single interface, with automation handling the repetitive work and AI surfacing the issues that need human judgment.

### Strategic Goals (Phase 1)

| **Goal** | **Metric** | **Target** |
|----|----|----|
| Reduce lawyer time per case | Hours per pre-signing workflow | From 3–4h → 30min |
| Catch issues before signing | Red flags identified per case | ≥ 1.5x current rate |
| Standardize output quality | Variance between cases | All cases produce identical-format reports |
| Build foundation for Phase 2 | Reusable infrastructure | Data models support post-signing workflow |
| Validate market direction | Lawyer satisfaction | Ron + Lev report willingness to pay \>₪1500/mo |

### Non-Goals (Phase 1)

- Replacing the Legal (CRM) system

- Replacing Landbit (post-signing client communication)

- Building a client-facing portal beyond the intake form

- Supporting commercial real estate (residential only)

- Supporting multi-jurisdictional transactions

## 3. Users & Personas

### Primary User: Ron (The Senior Lawyer)

- **Role:** Partner, real estate attorney

- **Tech proficiency:** Moderate — comfortable with web apps, but not a developer

- **Daily workflow:** 10–15 active cases at various stages

- **Pain points:** Repetitive manual checks, fear of missing a red flag, time pressure from multiple cases

- **Goals:** Reduce time per case, increase confidence in due diligence, scale practice without hiring

### Secondary User: Lev (The Partner)

- **Role:** Partner, similar real estate focus

- **Same workflow as Ron** — both partners use the system for their respective caseloads

- **Permissions:** Equal to Ron; can view all firm cases

### Tertiary User: The Client (Buyer/Seller)

- **Role:** End client purchasing or selling property

- **Tech proficiency:** Varies wildly (25–70 years old)

- **Interaction:** Receives a single intake form link via email/WhatsApp, fills it on phone or desktop

- **Does NOT log into the system** — intake form is the only client-facing surface in Phase 1

### Out of Scope Personas (Phase 1)

- Paralegals / interns (no junior staff at the firm currently)

- Counterparty lawyers (we do not integrate with their workflows)

- Court/government clerks (no direct integration with their systems beyond scraping)

## 4. Scope: What's In, What's Out

### In Scope (Phase 1)

The 10 sequential steps that happen between a client signing a representation agreement and the parties signing the purchase contract:

| **\#** | **Step**                             | **Automation Level** |
|--------|--------------------------------------|----------------------|
| 1      | Fee payment + case creation          | Full                 |
| 2      | Client intake form (15+ questions)   | Full                 |
| 3      | Document package preparation         | Full                 |
| 4      | Municipal/planning check             | Partial              |
| 5      | Identity & risk check (both parties) | Full                 |
| 6      | Land Registry (Taboo) extracts       | Full                 |
| 7      | Condominium file retrieval           | Full                 |
| 8      | Draft contract review                | AI-assisted          |
| 9      | Negotiation & addenda collection     | Manual + tracking    |
| 10     | Signing date coordination            | Manual + tracking    |

### Out of Scope (Phase 1)

- All post-signing workflow (steps 11–29)

- Direct integration with the Legal CRM system

- Direct integration with Landbit

- Multi-firm support (single tenant only)

- Mobile native apps (responsive web only)

- Internationalization beyond Hebrew + minimal English UI

- Public marketing site

## 5. The 10 Pre-Signing Steps — Detailed Specs

Each step is specified with: trigger, inputs, automated actions, manual actions, outputs, acceptance criteria, and external dependencies.

### Step 1: Fee Payment & Case Creation

**Trigger:** Lawyer initiates a new case from the dashboard.

**Inputs:**

- Deal type (purchase / sale / exchange)

- Property identifiers (block / parcel / sub-parcel — *gush, chelka, tat-chelka*)

- Property address (street, building, apartment, city)

- Primary client name + Israeli ID + phone + email

- Counterparty representative (lawyer name + contact)

- Engagement fee amount

**Automated Actions:**

- Generate unique case ID (format: YYYY-NNNN)

- Create case record in database

- Send engagement letter template to lawyer for review

- Create folder structure in document storage

- Log activity: "Case opened"

**Manual Actions:**

- Lawyer reviews & sends engagement letter to client

- Client pays (out of system — bank transfer / check / credit)

- Lawyer marks payment received

**Outputs:**

- Case record with status intake_pending

- Auto-generated engagement letter (Hebrew Word doc)

- Empty document folder

**Acceptance Criteria:**

- Case creation takes \< 60 seconds from lawyer opening the modal

- All Hebrew text renders correctly RTL

- Engagement letter populates with client name, property details, fee, date

**External Dependencies:** None.

### Step 2: Client Intake Form

**Trigger:** Case created with status intake_pending. Lawyer clicks "Send intake form to client".

**Inputs:**

- Pre-populated client name and basic case info from Step 1

**Automated Actions:**

- Generate unique, time-limited link (valid 30 days)

- Send email + WhatsApp message to client with link

- Form auto-saves draft on every field change

- Branching logic: questions adapt based on previous answers

**Form Structure (15+ questions, branching):**

Section A: Property Ownership Status

- Is this your only residence? (Yes/No/Improving housing/Additional property)

- If "additional": how many properties do you currently own?

Section B: Inheritance Track

- Is this an inherited apartment? (Yes/No)

- If yes: was the deceased eligible for single-residence exemption when alive?

- If yes: what is the seller's portion (under/over 1.5 properties)?

Section C: Residency & Citizenship

- Are you an Israeli resident and citizen? (Yes/No)

- If no: which country?

Section D: Recent Sales

- When did you purchase the property being sold? (date)

- Have 18 months passed since occupancy certificate?

- Have you sold another property with single-residence exemption in the last 18 months?

Section E: Gifts & Marital Status

- Did you receive this property as a gift? (Yes/No + date)

- Marital status + prenuptial agreement? (single/married+prenup/married+no prenup/divorced)

Section F: Mortgage

- Are you taking a mortgage? (Yes/No)

- If yes: do you have a current in-principle approval? (Yes/No + upload)

- Liquid equity available (ILS)

Section G: Tenancy

- Are there current tenants? (Yes/No)

- If yes: upload tenant IDs and lease agreement; eviction date

Section H: Urban Renewal

- Is the building in urban renewal proceedings? (Yes/No)

- If yes: which developer/company?

Section I: Special Conditions

- Handover date

- What stays in the property (appliances, fixtures, etc.)

- Known issues (leaks, etc.)

- Known building violations or inspection alerts

- Additional building rights known

- Is this a garden apartment or penthouse?

**Manual Actions:**

- Client fills form on their own time

- Lawyer can view real-time progress

- Lawyer can manually edit any field after submission

**Outputs:**

- Structured JSON intake record

- PDF snapshot of completed form (for case file)

- Triggers Step 3 automatically on submission

**Acceptance Criteria:**

- Form is fully mobile-responsive (60%+ of clients will complete on phone)

- Hebrew RTL works correctly on iOS Safari and Android Chrome

- Auto-save prevents data loss

- Conditional logic correctly hides/shows questions

- Lawyer receives notification when client submits

**External Dependencies:**

- Email delivery service (e.g., Resend, Postmark)

- WhatsApp Business API (or fallback to email-only for MVP)

### Step 3: Document Package Preparation

**Trigger:** Client submits intake form in Step 2.

**Inputs:**

- Completed intake form data (JSON)

- Property details from case record

**Automated Actions:**

- Calculate purchase tax (mas rechisha) using 2026 brackets:

  - Single residence: progressive 0% → 8% → 10%

  - Additional residence: 8% / 10%

  - Improving housing: special calculation with 18-month exemption rule

  - Olim (new immigrants): special brackets

- Generate document set from templates:

  1.  **Engagement checklist** (Tzek list shlavei heskem ha'mekher)

  2.  **KYC form** (tofes haker et ha'lakoach)

  3.  **Tax calculation memo** (tachshiv mas rechisha)

  4.  **Client billing for fees** (pratei chiuv lakoach la'agarot)

  5.  **ID copies** (from uploads in intake form)

<!-- -->

- Save all documents to case folder

- Mark Step 3 as complete

**Manual Actions:**

- Lawyer reviews tax calculation (optional override)

- Lawyer reviews generated documents

**Outputs:**

- 5 Word documents in case folder

- Tax calculation result displayed in case header

- Activity log entry

**Acceptance Criteria:**

- Tax calculation matches official Israel Tax Authority calculator within 1 ILS

- All Hebrew text in generated documents renders correctly

- Templates use the firm's standard formatting (letterhead, fonts)

- Generation completes in \< 10 seconds

**External Dependencies:**

- Up-to-date tax bracket data (manually maintained config, updated annually)

### Step 4: Municipal & Planning Check

**Trigger:** Manual — lawyer clicks "Run municipal check" on Step 4.

**Inputs:**

- Property block / parcel / sub-parcel

- City name

**Automated Actions:**

- Query GovMap for the parcel (unofficial API)

- Retrieve aerial imagery

- Search for active plans / *tochniyot* in the area

- Compare condominium plan (from Step 7 — may run later) with aerial imagery using vision AI

- Check for known violations from publicly accessible municipal data

**Manual Actions (Lawyer must do these):**

- Visit the relevant municipality's website to check the building file

- Verify the building permit / Form 4 / completion certificate status

- Check for active inspection alerts

- Confirm betterment levy (heitel hashbacha) status

- Take screenshots and upload to case folder

**Outputs:**

- GovMap report (PDF)

- AI-flagged potential discrepancies between plan and aerial view

- Manual lawyer notes section

- Status: OK / requires attention / red flag

**Acceptance Criteria:**

- GovMap scraping completes within 30 seconds

- AI vision analysis correctly identifies at least common discrepancies (extensions, enclosed balconies)

- Lawyer can upload manual screenshots and notes

- Output is captured in standardized report format

**External Dependencies:**

- GovMap (unofficial API — fragile, must monitor for changes)

- Anthropic Claude Vision API for aerial comparison

**Priority Note:** This step is the most complex and most fragile. For the first MVP, we may ship with **GovMap query + manual checklist only**, deferring the AI vision comparison to a v1.1.

### Step 5: Identity & Risk Check (Both Parties)

**Trigger:** Automatic — fires when Step 2 (intake) completes; manual re-run available.

**Inputs:**

- Israeli IDs of all buyers, all sellers, and any guarantors

**Automated Actions:**

- Query each of the following per party:

  1.  **Bailiff Office** (hotzaa lapoal) — restricted debtor status

  2.  **Insolvency Authority** (memuneh chadalut peraon) — bankruptcy proceedings

  3.  **Bank of Israel** — restricted bank account status

  4.  **Liens Registry** (rasham hamishkonot) — active liens against the person

  5.  **Ministry of Justice publications** — probate orders, insolvency notices

<!-- -->

- Cross-reference results

- Generate unified per-party report

**Manual Actions:**

- Lawyer reviews any red flags

- If issues found, lawyer contacts party for explanation

**Outputs:**

- One PDF report per party (5 source checks each)

- Status flag per party: clean / warning / red flag

- Activity log entry per source

**Acceptance Criteria:**

- All 5 sources checked in parallel

- Total run time \< 60 seconds for a 2-party transaction

- PDF reports include source URLs and timestamps for evidentiary value

- Any access failures are clearly logged (don't silently fail)

**External Dependencies:**

- 5 government websites (all publicly accessible without lawyer credentials)

- Headless browser infrastructure (Playwright)

**Priority Note:** This is the **highest-ROI module** to build first. All 5 sources are accessible without authentication, return fast results, and the value to the lawyer is immediate and clear.

### Step 6: Land Registry (Taboo) Extracts

**Trigger:** Manual — lawyer clicks "Pull Taboo extracts".

**Inputs:**

- Property block / parcel / sub-parcel

- Lawyer's digital signature certificate (smart card or remote certificate)

- Lawyer's pre-loaded billing method (for the ₪15 per extract fee)

**Automated Actions:**

- Authenticate to Israeli Government Payment Service using lawyer's credentials

- Request:

  1.  **Consolidated extract** (nesach merukaz) — full picture of all rights

  2.  **Detailed extract** (nesach pratani) — specific sub-parcel

<!-- -->

- Pay ₪15 per extract (₪30 total)

- Download PDFs

- Parse extracts to extract structured data:

  - Current owner(s) with ID numbers

  - Property dimensions

  - Active mortgages with creditor names and amounts

  - Cautionary notes (he'arot azhara)

  - Liens

  - Attached units (parking, storage)

  - Leasehold vs freehold status

<!-- -->

- Save PDFs to case folder

- Store structured data in database for cross-referencing in other steps

**Manual Actions:**

- Lawyer verifies parsed data matches intake form claims (auto-flagged if mismatched)

**Outputs:**

- 2 PDF extracts in case folder

- Structured property data in database

- Side-by-side comparison: client claims vs Taboo reality

- Flags for any mismatches

**Acceptance Criteria:**

- Authentication with smart card works reliably

- Payment processed without manual intervention

- PDF parsing extracts owner names with 99%+ accuracy

- All Hebrew characters correctly extracted

- Round-trip (request → PDF → parsed data) completes in \< 90 seconds

**External Dependencies:**

- Israeli Government Payment Service (shirut ha'tashlumim ha'memshalti)

- Smart card / digital signature (Comsign or PersonalID)

- Anthropic Claude Vision for PDF parsing fallback if structured extraction fails

**Critical Constraint:** The lawyer's digital signature is legally required for this step. The system must securely handle the signing credential — likely via a per-request signature workflow where Ron approves each fetch on his own device (Comsign mobile app or similar).

### Step 7: Condominium File Retrieval

**Trigger:** Manual — lawyer clicks "Pull condo file". Often run alongside Step 6.

**Inputs:**

- Same block / parcel as Step 6

- Lawyer's digital signature credentials

**Automated Actions:**

- Request from Government Payment Service:

  1.  **Condominium registration order** (tzav rishum)

  2.  **Building bylaws** (takanon)

  3.  **Building plan** (tashrit) — typically PDF with floor plans

<!-- -->

- Parse documents:

  - Identify all units in the building

  - Identify which auxiliary spaces (parking, storage) are attached to which units

  - Extract building bylaws restrictions (rental limits, modification rules)

<!-- -->

- Cross-reference with intake claims (e.g., "parking \#12 and storage \#4 belong to apt 4")

**Manual Actions:**

- Lawyer reviews bylaws for unusual restrictions

- Lawyer verifies attachment claims against actual plan

**Outputs:**

- 3 PDFs in case folder

- AI-extracted attachment map

- Flagged bylaw restrictions (rental limits, modification approvals required, etc.)

- Status: OK / requires attention

**Acceptance Criteria:**

- Floor plan parsing identifies attached units with 90%+ accuracy

- Bylaw analysis surfaces non-standard restrictions

- Total cost ≤ ₪45 per case (3 documents × ₪15)

**External Dependencies:**

- Same as Step 6

- Anthropic Claude Vision for floor plan analysis

### Step 8: Draft Contract Review

**Trigger:** Manual — lawyer uploads a draft contract received from counterparty.

**Inputs:**

- Draft contract (Word or PDF)

- Firm's standard contract checklist (configured per-firm, can be updated)

**Automated Actions:**

- Parse contract document

- Run Claude analysis against the firm's checklist (~14 standard clauses)

- For each clause, classify:

  - **Present and standard** — matches firm's preferred language

  - **Present but non-standard** — needs review

  - **Missing** — clause not found

  - **Concerning** — language that benefits counterparty / risks client

- Generate annotated contract with comments

- Generate summary report with top 3–5 issues to address

**Manual Actions:**

- Lawyer reviews each flagged clause

- Lawyer decides on negotiation strategy

- Lawyer iterates with counterparty (out of system in Phase 1)

**Outputs:**

- Annotated contract (Word with tracked changes / comments)

- Summary issue list

- Issues are linked to case record

**Acceptance Criteria:**

- Document parsing handles both .docx and .pdf

- Claude correctly identifies all 14 standard clauses in 90%+ of cases

- Output is the lawyer's actual annotated draft, not a summary

- Lawyer can override AI classification per clause

**External Dependencies:**

- Anthropic Claude API (Sonnet 4.5)

- python-docx for Word manipulation with tracked changes

**Priority Note:** This is the highest-value AI feature in the system. Even if accuracy is imperfect, surfacing issues for lawyer review is more valuable than missing them. Build with explicit "AI suggestion, please verify" framing.

### Step 9: Negotiation & Addenda Collection

**Trigger:** Manual — lawyer progresses Step 8 to Step 9 when contract review is done.

**Inputs:**

- Final draft (after negotiations)

- Required addenda based on intake answers:

  - Mortgage in-principle approval (if buyer is taking mortgage)

  - Spousal consent (if married + no prenup)

  - Absence-of-spouse affidavit (if single but property could be community property)

  - Most recent property tax (arnona) bill

  - Letter of intent or leasehold agreement (if applicable)

  - Counterparty's IDs

**Automated Actions:**

- Checklist of required documents based on intake answers

- Track which documents have been received vs pending

- Auto-categorize uploaded documents using AI

**Manual Actions:**

- Lawyer chases counterparty for missing documents

- Lawyer uploads documents as received

- Negotiation itself happens out-of-system (email/phone)

**Outputs:**

- Document completeness checklist

- All required addenda in case folder

**Acceptance Criteria:**

- Required document list correctly derives from intake answers

- Uploaded documents are correctly categorized by AI

- Lawyer can manually re-categorize

**External Dependencies:** Minimal — primarily a tracking step.

### Step 10: Signing Date Coordination

**Trigger:** Manual — lawyer initiates when contract and addenda are finalized.

**Inputs:**

- Proposed signing date and time

- All parties' contact info

**Automated Actions:**

- Generate pre-signing checklist for the lawyer:

  - All parties confirmed

  - Bank check (shek bankai) amount confirmed with buyer

  - ID verification reminder

  - Spousal consent (if needed)

  - Updated mortgage approval (within validity window)

- Send calendar invites to all parties (or push to lawyer's calendar — Outlook/Google)

- Send pre-meeting reminders (24h and 2h before)

**Manual Actions:**

- Lawyer confirms signing date with all parties

- Lawyer briefs the client on what to bring

**Outputs:**

- Calendar event(s) created

- Reminder notifications sent

- Case status updated to signing_scheduled

**Acceptance Criteria:**

- Calendar integration works for at least Google Calendar (Outlook in Phase 2)

- Reminders are correctly timed

- Pre-signing checklist is complete before signing

**External Dependencies:**

- Google Calendar API

- Email delivery for reminders

## 6. System Architecture

### High-Level Architecture

┌─────────────────────────────────────────────────────────────┐

│ Frontend (Next.js) │

│ Lawyer Dashboard │ Case Detail │ Client Intake Form │

└──────────────────────────┬──────────────────────────────────┘

│ REST + WebSocket

▼

┌─────────────────────────────────────────────────────────────┐

│ API Layer (FastAPI) │

│ Auth │ Cases │ Steps │ Documents │ Notifications │

└──────┬──────────────────────────────┬───────────────────────┘

│ │

▼ ▼

┌─────────────────┐ ┌────────────────────┐

│ PostgreSQL │ │ Background Jobs │

│ Cases, Users │◄────────│ (Celery + Redis) │

│ Documents │ │ Scraping, AI, │

│ Activity Log │ │ Document Gen │

└─────────────────┘ └─────────┬──────────┘

│

▼

┌───────────────────────────────────────┐

│ External Services │

├───────────────────────────────────────┤

│ • Anthropic Claude API (AI analysis) │

│ • Google Vision API (Hebrew OCR) │

│ • Playwright (gov site scraping) │

│ • Israeli Govt Payment (Taboo) │

│ • Email + WhatsApp (notifications) │

│ • Google Calendar API │

└───────────────────────────────────────┘

┌───────────────────────────────────────┐

│ Storage │

│ • Document files (S3/R2) │

│ • Generated PDFs │

│ • Scraped extracts │

└───────────────────────────────────────┘

### Key Architectural Decisions

**1. Separation of frontend and backend**

- Why: Allows independent scaling, easier hiring (any TS dev / any Python dev)

- Frontend deployed to Vercel, backend to a dedicated container host

**2. Background jobs for all long-running work**

- Why: Government scraping can take 30–60 seconds; users shouldn't wait synchronously

- WebSocket pushes update the UI when jobs complete

- Failed jobs auto-retry with exponential backoff

**3. PostgreSQL with JSONB for flexible case data**

- Why: Case structure will evolve as we learn; rigid schemas create migration pain

- Core entities (cases, users, parties) are relational; per-step data is JSONB

**4. All sensitive PDFs encrypted at rest**

- Why: Compliance with Israel Privacy Protection Law

- AES-256 encryption with per-firm key

**5. No multi-tenancy in Phase 1**

- Why: Single firm = single deployment is simpler and more secure

- Phase 2 may introduce multi-tenancy if we go to market

## 7. Tech Stack

### Selection Rationale

Stack chosen to optimize for:

1.  **Speed of MVP delivery** (well-known, well-documented technologies)

2.  **AI workload support** (Python ecosystem for AI; TypeScript for typed frontend)

3.  **Hebrew/RTL support** (mature in modern web stacks)

4.  **Government scraping reliability** (real browser via Playwright)

5.  **Single-developer maintainability** (no exotic dependencies)

### Frontend

| **Technology** | **Version** | **Purpose** | **Why** |
|----|----|----|----|
| Next.js | 14+ (App Router) | React framework | SSR, streaming, file-based routing, Vercel-native |
| TypeScript | 5+ | Type safety | Catches bugs at compile time; essential for solo dev |
| Tailwind CSS | 3+ | Styling | Speed of development; consistency |
| **tailwindcss-rtl** | latest | RTL plugin for Tailwind | **Required — see Section 0**. Enables ms-\*, me-\* logical properties |
| **next-intl** | latest | Internationalization | **Required — see Section 0**. All UI strings in messages/he.json |
| shadcn/ui | latest | Component library | Copy-paste components; full customization; **must be RTL-validated per Section 0** |
| TanStack Query | 5+ | Data fetching & cache | Best-in-class server state management |
| React Hook Form | 7+ | Forms | Performant, great validation integration |
| Zod | 3+ | Schema validation | Shared schemas between FE and BE; supports Hebrew error messages |
| Lucide React | latest | Icons | Clean, consistent icon set; directional icons flipped automatically with RTL |

### Backend

| **Technology** | **Version** | **Purpose** | **Why** |
|----|----|----|----|
| Python | 3.11+ | Language | Best for AI/scraping ecosystem |
| FastAPI | latest | Web framework | Async-native, type-safe, automatic OpenAPI |
| Pydantic | 2+ | Data validation | Used by FastAPI; matches frontend Zod schemas |
| SQLAlchemy | 2+ | ORM | Mature, async support |
| Alembic | latest | Migrations | Standard for SQLAlchemy |
| Celery | 5+ | Background jobs | Battle-tested; works with Redis |
| Redis | 7+ | Job queue + cache | Standard with Celery |
| httpx | latest | HTTP client | Async, modern API |
| Playwright (Python) | latest | Browser automation | Best for modern JS-heavy government sites |

### AI & Document Processing

| **Service** | **Purpose** | **Why** |
|----|----|----|
| Anthropic Claude API (Sonnet 4.5) | Contract review, document classification, vision analysis | Best Hebrew comprehension; vision capability; long context |
| Google Cloud Vision API | Hebrew OCR | Best Hebrew OCR accuracy available |
| python-docx | Word document generation | Standard library; supports complex formatting |
| docxtpl | Templated Word generation | Cleaner than python-docx for template-based docs |
| WeasyPrint | PDF generation from HTML | Easier than ReportLab for complex layouts |
| pypdf | PDF parsing | Fast PDF text extraction |
| PyMuPDF (fitz) | PDF rendering | For rendering pages to images for Claude Vision |

### Database & Storage

| **Service**    | **Purpose**      | **Why**                                 |
|----------------|------------------|-----------------------------------------|
| PostgreSQL 15+ | Primary database | JSONB support, full-text search, proven |
| Cloudflare R2  | Document storage | S3-compatible, no egress fees, EU edge  |

### Infrastructure & DevOps

| **Service** | **Purpose** | **Why** |
|----|----|----|
| Vercel | Frontend hosting | Native Next.js support; Israel edge location |
| Fly.io OR Railway | Backend hosting | Container-based; good Docker support; affordable |
| Neon | Managed PostgreSQL | Generous free tier; automatic backups |
| Upstash | Managed Redis | Pay-per-request; perfect for low/medium volume |
| GitHub Actions | CI/CD | Standard; free for small repos |
| Sentry | Error monitoring | Industry standard; great Python + Next.js SDKs |

**Compliance Note on Hosting:** For Israeli compliance with the Privacy Protection Law, document storage must remain in Israel or an "adequate" jurisdiction (EU). Cloudflare R2 with EU region selected satisfies this. If we later need pure Israeli hosting, Kamatera is the standard option.

### Authentication

| **Technology** | **Purpose** | **Why** |
|----|----|----|
| Auth.js (NextAuth) | Authentication framework | Standard for Next.js |
| Email magic links | Login method | No passwords to manage |
| TOTP 2FA | Second factor | Required for handling sensitive data |

### External Integrations

| **Service** | **Purpose** |
|----|----|
| Resend | Transactional email |
| Twilio | WhatsApp Business API (Phase 2 if budget allows; email-only in MVP) |
| Google Calendar API | Signing date calendar events |
| GovMap | Planning data scraping (unofficial) |
| Israeli Govt Payment Service | Taboo extracts |
| Bailiff/Insolvency/Bank Israel/etc | Identity check scraping |

## 8. Data Models

### Core Entities

// User (firm staff)

User {

id: UUID

email: string (unique)

full_name: string

role: 'partner' \| 'lawyer' \| 'admin'

bar_license_number: string

digital_signature_id?: string // for Taboo access

created_at: timestamp

last_login_at: timestamp

is_active: boolean

}

// Case (the central entity)

Case {

id: UUID

case_number: string (unique, format: YYYY-NNNN)

status: CaseStatus // see enum below

current_step: integer (1-10)

// Property

block: string // gush

parcel: string // chelka

sub_parcel: string // tat chelka

property_address: string

property_city: string

// Deal

deal_type: 'purchase' \| 'sale' \| 'exchange'

deal_value_ils: integer?

// Assigned lawyer

primary_lawyer_id: UUID (FK User)

// Counterparty

counterparty_lawyer_name: string?

counterparty_lawyer_phone: string?

// Dates

opened_at: timestamp

signing_scheduled_at: timestamp?

handover_scheduled_at: timestamp?

closed_at: timestamp?

// Per-step data (JSONB)

intake_data: jsonb // Step 2 output

tax_calculation: jsonb // Step 3 output

municipal_check: jsonb // Step 4 output

identity_checks: jsonb // Step 5 output

taboo_data: jsonb // Step 6 output

condo_data: jsonb // Step 7 output

contract_review: jsonb // Step 8 output

addenda_checklist: jsonb // Step 9 output

// Computed

red_flags_count: integer (computed)

completion_percentage: integer (computed)

created_at: timestamp

updated_at: timestamp

}

enum CaseStatus {

intake_pending // Waiting for client to fill intake form

intake_complete // Form submitted, ready for automation

in_progress // Automation running / lawyer working

needs_attention // Red flags raised

signing_scheduled // Step 10 complete

signed // (end of Phase 1 scope)

archived

}

// Party (buyer / seller / guarantor on a case)

Party {

id: UUID

case_id: UUID (FK Case)

role: 'buyer' \| 'seller' \| 'guarantor' \| 'spouse'

full_name: string

israeli_id: string (encrypted)

phone: string

email: string

identity_check_status: 'pending' \| 'clean' \| 'warning' \| 'red_flag'

identity_check_results: jsonb // Step 5 per-party detail

created_at: timestamp

}

// Document (any file attached to a case)

Document {

id: UUID

case_id: UUID (FK Case)

type: DocumentType // see enum below

filename: string

storage_path: string // R2 key

mime_type: string

size_bytes: integer

source: 'uploaded' \| 'generated' \| 'scraped'

related_step: integer (1-10)

metadata: jsonb // extracted data, scan results

uploaded_by: UUID? (FK User)

created_at: timestamp

}

enum DocumentType {

engagement_letter

kyc_form

tax_calculation

client_id

intake_pdf

taboo_consolidated

taboo_detailed

condo_registration

condo_bylaws

condo_plan

identity_check_report

govmap_report

draft_contract

reviewed_contract

mortgage_approval

spousal_consent

arnona_bill

other

}

// Activity log (audit trail)

Activity {

id: UUID

case_id: UUID (FK Case)

user_id: UUID? (FK User)

type: ActivityType

description: string // Hebrew display string

metadata: jsonb // step \#, source, etc.

created_at: timestamp

}

enum ActivityType {

case_opened

step_started

step_completed

step_flagged

document_uploaded

document_generated

scraping_completed

scraping_failed

ai_analysis_completed

client_message_sent

client_message_received

red_flag_raised

note_added

}

// Intake form session (separate from Party, holds the client form state)

IntakeSession {

id: UUID

case_id: UUID (FK Case)

token: string (unique, used in URL)

expires_at: timestamp

status: 'sent' \| 'in_progress' \| 'submitted' \| 'expired'

draft_data: jsonb // auto-saved progress

submitted_data: jsonb? // final submission

submitted_at: timestamp?

ip_address: string? // for audit

created_at: timestamp

}

// Background job tracking

Job {

id: UUID

case_id: UUID? (FK Case)

type: JobType

status: 'pending' \| 'running' \| 'completed' \| 'failed'

payload: jsonb

result: jsonb?

error: string?

attempts: integer

created_at: timestamp

started_at: timestamp?

completed_at: timestamp?

}

enum JobType {

taboo_fetch

condo_fetch

identity_check

govmap_query

contract_analysis

document_generation

notification_send

}

## 9. API Design

### Authentication

POST /api/auth/login { email } → magic link sent

POST /api/auth/verify { token } → session

POST /api/auth/2fa/verify { code } → confirmed

POST /api/auth/logout → 204

GET /api/auth/me → User

### Cases

GET /api/cases?status=&page= → CasesList

POST /api/cases CreateCaseDto → Case

GET /api/cases/:id → CaseDetail (includes parties, docs, activity)

PATCH /api/cases/:id UpdateCaseDto → Case

DELETE /api/cases/:id → 204

GET /api/cases/:id/activity → Activity\[\]

GET /api/cases/:id/parties → Party\[\]

POST /api/cases/:id/parties CreatePartyDto → Party

PATCH /api/cases/:id/parties/:pid UpdatePartyDto → Party

### Steps (one endpoint per step's actions)

\# Step 1 — done implicitly at case creation

\# Step 2 — Intake Form

POST /api/cases/:id/intake/send → IntakeSession (creates link)

GET /api/intake/:token → IntakeForm (public, no auth)

PATCH /api/intake/:token PartialFormDto → 204 (auto-save)

POST /api/intake/:token/submit SubmitFormDto → 200

\# Step 3 — Document Package

POST /api/cases/:id/documents/generate-package → Job

\# Step 4 — Municipal Check

POST /api/cases/:id/checks/municipal → Job

\# Step 5 — Identity Checks

POST /api/cases/:id/checks/identity → Job

GET /api/cases/:id/checks/identity/:partyId → IdentityReport

\# Step 6 — Taboo Extracts

POST /api/cases/:id/taboo/fetch → Job (requires signature step)

POST /api/cases/:id/taboo/sign SignatureDto → 200 (callback from sign app)

\# Step 7 — Condo File

POST /api/cases/:id/condo/fetch → Job

\# Step 8 — Contract Review

POST /api/cases/:id/contract/upload multipart → Document

POST /api/cases/:id/contract/analyze :docId → Job

GET /api/cases/:id/contract/review → ContractReview

\# Step 9 — Addenda

GET /api/cases/:id/addenda/checklist → AddendaChecklist

POST /api/cases/:id/addenda/upload multipart → Document

\# Step 10 — Signing

POST /api/cases/:id/signing/schedule → CalendarEvent

GET /api/cases/:id/signing/checklist → PreSigningChecklist

### Documents

GET /api/cases/:id/documents → Document\[\]

POST /api/cases/:id/documents/upload multipart → Document

GET /api/documents/:id/download → file stream

DELETE /api/documents/:id → 204

### Jobs (status polling + WebSocket)

GET /api/jobs/:id → Job status

WS /ws/cases/:id → real-time updates

### Webhooks (external)

POST /webhooks/payment/taboo → Government payment confirmation

POST /webhooks/signature/comsign → Digital signature confirmation

### Conventions

- All responses are JSON

- Timestamps in ISO 8601 UTC

- All endpoints (except public intake) require auth

- Validation errors return 422 with field-level details

- Server errors return 500 with correlation ID for support

## 10. UI/UX Specifications

> **Reminder:** All UI text is in Hebrew, RTL. See Section 0 for non-negotiable localization rules. The wireframe examples and string examples below use English in this PRD for developer readability, but the actual implementation uses Hebrew throughout.

### Design Direction

- **Aesthetic:** Editorial Legal (refined, professional, paper-like)

- **Fonts:** Frank Ruhl Libre (display, Hebrew serif) + Heebo (body, Hebrew sans)

- **Palette:** Ink (#1a1d23), warm paper (#fafaf7), accent burgundy (#8b1538), gold accent (#a67c2e)

- **Layout:** Right-to-left primary; English headings allowed for tech-facing screens

- **Density:** Moderate — Israeli professionals expect information-dense interfaces, not airy SaaS

### Key Screens (Phase 1)

#### 10.1 Dashboard

- Header with firm logo + lawyer profile

- 4 KPI cards: Active cases, Checks completed this week, Needs attention, Signings this week

- Table of active cases:

  - Case number

  - Property address

  - Client name

  - Status badge

  - Progress bar (X/10 steps)

  - Next action label

  - Click → Case Detail

- "+ New Case" button (modal)

#### 10.2 New Case Modal

- Deal type selector

- Property identifiers (block / parcel / sub-parcel)

- Property address

- Client name + Israeli ID + phone + email

- Counterparty lawyer details

- "Open case and send intake form" button

#### 10.3 Case Detail

- Header: Case ID, property address, client name, counterparty, key dates, phase pill

- Timeline progress bar (10 segments, each clickable)

- Two-column layout:

  - **Left:** List of 10 step cards (collapsible)

    - Each card shows: step number, name, status icon, automation level badge, completion summary

    - Expanded view shows: actions, outputs, manual override

  - **Right sidebar:**

    - Red flags card (if any)

    - Deal details summary

    - Recent activity feed

    - Case team

#### 10.4 Client Intake Form (Public)

- Mobile-first responsive design

- Multi-section progressive form with progress indicator

- Branching logic (next questions depend on previous answers)

- Auto-save every 30 seconds + on blur

- Hebrew RTL primary

- Accessible (WCAG AA)

- File uploads for mortgage approval, tenant IDs, lease

#### 10.5 Step Detail Modals (per step type)

- Identity Check Report

- Taboo Data Viewer

- Contract Review with annotation

- Document package preview

### Navigation

- Top nav: Active cases / Clients / Templates / Archive / Settings

- Persistent breadcrumbs on case detail screens

- "Back to dashboard" link on all case screens

### States & Feedback

- Loading skeletons for all data fetches

- Toast notifications for completed actions

- Inline error messages for form validation

- "Run automation" buttons show spinner + estimated time

- WebSocket-driven real-time status updates (no manual refresh needed)

### Accessibility

- All interactive elements keyboard-accessible

- ARIA labels on icon-only buttons

- Color contrast meets WCAG AA (4.5:1 for text)

- Form errors announced to screen readers

## 11. Security, Privacy & Compliance

### Legal Framework

The system handles personal information about Israeli citizens under the **Protection of Privacy Law, 5741-1981** (PPL). This is more permissive than GDPR but still requires:

- Reasonable security measures

- Data minimization

- Purpose limitation

- Database registration (if applicable)

- Data subject rights (access, correction)

### Compliance Requirements

| **Requirement** | **Implementation** |
|----|----|
| Israeli IDs stored encrypted | AES-256-GCM at rest, separate key per record |
| Audit trail for all access | Activity log table, never deleted |
| Data stays in approved jurisdictions | All hosting in Israel or EU |
| Lawyer-client privilege preserved | No third-party access to case content |
| Right to erasure | Soft-delete with cryptographic shredding after 7 years (regulatory retention) |
| Database registration | If we reach 10,000+ data subjects, register with Privacy Protection Authority |

### Technical Security

**Authentication:**

- Magic-link login (no passwords stored)

- TOTP 2FA required for all lawyer accounts

- Session tokens with 12-hour idle expiry

- Refresh tokens stored httpOnly secure cookies

**Authorization:**

- Role-based access control (RBAC): partner / lawyer / admin

- All case data scoped to firm

- Public endpoints (intake form) are token-gated and time-limited

**Data Protection:**

- All connections over TLS 1.3

- Database encrypted at rest (Neon default)

- Document storage encrypted at rest (R2 default)

- Sensitive fields (Israeli IDs) encrypted at the application layer

- API keys and credentials in environment variables, never in code

**Operational Security:**

- Dependency scanning (Dependabot)

- SAST in CI (Semgrep)

- Sentry for production error monitoring (PII scrubbed)

- Database backups: daily, retained 30 days, tested quarterly

**Third-Party Risk:**

- Anthropic API: Zero Data Retention agreement required (case data flows to Claude)

- Google Vision: Data not retained per Google ToS for paid customers

- All vendors: contractual confidentiality + DPA where available

### Threat Model (Top Risks)

1.  **Compromised lawyer account** → 2FA mandatory; session expiry; audit log

2.  **Intake form link leaked** → Tokens are single-use-ready and expire in 30 days

3.  **Insider data exfiltration** → All document downloads logged; rate-limited

4.  **Government site changes break scraping** → Sentry alerts on scraping job failures

5.  **AI hallucinations in contract review** → All AI output labeled "AI suggestion, lawyer must verify"

## 12. Development Roadmap

### Sprint Structure

- 2-week sprints

- Sprint 0: Foundation (1 sprint)

- Phase 1 MVP: 6 sprints (12 weeks total)

- Each sprint targets ONE complete module to enable continuous feedback

### Sprint 0 (Foundation) — 2 weeks

- Project setup (FE + BE + DB + deployment pipeline)

- **Hebrew/RTL foundation set up from day one:**

  - \<html dir="rtl" lang="he"\> configured globally

  - tailwindcss-rtl plugin installed and configured

  - next-intl set up with messages/he.json

  - Hebrew fonts (Frank Ruhl Libre + Heebo) loaded with Hebrew subset

  - Israeli locale (he-IL) configured for dates, numbers, currency

  - shadcn/ui base components installed and RTL-validated

  - Test page proving end-to-end RTL works correctly on all target browsers

- Authentication (magic link + 2FA) — all UI in Hebrew

- Base data models (User, Case, Party, Document, Activity)

- Empty dashboard + case detail shell with Hebrew labels

- Basic case CRUD

- **Acceptance:** Ron can log in (Hebrew UI), create a case manually (Hebrew form), see it in the dashboard (Hebrew table). All Hebrew renders correctly RTL on Chrome, Safari, iOS Safari, Android Chrome.

### Sprint 1 (Identity & Risk Check) — 2 weeks

- Step 5 implementation: 5-source identity check

- Playwright scrapers for: Bailiff, Insolvency, Bank Israel, Liens, MoJ Publications

- Background job orchestration (Celery)

- Per-party report generation

- **Acceptance:** Ron enters 2 Israeli IDs, gets back unified reports within 60 seconds

- **Why first:** Highest ROI, no authentication dependencies, all 5 sources are public

### Sprint 2 (Client Intake Form) — 2 weeks

- Step 2 implementation

- Public form with branching logic

- Auto-save mechanism

- Mobile-responsive design (60% will use phones)

- Magic link delivery (email)

- Lawyer-side form review screen

- **Acceptance:** Ron sends link to a test client; client completes 15-question form on phone; data appears in case

### Sprint 3 (Document Generation) — 2 weeks

- Step 3 implementation

- Tax calculator (2026 brackets, all scenarios)

- Word template engine (docxtpl)

- Template management UI

- Generated documents stored in case folder

- **Acceptance:** After intake submission, system auto-generates 5 documents within 10 seconds

### Sprint 4 (Taboo + Condo Fetch) — 2 weeks

- Steps 6 + 7 implementation

- Israeli Government Payment Service integration

- Digital signature flow (Comsign or equivalent)

- PDF parsing with Claude Vision fallback

- Cross-reference with intake data; flag mismatches

- **Acceptance:** Ron triggers Taboo fetch; signs on his phone; PDFs + parsed data return within 90 seconds

### Sprint 5 (Contract Review AI) — 2 weeks

- Step 8 implementation

- Firm checklist configuration UI

- Contract upload + parsing

- Claude analysis against checklist

- Annotated Word output with tracked changes

- **Acceptance:** Ron uploads a draft contract; system returns annotated version with 3–5 flagged issues; Ron rates analysis quality

### Sprint 6 (Polish & Remaining Steps) — 2 weeks

- Step 4 (Municipal check — manual checklist + GovMap)

- Step 9 (Addenda tracking)

- Step 10 (Signing scheduling + calendar integration)

- Final polish, performance, bug fixes

- Production deployment

- Ron & Lev onboarding

- **Acceptance:** Ron runs a real case end-to-end on the new platform

### Post-Launch Phase 1

- 4 weeks of intensive feedback iteration

- Daily check-ins with Ron + Lev

- Bug fixes and small improvements

- Decision point: proceed to Phase 2 (post-signing) or expand Phase 1 features

## 13. Success Metrics

### Launch Metrics (End of Phase 1)

| **Metric** | **Target** |
|----|----|
| Cases handled through system | 5+ in first month |
| Average lawyer time per pre-signing | 30–45 minutes (down from 3–4h) |
| Automated steps that complete without error | 95%+ |
| Red flags caught per case | ≥ 1.5x manual baseline |
| Lawyer NPS | ≥ 8/10 |
| System uptime | 99%+ |

### Quality Gates Before Going Live

- All 10 step modules have automated tests

- Tax calculator validated against 20 hand-calculated examples

- Identity check accuracy validated against 10 known-state IDs (some clean, some flagged)

- Hebrew rendering tested across: Chrome, Safari, iOS Safari, Android Chrome

- Mobile intake form completion rate ≥ 70% on test users

- Lawyer can recover from any error state without contacting support

- Ron + Lev complete 3 real cases end-to-end in private beta before announcement

## 14. Risks & Mitigations

| **Risk** | **Likelihood** | **Impact** | **Mitigation** |
|----|----|----|----|
| Government sites change HTML/break scrapers | High | High | Monitoring + Sentry alerts; modular scrapers; manual fallback always available |
| Digital signature flow (Comsign) is complex | High | High | Spike sprint to validate approach; have phone-based approval as backup |
| AI contract review accuracy is too low | Medium | High | Always frame as "AI suggestion"; track accuracy; iterate prompts |
| Hebrew RTL breaks on edge case browsers | Medium | Medium | Cross-browser testing; CSS reset for RTL contexts |
| Ron/Lev resist process change | Medium | Critical | Continuous feedback loops; deliver value early; preserve manual override always |
| Israeli Privacy Authority audit | Low | Critical | Build with compliance from day 1; document everything |
| Anthropic API outage | Low | High | Graceful degradation; lawyer can proceed manually |
| Single-developer bus factor | Medium | High | Excellent docs in README; clean architecture; consider second dev after MVP |

## 15. Out of Scope (Phase 2+)

These are explicitly NOT being built in Phase 1, listed here so we don't accidentally creep:

### Phase 2 (Post-Signing Workflow)

- Steps 11–23: post-signing tasks (scanning to Legal, Landbit sync, cautionary note registration, tax filing, mortgage handling, payment tracking, handover)

- Integration with Legal SQL Server

- Integration with Landbit

- Cautionary note submission to Taboo

- Tax filing via Israeli Tax Authority's mereyatzaim system

### Phase 3 (Post-Handover)

- Steps 24–29: mortgage deed ordering, tax clearances, registration submission, follow-up verification, closing letters, physical file delivery

### Future Considerations

- Multi-tenant SaaS model (sell to other firms)

- Commercial real estate support

- Client-facing portal (beyond intake form)

- Mobile native apps

- Direct API integrations with banks

- Counterparty lawyer collaboration features

## Appendix A: Sample Test Cases for Phase 1

### Case A: Standard Purchase

- Buyer: first-time buyer, Israeli citizen

- Seller: 2 owners (couple), no liens, no flags

- Property: Tel Aviv apartment, no urban renewal

- Expected: Clean flow, all 10 steps complete in \<1 lawyer-hour

### Case B: Inherited Property Sale

- Sellers: 3 siblings (inherited)

- Buyer: improving housing, taking mortgage

- Property: Haifa apartment with building violation

- Expected: Red flag on Step 4 (violation); Step 5 requires probate verification; tax calc includes inheritance exemption

### Case C: Counterparty Identity Issue

- One seller has a restricted bank account

- Otherwise standard

- Expected: Step 5 raises red flag; case status changes to needs_attention; lawyer documents resolution before proceeding

### Case D: Garden Apartment with Encroachment

- Property: garden apartment in Ra'anana

- Aerial view shows extension into common area

- Expected: Step 4 (or Step 7) AI surfaces discrepancy; lawyer must verify with municipality before signing

## Appendix B: Module Build Order Justification

Why Identity Check (Step 5) before Intake Form (Step 2):

1.  **Identity Check has zero dependencies** — works with just an Israeli ID

2.  **Builds the scraping infrastructure** that other steps reuse

3.  **Validates the architecture** with the simplest possible module

4.  **Provides immediate standalone value** — Ron can use it even before the rest of the system is built (just enter an ID, get a report)

5.  **De-risks the hardest technical challenge** (government site automation) before betting more time

Intake Form is built second because:

1.  It's a prerequisite for Steps 3, 6, 7, 9

2.  Building it second means we can use insights from Step 1's user feedback to shape it

## Appendix C: Open Questions Requiring Ron's Input

These need answers before development begins:

1.  **Digital signature method:** Does Ron have a Comsign smart card or another digital signature method? What's the model?

2.  **Geographic focus:** What are the 3–5 cities where Ron handles the most cases? (Drives municipal scraping priorities for Step 4)

3.  **Volume:** How many pre-signing workflows does Ron handle per month on average?

4.  **Templates:** Can Ron provide the firm's current Word templates for engagement letter, KYC, etc.?

5.  **Examples:** Can Ron provide 5 anonymized historical contracts and their corresponding red flags? (For Step 8 AI training data)

6.  **Brand:** What's the firm's preferred name and logo? (Currently using "Halevi · Luttati" as placeholder)

7.  **Hosting jurisdiction:** Strong preference for Israeli hosting (Kamatera) vs EU (cheaper, more reliable)?

8.  **Landbit pricing/API:** What does Ron pay for Landbit? Do they offer API access? (Determines Phase 2 integration approach)

**End of PRD**

This document represents the complete specification for Phase 1 development. All decisions, scope changes, and clarifications during development should be tracked in a separate decision log and folded into v2 of this document at Phase 1 completion.
