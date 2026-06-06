# Code Examples — Reference Only

> ⚠️ **The code in this folder is illustrative example/reference code, not part of the application.**

These files are design sketches that show *one possible approach* to specific
features described in the PRD. They exist to communicate intent and guide the
real implementation.

**They are NOT:**

- imported by `apps/api` or `apps/web`
- covered by tests
- part of the build, CI, or any runtime
- guaranteed to run as-is (dependencies, API tokens, and endpoints are illustrative)

**Note for future Claude:** Do not assume anything here is production code or
that it is wired into the app. If you implement one of these features, treat the
example as a starting point and build the real version inside `apps/`.

## Contents

| File | Feature | Related PRD section |
| :--- | :--- | :--- |
| `address_resolver.py` | Resolve an Israeli address → block/parcel (gush/chelka) via GovMap | New Step 5.5 (see `PRD_DELTA_v1.0_to_v1.1.md`) |
| `taboo_fetcher.py` | Automate Land Registry (Taboo) extract retrieval | Step 6 (see `PRD_DELTA_v1.0_to_v1.1.md`) |
