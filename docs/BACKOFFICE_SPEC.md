# Backoffice Admin Panel — Specification

## Halevi-Luttati Real Estate Practice Platform

**Document version:** 1.1 **Status:** Ready for development **Scope:** All admin-controllable settings, configurations, and read-only monitoring

**Changelog v1.1:**

- Added Brand Transparency sub-principle (Section 0\)  
- Added new Tab 8: Provenance Browser (יומן הוכחות) for full audit chain of all results  
- Renumbered subsequent tabs

---

## 0\. Purpose

The Backoffice is a separate admin panel within the application that gives Ron and Lev (the firm's partners) **direct control** over values, configurations, templates, and policies — **without requesting code changes**.

### The core principle

Anything that might change over time or that the lawyer might reasonably want to tune should be in the Backoffice, not in the code.

### Why this exists

- Tax brackets and thresholds change annually (and sometimes mid-year)  
- Government website URLs occasionally change  
- Email templates need tweaking based on client feedback  
- Pricing on government services changes  
- Document templates evolve as the firm refines its practice

If everything is hardcoded, every change is a developer ticket. If everything is in the Backoffice, the firm is self-sufficient.

### Critical sub-principle: Brand Transparency

The Backoffice is ALSO where the lawyer maintains the trust chain that protects his professional brand. Per `FEATURE_SPEC_Tax_Calculator.md` Section 1.5, every result the system produces must be traceable to an authoritative source. The Backoffice is where the lawyer:

- Audits every calculation that was ever produced  
- Verifies that the system's data sources are still pointing at the right URLs  
- Inspects the provenance chain (inputs, screenshots, results) of any past calculation  
- Detects when external sources have changed or degraded  
- Generates compliance reports to demonstrate due diligence

**Implication for implementation:** The Monitoring tab (Section 9\) and Audit Log tab (Section 10\) are not just operational tools — they are brand-protection tools. They must be as polished and informative as the lawyer-facing features.

---

## 1\. Access & Permissions

### Who can access

- **Partners only:** Ron and Lev (role: `partner`)  
- **Future:** May add a junior admin role with read-only access

### How to access

- Navigation: top menu → "הגדרות" (Settings)  
- Direct URL: `/admin` or `/backoffice`  
- Requires re-authentication (2FA prompt even if already logged in)

### Audit trail

- Every change in the Backoffice is logged with:  
  - Who changed it  
  - When  
  - What was the previous value  
  - What was the new value  
  - Optional reason note (encouraged but not required)  
- The audit log itself is viewable in the Backoffice (read-only)

---

## 2\. Navigation Structure

The Backoffice is organized as tabs:

┌──────────────────────────────────────────────────────────────────┐

│  Backoffice / לוח ניהול                                           │

├──────────────────────────────────────────────────────────────────┤

│  \[Tax Settings\] \[Service URLs\] \[Templates\] \[Pricing\]             │

│  \[Email & Notifications\] \[Users & Team\] \[Monitoring\]             │

│  \[Provenance Browser\] \[Audit Log\] \[Data Export\] \[System Config\]  │

├──────────────────────────────────────────────────────────────────┤

│                                                                  │

│         (content of selected tab)                                │

│                                                                  │

└──────────────────────────────────────────────────────────────────┘

All tabs are in Hebrew RTL. The labels above are translated for the developer's clarity.

---

## 3\. Tab 1: Tax Settings (הגדרות מס)

The most frequently updated tab — Ron checks this every January when tax law changes.

### 3.1 Purchase Tax Section (מס רכישה)

| Setting | Description | Current Value | Type |
| :---- | :---- | :---- | :---- |
| `purchase_tax_simulator_url` | Official simulator URL | [https://www.misim.gov.il/svsimurechisha/startPage.aspx](https://www.misim.gov.il/svsimurechisha/startPage.aspx) | URL |
| `single_residence_brackets_url_section` | Anchor link to law section | gov.il page | URL |
| `last_known_freeze_end_date` | When current bracket freeze ends | 15.1.2028 | Date |

These are mostly informational. The system always uses the live simulator for actual calculations.

### 3.2 Capital Gains Tax Section (מס שבח)

| Setting | Description | Current Value | Type |
| :---- | :---- | :---- | :---- |
| `capital_gains_simulator_url` | Self-assessment simulator | [https://www.misim.gov.il/svtsvazmitnew/](https://www.misim.gov.il/svtsvazmitnew/) | URL |
| `excess_tax_annual_income_threshold` | Income above which מס יסף applies | ₪721,000 | Currency |
| `excess_tax_additional_rate_percent` | Extra rate for high earners | 5% | Percentage |
| `single_residence_luxury_cap` | Above this sale price \= partial exemption | ₪4,603,000 | Currency |
| `linear_calculation_cutoff_date` | Properties bought before this can use linear | 1.1.2014 | Date |
| `improving_housing_grace_period_months` | Time to sell previous primary | 18 months | Number |
| `inheritance_max_share_percent_for_single_residence` | Max inheritance share to still qualify | 50% | Percentage |
| `oleh_eligibility_window_years_before` | Aliyah window before | 1 year | Number |
| `oleh_eligibility_window_years_after` | Aliyah window after | 7 years | Number |
| `disability_minimum_percent` | Min disability % for discount | 19% | Percentage |

### 3.3 UI for this Tab

- Grouped by category with clear Hebrew headers  
- Each value shows: current value, when last changed, by whom  
- "Edit" button next to each value opens a modal:  
  - New value input (with type-appropriate validation)  
  - Reason field (optional text, encouraged)  
  - "Save" button — requires confirmation  
- After save, the change is reflected immediately across the system (no restart needed)  
- "Revert to default" button shows the originally seeded value

### 3.4 Validation

- All numeric fields validate as positive numbers  
- Currency fields formatted with thousand separators and ₪ symbol  
- Date fields use Israeli format (DD/MM/YYYY)  
- URLs validated against allowed domains list

---

## 4\. Tab 2: Service URLs & Endpoints (כתובות שירותים)

For every external government service the system depends on:

| Service | URL | Last Verified | Status |
| :---- | :---- | :---- | :---- |
| Mekarkein Online (Taboo) | [https://mekarkein-online.justice.gov.il/voucher/main](https://mekarkein-online.justice.gov.il/voucher/main) | (timestamp) | ✅ Up |
| Purchase Tax Simulator | [https://www.misim.gov.il/svsimurechisha](https://www.misim.gov.il/svsimurechisha) | (timestamp) | ✅ Up |
| Capital Gains Simulator | [https://www.misim.gov.il/svtsvazmitnew](https://www.misim.gov.il/svtsvazmitnew) | (timestamp) | ⚠️ Slow |
| GovMap (Address Resolver) | [https://www.govmap.gov.il](https://www.govmap.gov.il) | (timestamp) | ✅ Up |
| Bailiff Registry | [https://www.gov.il/he/service/restricted\_debtors\_inquiry](https://www.gov.il/he/service/restricted_debtors_inquiry) | (timestamp) | ✅ Up |
| Liens Registry | [https://www.gov.il/he/service/lien\_inquiry](https://www.gov.il/he/service/lien_inquiry) | (timestamp) | ✅ Up |
| Bank of Israel — Restricted Accounts | [https://www.boi.org.il/](https://www.boi.org.il/)... | (timestamp) | ✅ Up |
| Insolvency Authority | [https://www.gov.il/he/departments/insolvency](https://www.gov.il/he/departments/insolvency) | (timestamp) | ✅ Up |
| MoJ Publications | [https://www.justice.gov.il/](https://www.justice.gov.il/)... | (timestamp) | ✅ Up |

### Features

- Each row has a "Test now" button that runs a health check against the URL  
- Status badges: ✅ Up / ⚠️ Slow / ❌ Down  
- Editable URL field with confirmation modal  
- "View last health check log" link

### Why this matters

Government URLs change. When the Ministry of Justice updated their portal in 2023, every legal tech tool broke for a week. By exposing the URLs in the Backoffice, Ron can update one URL and the system works again — instead of waiting for a developer.

---

## 5\. Tab 3: Document Templates (תבניות מסמכים)

All Word templates the system generates can be edited here.

### Templates list

| Template | Used For | Last Updated | Variables |
| :---- | :---- | :---- | :---- |
| Engagement Letter | Step 1 | (date) | client\_name, fee, property\_address, ... |
| KYC Form | Step 3 | (date) | client\_name, id, ... |
| Pre-Deal Checklist | Step 3 | (date) | property\_address, deal\_type, ... |
| Tax Calculation Memo | Step 3 | (date) | tax\_amount, breakdown, ... |
| Engagement Checklist | Step 3 | (date) | (various) |
| Closing Letter | Step 28 (Phase 2\) | (date) | client\_name, completion\_date, ... |
| Anti-Money-Laundering Form | Step 3 | (date) | (various) |

### UI per template

- "Download current template" button (downloads the .docx file)  
- "Upload new template" button (uploads a replacement .docx)  
- Shows the list of variables the template uses (auto-detected)  
- "Preview with sample data" button (renders the template with test inputs)  
- Version history with rollback option  
- Diff view between versions

### Validation on upload

- File must be .docx  
- All required variables must be present in the new template (verified by parsing)  
- If a variable is missing, show error before allowing the upload to complete  
- File size limit: 5 MB

---

## 6\. Tab 4: Pricing & Costs (תמחור ועלויות)

Government service fees and firm pricing.

### Government fees (paid to authorities)

| Service | Current Fee | Last Updated |
| :---- | :---- | :---- |
| Taboo Consolidated Extract | ₪14 | (date) |
| Taboo Detailed Extract | ₪14 | (date) |
| Taboo Historical Extract | ₪70 | (date) |
| Condo Registration Order | ₪14 | (date) |
| Condo Bylaws | ₪14 | (date) |
| Condo Plan | ₪14 | (date) |

These are passed through to the client; the system uses them to compute total case cost.

### Firm pricing (for the lawyer's quotes)

| Service | Default Fee | Notes |
| :---- | :---- | :---- |
| Purchase representation — single residence | ₪9,500 | Negotiable per client |
| Purchase representation — additional residence | ₪12,000 | Includes more complex tax work |
| Sale representation — exemption case | ₪7,500 | Simpler workflow |
| Sale representation — taxable case | ₪10,000 | Includes self-assessment |
| Mortgage refinance | ₪3,500 | Bank fees only |

### UI

- Editable per row with audit trail  
- Currency formatting  
- "Apply to new cases only" vs "Apply retroactively" choice (defaults to former)

---

## 7\. Tab 5: Email & Notifications (התראות ומיילים)

### Email templates

Each transactional email is editable here:

| Email | Trigger | Recipient |
| :---- | :---- | :---- |
| Client intake form link | Lawyer sends form | Client |
| Intake form completed | Client submits form | Lawyer |
| Identity check red flag | Step 5 finds an issue | Lawyer |
| Taboo extract complete | Step 6 success | Lawyer |
| Taboo extract failed | Step 6 failure | Lawyer |
| Tax calculation complete | Tax Calculator success | Lawyer |
| Payment approval needed | Strategy A approval prompt | Lawyer (push \+ email fallback) |
| Case milestone reached | Various | Client |
| Closing letter | End of case | Client |

### Per email

- Subject line (editable)  
- Body — rich text editor with variable insertion  
- Available variables shown in a sidebar  
- "Send test email" button  
- Per-email setting: enabled / disabled

### Notification preferences (per user)

| Notification | Push | Email | SMS |
| :---- | :---- | :---- | :---- |
| Payment approval needed | ✅ | ✅ | ❌ |
| Red flag found | ✅ | ✅ | ❌ |
| Case status update | ❌ | ✅ | ❌ |
| Daily summary | ❌ | ✅ | ❌ |

Each row is a toggle per user.

---

## 8\. Tab 6: Users & Team (משתמשים וצוות)

### User list

| Name | Email | Role | 2FA | Last Login | Status |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Ron Halevy | ron@... | Partner | ✅ | (timestamp) | Active |
| Lev Luttati | lev@... | Partner | ✅ | (timestamp) | Active |

### Actions per user

- Edit profile (name, email, phone)  
- Reset 2FA  
- Send password reset link (if using passwords)  
- Deactivate account  
- View activity log

### Add user button

- Email  
- Name  
- Role (partner / future: junior)  
- Sends magic link invitation

---

## 9\. Tab 7: Monitoring (מעקב ותפקוד מערכת)

Real-time and historical health of the system.

### 9.1 Scraper Health

For each external scraper (Taboo, Purchase Tax, Capital Gains, Identity Checks):

| Scraper | Last Run | Success Rate (7d) | Avg Duration | Status |
| :---- | :---- | :---- | :---- | :---- |
| Taboo Extract | 12 min ago | 98% (47/48) | 45 sec | ✅ Healthy |
| Purchase Tax Calc | 1 hour ago | 100% (15/15) | 12 sec | ✅ Healthy |
| Capital Gains Calc | 3 hours ago | 95% (19/20) | 38 sec | ⚠️ Watch |
| Identity Check | 30 min ago | 100% (22/22) | 28 sec | ✅ Healthy |
| Address Resolver | 1 hour ago | 92% (46/50) | 8 sec | ⚠️ Watch |

### 9.2 Recent Failures

Last 20 failures with:

- Timestamp  
- Scraper name  
- Error type  
- Case ID (link)  
- Stack trace (expandable)  
- "Mark resolved" button (for tracking)

### 9.3 Active Sessions

For Tax Authority and any other authenticated services:

| User | Service | Session Started | Last Active | Expires |
| :---- | :---- | :---- | :---- | :---- |
| Ron | Tax Authority | 9:34 AM | 11:02 AM | 11:32 AM |

- "Force logout" button next to each session

### 9.4 Usage Statistics

- Total cases this month  
- Total calculations run (purchase tax \+ capital gains)  
- Total Taboo extracts pulled  
- Total identity checks run  
- Cost spent on government services this month (₪)

### 9.5 Cost Tracking

| Service | This Month | Last Month | Total YTD |
| :---- | :---- | :---- | :---- |
| Taboo Extracts | ₪450 | ₪420 | ₪3,200 |
| Anthropic API | $87 | $95 | $620 |
| Google Vision API | $3 | $4 | $25 |
| Hosting (Kamatera) | $40 | $40 | $280 |
| **Total** | **\~₪650** | **\~₪650** | **\~₪4,500** |

---

## 10\. Tab 8: Provenance Browser (יומן הוכחות)

This tab is the **brand-protection backbone**. Every result the system has ever produced — every tax calculation, every Taboo extract, every identity check — is browseable here with its full provenance chain.

### Purpose

When a client or regulator asks "show me exactly how this number was derived," the lawyer comes here. In under 30 seconds, they can produce the complete chain of evidence.

### List View

A searchable, filterable table of every result the system has ever produced:

| Calculation ID | Type | Case | Result | Source | Date | Actions |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| `calc_a1b2...` | Purchase Tax | \#2026-0042 | ₪0 | misim.gov.il | 7.6.2026 | \[View\] \[Export PDF\] |
| `calc_c3d4...` | Capital Gains | \#2026-0042 | EXEMPT (49ב(2)) | exemption\_check | 7.6.2026 | \[View\] \[Export PDF\] |
| `calc_e5f6...` | Identity Check | \#2026-0041 | Clean | 5 sources | 6.6.2026 | \[View\] \[Export PDF\] |
| `calc_g7h8...` | Taboo Extract | \#2026-0041 | (PDF available) | mekarkein-online | 6.6.2026 | \[View\] \[Export PDF\] |
| ... | ... | ... | ... | ... | ... | ... |

### Filters

- By date range  
- By type (Purchase Tax / Capital Gains / Identity Check / Taboo / etc.)  
- By case ID  
- By source (which external service)  
- By status (success / failed / override)

### Detail View

When the lawyer clicks "View" on any row, they see the complete provenance chain:

**Section 1 — Result Summary**

- The final number/output  
- When it was produced  
- Who initiated it  
- Override status (if applicable)

**Section 2 — Inputs**

- Every input that was submitted to the external source  
- Source of each input (e.g., "From case intake form, field X")  
- Validation status

**Section 3 — Provenance Artifacts**

- Screenshot of input form filled (before submit)  
- Screenshot of result page (after submit)  
- HTML snapshot of result page  
- Network logs (URLs visited during the scrape)  
- Each artifact has a download link and a timestamp

**Section 4 — Audit Metadata**

- Scraper version used  
- Backend session ID  
- Total scrape duration  
- Retry attempts (if any)

**Section 5 — Actions**

- "Re-export client PDF" button  
- "Re-run calculation now" button (creates a NEW calculation, doesn't replace)  
- "Mark for legal review" button  
- "Add note" button

### Search

A search bar at the top supports:

- Free text search across calculation IDs, case identifiers, client names  
- Date range queries  
- "Show me all calculations that flagged a warning"  
- "Show me all calculations where the lawyer manually overrode the result"

### Why This Matters

Without this tab, the Brand Transparency principle (per Feature Spec Section 1.5) is theoretical. With this tab, it's operational:

- When a client questions a number from 6 months ago, the lawyer pulls it up in 10 seconds  
- When the Tax Authority audits the firm, the lawyer can demonstrate due diligence  
- When a new partner joins, they can review the firm's historical work for quality assurance  
- When the system breaks, the lawyer can verify which calculations were affected

### Retention

- All provenance data retained indefinitely (per Section 11.6 of Feature Spec)  
- No automated cleanup  
- Lawyer can export and archive externally at any time

---

## 11\. Tab 9: Audit Log (יומן שינויים)

Complete, searchable log of every change made in the Backoffice.

### Columns

- Timestamp  
- User (who made the change)  
- Section (which tab/area)  
- Field (what specific value)  
- Old value  
- New value  
- Reason (if provided)

### Filters

- By user  
- By section  
- By date range  
- Free text search

### Export

- Download as CSV for any filtered view

### Retention

- All audit log entries kept forever (never deleted)

---

## 12\. Tab 10: Data Export (ייצוא נתונים)

For when Ron wants to migrate data out, archive, or just keep backups.

### Available exports

| Export | Format | Includes |
| :---- | :---- | :---- |
| All cases | ZIP of JSON | Every case record with all sub-data |
| All documents | ZIP | All PDFs, Word docs, screenshots organized by case |
| All calculations | CSV | Every tax calculation ever run |
| All identity checks | ZIP | Every identity check report |
| Audit log | CSV | All Backoffice changes |
| Database snapshot | SQL | Full database dump (for technical migration) |

### UI per export

- "Generate export" button (creates async job)  
- Email notification when ready (large exports may take minutes)  
- Download link valid for 7 days  
- Encryption option for sensitive exports (password-protected ZIP)

---

## 13\. Tab 11: System Config (תצורת מערכת)

Advanced settings — Ron rarely touches these, but they're here when needed.

### Scraper tuning

| Setting | Description | Current |
| :---- | :---- | :---- |
| `scraper_retry_max_attempts` | How many times to retry | 3 |
| `scraper_retry_backoff_seconds` | Initial backoff | 1, 3, 9 |
| `scraper_timeout_seconds` | Per-page timeout | 60 |
| `scraper_concurrency_limit` | Parallel scrape limit | 3 |
| `headless_mode` | Run scrapers in background | true |

### Result validation

| Setting | Description | Current |
| :---- | :---- | :---- |
| `result_sanity_bounds_purchase_max_percent` | Max plausible purchase tax % | 10% |
| `result_sanity_bounds_capital_gains_max_percent` | Max plausible capital gains % | 50% |
| `result_validation_strict` | Fail on out-of-bounds vs warn | true |

### Session management

| Setting | Description | Current |
| :---- | :---- | :---- |
| `session_timeout_minutes` | Tax Authority session expiry | 30 |
| `session_max_per_user` | Max concurrent sessions | 1 |

### Maintenance

| Setting | Description | Current |
| :---- | :---- | :---- |
| `maintenance_mode` | Show "system down" banner to non-admins | false |
| `maintenance_message` | Banner text in Hebrew | (text) |

---

## 14\. Implementation Notes

### Database

- Single `system_config` table with schema: `(key, value, description, value_type, default_value, last_updated_at, last_updated_by_user_id)`  
- Loaded into memory on application startup  
- In-memory cache invalidated on update  
- Type-safe accessors in code: `config.get_currency('excess_tax_annual_income_threshold')`

### Frontend

- Each tab is a separate route under `/admin/*`  
- Permission check on every route (must be partner)  
- Optimistic updates with rollback on save failure  
- All changes confirmed via modal (no accidental saves)

### Validation

- Server-side validation of all values (don't trust the client)  
- Type validation matches the declared type  
- Range validation for percentages (0-100) and currency (positive)  
- URL validation against allowed domains list

### Migration of existing hardcoded values

On first deploy, the database migration that creates the `system_config` table also seeds all the default values. The application reads from the table, but the seed values ARE the previously-hardcoded values — so there's no behavior change on initial deploy.

### Backup

- Before any value is changed, the previous value is logged in the audit table  
- Database is backed up daily (already in PRD)  
- Specific "Backoffice export" function allows downloading the entire config as JSON

---

## 15\. Out of Scope for MVP

These are features that the Backoffice could plausibly have but are NOT in scope for Phase 1:

- **Multi-tenancy** — supporting multiple firms  
- **Granular permissions** — different access levels per partner (everyone is admin for now)  
- **API access** — allowing third-party tools to read/modify Backoffice  
- **A/B testing** — running different config values for different cases  
- **Self-service onboarding** — adding new firms to the platform  
- **White-labeling** — customizing the platform's branding per firm  
- **Workflow editor** — visual editor for the 10 pre-signing steps (steps are hardcoded)  
- **Form designer** — visual editor for the Smart Intake Form (form is hardcoded)  
- **Reporting builder** — custom reports beyond what's in Monitoring tab

---

## 16\. Acceptance Criteria

The Backoffice is ready to ship when:

**Functional:**

- [ ] Ron and Lev can both log in and access all tabs  
- [ ] Every tax-related value listed in Section 3 can be edited without code change  
- [ ] All changes are logged with who/when/what  
- [ ] The system reads values from the config table at runtime (no hardcoded constants in business logic for any value listed here)  
- [ ] Templates can be downloaded, edited offline, and re-uploaded  
- [ ] Monitoring tab shows real scraper health data

**Brand Transparency (per Feature Spec Section 1.5):**

- [ ] Provenance Browser tab lists every historical calculation across all features  
- [ ] Each provenance entry includes inputs, screenshots, raw HTML, and audit metadata  
- [ ] Lawyer can retrieve any past result's full provenance chain in under 30 seconds  
- [ ] Re-export of client PDF works for any historical calculation  
- [ ] No automated deletion of provenance data  
- [ ] Search and filter on provenance browser works smoothly across thousands of entries

**Quality:**

- [ ] Audit log is searchable and exportable  
- [ ] All UI is in Hebrew RTL  
- [ ] 2FA is required to enter the Backoffice (even from authenticated session)  
- [ ] Permission check prevents non-partners from accessing  
- [ ] Sample data tour for new admins (first-time walkthrough)

---

## 17\. Future Tabs (Phase 2+)

These tabs may be added later as the system grows:

- **Workflow Builder** — visual editor for the case workflow (currently hardcoded)  
- **Integration Settings** — when Legal CRM and Landbit integrations are added  
- **Billing & Subscriptions** — if this becomes a multi-firm SaaS  
- **API Keys** — for managing programmatic access  
- **White-label Settings** — colors, logo, fonts for the client-facing portal

---

**End of Backoffice Spec**

This document is a sibling to `FEATURE_SPEC_Tax_Calculator.md` and the main `PRD_Phase1_Pre-Signing.md`. The Backoffice is implemented in parallel with the main feature development — every new feature should consider what should be in the Backoffice from day one.  
