"""
⚠️ EXAMPLE / REFERENCE CODE — NOT WIRED INTO THE APP ⚠️
========================================================
This file lives under docs/Code Examples/ and is an illustrative reference
showing one possible approach to the Address Resolver feature. It is NOT
imported by apps/api or apps/web, has no tests, and is not part of the build.
Treat it as a design sketch to inform the real implementation, not as
shippable code. (Note for future Claude: do not assume this runs in production.)

Address Resolver - Reference example
====================================
Converts an Israeli address (city, street, number) into block/parcel/sub-parcel
using the official GovMap API.

Strategy:
1. PRIMARY:  GovMap searchAndLocate JS API via Playwright headless browser
2. FALLBACK: Direct GovMap REST endpoint (if we reverse-engineer it)
3. MANUAL:   Return error and ask the lawyer to enter block/parcel manually

REQUIREMENTS (install with):
    pip install playwright
    playwright install chromium

ENVIRONMENT:
    Must run from an Israeli IP for best reliability with government sites.
    Recommended hosting: Kamatera (Israel), or any Israeli VPS.

USAGE:
    from address_resolver import resolve_address
    result = await resolve_address("בת ים", "בר יהודה", "33")
    # → {"gush": "7136", "chelka": "142", "sub_parcels": [...], ...}
"""

from playwright.async_api import async_playwright
from dataclasses import dataclass, asdict
from typing import Optional
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AddressResolutionResult:
    """Result of an address-to-block/parcel lookup."""
    success: bool
    address_input: str                       # what we searched for
    gush: Optional[str] = None              # block
    chelka: Optional[str] = None            # parcel
    sub_parcels: Optional[list] = None      # all sub-parcels at this address
    settlement_code: Optional[int] = None
    coordinates: Optional[dict] = None      # {x, y} in ITM (Israeli grid)
    raw_response: Optional[dict] = None     # full GovMap response for debugging
    error: Optional[str] = None
    method_used: Optional[str] = None       # "govmap_js" / "govmap_rest" / "manual"


