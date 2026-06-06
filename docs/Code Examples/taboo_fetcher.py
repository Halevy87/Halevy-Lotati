"""
⚠️ EXAMPLE / REFERENCE CODE — NOT WIRED INTO THE APP ⚠️
========================================================
This file lives under docs/Code Examples/ and is an illustrative reference
showing one possible approach to the Taboo Extract Fetcher feature. It is NOT
imported by apps/api or apps/web, has no tests, and is not part of the build.
Treat it as a design sketch to inform the real implementation, not as
shippable code. (Note for future Claude: do not assume this runs in production.)

Taboo Extract Fetcher - Reference example (Phase 1)
================================
Automates the retrieval of Land Registry (Taboo) extracts from the Israeli
Ministry of Justice's online portal: mekarkein-online.justice.gov.il

KEY INSIGHT (June 2026 research):
Pulling Taboo extracts does NOT require a lawyer's digital signature.
The service is open to anyone with:
- Block/Parcel/Sub-parcel numbers (gush/chelka/tat-chelka)
- A credit card for the fee (~₪15 for standard extract, ~₪70 for full historical)
- An email address to receive the PDF

Digital signature is ONLY required for:
- Filing cautionary notes (post-signing)
- Mortgage registration (post-signing)
- Sale registration (post-handover)

This means Phase 1 (pre-signing) has NO digital signature dependency.
The server can run this fully autonomously from an Israeli IP.

ARCHITECTURE:
1. Web app calls fetch_taboo_extract() with case ID and parcel info
2. This module uses Playwright to:
   a. Open mekarkein-online.justice.gov.il
   b. Fill in gush/chelka/tat-chelka
   c. Choose extract type (standard / historical / consolidated)
   d. Pay with the firm's stored credit card (via stored Stripe token)
   e. Download the PDF
3. PDF is stored in case folder
4. Parser extracts structured data (owners, mortgages, liens, etc.)

REQUIREMENTS:
    pip install playwright stripe python-dotenv
    playwright install chromium

ENVIRONMENT (required vars in .env):
    FIRM_CC_STRIPE_TOKEN     - tokenized credit card for the firm
    FIRM_EMAIL_FOR_RECEIPTS  - email to receive PDFs and receipts
    TABOO_BASE_URL=https://mekarkein-online.justice.gov.il
"""

from playwright.async_api import async_playwright, Page
from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path
import asyncio
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


ExtractType = Literal[
    "standard",      # נסח רישום רגיל - the most common, ~₪15
    "consolidated",  # נסח רישום מרוכז - all units in the block
    "historical",    # נסח רישום היסטורי - includes deleted entries
    "condo_file"     # תיק בית משותף - registration order + bylaws + plan
]


@dataclass
class ParcelIdentifier:
    """Identifier for a property in the Israeli Land Registry."""
    gush: str          # block
    chelka: str        # parcel
    tat_chelka: Optional[str] = None  # sub-parcel (for apartments in condos)

    def display(self) -> str:
        if self.tat_chelka:
            return f"{self.gush}/{self.chelka}/{self.tat_chelka}"
        return f"{self.gush}/{self.chelka}"


@dataclass
class TabooExtractResult:
    """Result of a Taboo extract fetch."""
    success: bool
    parcel: ParcelIdentifier
    extract_type: ExtractType
    pdf_path: Optional[Path] = None       # local path where PDF was saved
    transaction_id: Optional[str] = None  # govt confirmation number
    fee_paid_ils: Optional[float] = None
    fetched_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    # Parsed structured data (populated by parser, separate module)
    parsed_data: Optional[dict] = None