async def resolve_address_via_govmap(
    city: str,
    street: str,
    number: str,
    api_token: str = "",       # GovMap requires a free token for production use
    timeout_ms: int = 30000,
) -> AddressResolutionResult:
    """
    Use GovMap's official JavaScript API via Playwright.

    This is the most reliable method because:
    - GovMap is the official Israeli government mapping service
    - Its data comes from the Survey of Israel (mapi)
    - Updates are real-time
    """
    full_address = f"{street} {number}, {city}"
    logger.info(f"Resolving address via GovMap: {full_address}")

    # Build a minimal HTML page that hosts GovMap's JS API
    # and calls searchAndLocate with the lotParcelToAddress type
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://www.govmap.gov.il/govmap/api/govmap.api.js"></script>
    </head>
    <body>
        <div id="map" style="width:1px;height:1px;visibility:hidden;"></div>
        <div id="result" style="display:none;"></div>
        <script>
            window.resolveResult = null;
            window.resolveError = null;

            async function init() {{
                try {{
                    await govmap.createMap('map', {{
                        token: '{api_token}',
                        layers: ['PARCEL_ALL'],
                        showXY: true,
                        layersMode: 1
                    }});

                    const params = {{
                        type: govmap.locateType.lotParcelToAddress,
                        address: '{full_address}'
                    }};

                    const response = await govmap.searchAndLocate(params);
                    window.resolveResult = response;
                    document.getElementById('result').innerText =
                        JSON.stringify(response);
                }} catch (err) {{
                    window.resolveError = err.message || String(err);
                    document.getElementById('result').innerText =
                        'ERROR: ' + window.resolveError;
                }}
            }}

            // GovMap API loads async; wait until ready
            const checkReady = setInterval(() => {{
                if (typeof govmap !== 'undefined' &&
                    typeof govmap.createMap === 'function') {{
                    clearInterval(checkReady);
                    init();
                }}
            }}, 200);
        </script>
    </body>
    </html>
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        try:
            context = await browser.new_context(
                locale='he-IL',
                timezone_id='Asia/Jerusalem',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            # Load our embedded HTML
            await page.set_content(html_page)

            # Wait for either result or error to appear
            try:
                await page.wait_for_function(
                    "window.resolveResult !== null || window.resolveError !== null",
                    timeout=timeout_ms
                )
            except Exception as e:
                return AddressResolutionResult(
                    success=False,
                    address_input=full_address,
                    error=f"Timeout waiting for GovMap response: {e}",
                    method_used="govmap_js"
                )

            # Read result from window
            result_data = await page.evaluate("window.resolveResult")
            error_data = await page.evaluate("window.resolveError")

            if error_data:
                return AddressResolutionResult(
                    success=False,
                    address_input=full_address,
                    error=error_data,
                    method_used="govmap_js"
                )

            if not result_data or not isinstance(result_data, list) or len(result_data) == 0:
                return AddressResolutionResult(
                    success=False,
                    address_input=full_address,
                    error="No results from GovMap (empty or invalid response)",
                    raw_response=result_data,
                    method_used="govmap_js"
                )

            # Parse the response
            # GovMap returns an array of objects, each with:
            #   ObjectId, Values (the [gush, chelka] array), settlementCode, etc.
            first = result_data[0]
            values = first.get("Values", [])
            gush = str(values[0]) if len(values) > 0 else None
            chelka = str(values[1]) if len(values) > 1 else None

            return AddressResolutionResult(
                success=bool(gush and chelka),
                address_input=full_address,
                gush=gush,
                chelka=chelka,
                sub_parcels=None,  # GovMap doesn't return sub-parcels in this call
                settlement_code=first.get("settlementCode"),
                coordinates={
                    "x": first.get("X") or first.get("x"),
                    "y": first.get("Y") or first.get("y")
                } if first.get("X") or first.get("x") else None,
                raw_response=result_data,
                method_used="govmap_js"
            )
        finally:
            await browser.close()


async def get_sub_parcels(gush: str, chelka: str) -> list:
    """
    Once we have gush/chelka, fetch the list of sub-parcels (apartments)
    in that building from the Land Registry.

    This is a separate step because GovMap returns only the main parcel,
    but a multi-apartment building has many sub-parcels.

    NOTE: This requires accessing the Land Registry's records,
    which is usually done via the same Taboo extract process (Step 6 in our PRD).
    For now, we return a placeholder; the lawyer will identify the sub-parcel
    from the consolidated extract.
    """
    # In Phase 1 MVP: return empty and let lawyer identify from Taboo extract
    return []


async def resolve_address(
    city: str,
    street: str,
    number: str,
    api_token: str = ""
) -> AddressResolutionResult:
    """
    Main entry point. Tries methods in order of reliability.
    """
    # Method 1: GovMap JS API (primary)
    result = await resolve_address_via_govmap(city, street, number, api_token)
    if result.success:
        return result

    logger.warning(
        f"GovMap resolution failed for {street} {number}, {city}. "
        f"Error: {result.error}"
    )

    # Method 2: TODO - Reverse-engineered REST endpoint
    # Method 3: TODO - Alternative provider (nadlan.gov.il, gov.il/apps/mapi)

    return result


# ============================================================
# CLI usage for testing
# ============================================================
if __name__ == "__main__":
    import sys

    async def main():
        # Guy's apartment
        city = sys.argv[1] if len(sys.argv) > 1 else "בת ים"
        street = sys.argv[2] if len(sys.argv) > 2 else "בר יהודה"
        number = sys.argv[3] if len(sys.argv) > 3 else "33"

        print(f"Resolving: {street} {number}, {city}\n")

        result = await resolve_address(city, street, number)

        print("=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))

        if result.success:
            print(f"\n✅ Block (גוש): {result.gush}")
            print(f"✅ Parcel (חלקה): {result.chelka}")
            print(f"\nNext step: Pull Taboo extract for {result.gush}/{result.chelka}")
            print(f"This will return the list of sub-parcels (apartments).")
            print(f"Guy's apartment is #13 — that may or may not match the "
                  f"sub-parcel number on the Taboo extract.")
        else:
            print(f"\n❌ Failed: {result.error}")

    asyncio.run(main())