class TabooFetcher:
    """
    Encapsulates the Taboo fetch workflow.

    Usage:
        async with TabooFetcher() as fetcher:
            result = await fetcher.fetch(
                parcel=ParcelIdentifier(gush="7136", chelka="142", tat_chelka="13"),
                extract_type="consolidated",
                case_id="2026-0042"
            )
    """

    BASE_URL = "https://mekarkein-online.justice.gov.il"

    def __init__(
        self,
        download_dir: Path = Path("./taboo_extracts"),
        headless: bool = True,
        firm_cc_token: Optional[str] = None,
        firm_email: Optional[str] = None,
    ):
        self.download_dir = download_dir
        self.download_dir.mkdir(exist_ok=True, parents=True)
        self.headless = headless
        self.firm_cc_token = firm_cc_token or os.getenv("FIRM_CC_STRIPE_TOKEN")
        self.firm_email = firm_email or os.getenv("FIRM_EMAIL_FOR_RECEIPTS")

        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.context = await self.browser.new_context(
            locale="he-IL",
            timezone_id="Asia/Jerusalem",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            accept_downloads=True
        )
        return self

    async def __aexit__(self, *exc):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch(
        self,
        parcel: ParcelIdentifier,
        extract_type: ExtractType,
        case_id: str,
    ) -> TabooExtractResult:
        """
        Main entry point: fetch a Taboo extract for the given parcel.
        """
        logger.info(
            f"Fetching {extract_type} extract for parcel {parcel.display()} "
            f"(case {case_id})"
        )

        page = await self.context.new_page()
        try:
            # === Step 1: Navigate to the portal ===
            await page.goto(f"{self.BASE_URL}/voucher/main", wait_until="networkidle")
            await self._screenshot(page, case_id, "01_landing")

            # === Step 2: Choose extract type ===
            # The portal has different paths for standard vs consolidated etc.
            # We'll click the appropriate menu item.
            #
            # NOTE: The actual selectors here are PLACEHOLDERS.
            # When running for the first time in production, we'll need to
            # inspect the live site and update these. The structure of the
            # site changes occasionally and we should monitor for breakage.
            extract_button_map = {
                "standard": "text=הפקת נסח רישום רגיל",
                "consolidated": "text=הפקת נסח מרוכז",
                "historical": "text=הפקת נסח היסטורי",
                "condo_file": "text=הפקת תיק בית משותף",
            }
            await page.click(extract_button_map[extract_type])
            await page.wait_for_load_state("networkidle")
            await self._screenshot(page, case_id, "02_form")

            # === Step 3: Fill in parcel identifiers ===
            await page.fill("input[name='gush']", parcel.gush)
            await page.fill("input[name='chelka']", parcel.chelka)
            if parcel.tat_chelka and extract_type != "consolidated":
                await page.fill("input[name='tatChelka']", parcel.tat_chelka)

            # === Step 4: Email for receipt ===
            await page.fill("input[name='email']", self.firm_email)

            # Submit the form to proceed to payment
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
            await self._screenshot(page, case_id, "03_payment_form")

            # === Step 5: Payment ===
            # The govt payment service uses an embedded payment iframe.
            # We need to handle the iframe context here.
            #
            # In production, payment should use a stored credit card token.
            # Approach: Use Stripe Connect or BlueSnap to store the firm's card,
            # and present it to the gov portal via a token-based mechanism if
            # available, OR — more commonly — fill the form with stored card
            # details retrieved from a PCI-compliant vault on each request.
            #
            # For MVP: implement as a SEPARATE step requiring lawyer review.
            # The system PAUSES here, shows a "Confirm payment for case X"
            # prompt to the lawyer, who approves with one click.
            await self._handle_payment(page, case_id)

            # === Step 6: Wait for and download PDF ===
            async with page.expect_download(timeout=60000) as download_info:
                await page.click("text=הורד נסח")  # placeholder selector
            download = await download_info.value

            pdf_path = self.download_dir / (
                f"{case_id}_{extract_type}_"
                f"{parcel.display().replace('/', '_')}_"
                f"{datetime.now():%Y%m%d_%H%M%S}.pdf"
            )
            await download.save_as(pdf_path)

            # Extract transaction ID from the confirmation page
            transaction_id = await self._extract_transaction_id(page)

            return TabooExtractResult(
                success=True,
                parcel=parcel,
                extract_type=extract_type,
                pdf_path=pdf_path,
                transaction_id=transaction_id,
                fee_paid_ils=self._get_fee_for_type(extract_type),
            )

        except Exception as e:
            logger.exception(f"Failed to fetch Taboo extract: {e}")
            await self._screenshot(page, case_id, "99_error")
            return TabooExtractResult(
                success=False,
                parcel=parcel,
                extract_type=extract_type,
                error=str(e)
            )
        finally:
            await page.close()

    async def _handle_payment(self, page: Page, case_id: str) -> None:
        """
        Handles the payment step.

        MVP approach: pause for human approval, show payment form in the
        firm's dashboard, lawyer clicks "approve" which triggers continuation.

        Production approach: use stored tokenized credit card via vault.
        """
        # Placeholder: in real implementation, this would either:
        # 1. Fill form with stored card details from secure vault
        # 2. Or emit an event for human approval and wait
        raise NotImplementedError(
            "Payment integration pending. See PRD section on payment vault."
        )

    async def _extract_transaction_id(self, page: Page) -> Optional[str]:
        """Extracts the transaction confirmation number from the page."""
        try:
            text = await page.locator(".confirmation-number").inner_text()
            return text.strip()
        except Exception:
            return None

    async def _screenshot(self, page: Page, case_id: str, label: str) -> None:
        """Takes a screenshot for debugging / audit trail."""
        screenshot_path = (
            self.download_dir / f"{case_id}_{label}_"
            f"{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
        except Exception:
            pass

    def _get_fee_for_type(self, extract_type: ExtractType) -> float:
        """Returns the official fee for each extract type (2026 prices)."""
        fees = {
            "standard": 14.0,
            "consolidated": 14.0,
            "historical": 70.0,
            "condo_file": 14.0 * 3,  # plan + order + bylaws
        }
        return fees.get(extract_type, 14.0)


# ============================================================
# Example usage
# ============================================================
async def example():
    """Example workflow: fetch consolidated extract for Guy's apartment."""
    parcel = ParcelIdentifier(
        gush="XXXX",   # to be resolved by address_resolver.py
        chelka="XX",
        tat_chelka=None  # not needed for consolidated
    )

    async with TabooFetcher(headless=False) as fetcher:
        result = await fetcher.fetch(
            parcel=parcel,
            extract_type="consolidated",
            case_id="DEMO-001"
        )

    if result.success:
        print(f"✅ Extract saved to: {result.pdf_path}")
        print(f"   Transaction ID: {result.transaction_id}")
        print(f"   Fee paid: ₪{result.fee_paid_ils}")
    else:
        print(f"❌ Failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(example())
