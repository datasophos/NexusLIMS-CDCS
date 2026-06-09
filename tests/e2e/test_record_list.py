"""E2E tests for the record list and search."""

import re

from playwright.sync_api import expect


def test_record_list_renders(unauthenticated_page, base_url):
    """Record list page loads and shows at least one record.

    By default all three records in the test data are in the public
    workspace, so no login is needed to see them on the list page.
    """
    page = unauthenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")
    expect(page.locator("a[href*='/data?id=']")).not_to_have_count(0)


def test_search_filters_records(authenticated_page, base_url):
    """Typing in the search box filters the record list."""
    page = authenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    record_links = "a[href*='/data?id=']"
    expect(page.locator(record_links)).not_to_have_count(0)

    # The keyword field is a jQuery Tag-it widget: the real input is hidden and
    # the visible field registers a tag on Enter before the search is submitted.
    keyword_input = page.locator("input.ui-autocomplete-input")
    keyword_input.fill("zzznomatch")
    keyword_input.press("Enter")
    page.locator("button:has-text('Search')").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator(record_links)).to_have_count(0)
    expect(page.get_by_text("No results found")).to_be_visible()


def test_keyword_search_returns_matching_record(unauthenticated_page, base_url):
    """Searching for a keyword returns only the records that match it.

    Of the public records, only "Example record large" mentions "simple" (it
    triggers the simple display), so the search narrows the list to that one.
    """
    page = unauthenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    record_links = page.locator("a[href*='/data?id=']")
    expect(record_links).not_to_have_count(0)

    # The keyword field is a jQuery Tag-it widget: the real input is hidden and
    # the visible field registers a tag on Enter before the search is submitted.
    keyword_input = page.locator("input.ui-autocomplete-input")
    keyword_input.fill("simple")
    keyword_input.press("Enter")
    page.locator("button:has-text('Search')").click()

    expect(record_links).to_have_count(1)


def test_instrument_badge_filters_records(unauthenticated_page, base_url):
    """Clicking an instrument badge filters the record list to that instrument.

    Public records span multiple instruments. Clicking a badge adds an
    ``instrument-pid:`` tag to the keyword search and re-runs it. We verify
    that each filter reduces the count and that TEM has more records than STEM.
    """
    page = unauthenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    record_links = page.locator("a[href*='/data?id=']")
    total = record_links.count()
    assert total >= 3

    # Filter to the FEI Titan TEM instrument.
    page.locator(
        "span.instrument-badge-clickable[data-instrument-pid='FEI-Titan-TEM']"
    ).first.click()
    page.wait_for_load_state("networkidle")
    tem_count = record_links.count()
    assert tem_count >= 1

    # Clear the filter and restore the full list.
    page.locator(".tagit-choice .tagit-close").first.click()
    page.locator("button:has-text('Search')").click()
    page.wait_for_load_state("networkidle")
    expect(record_links).to_have_count(total)

    # Filter to the FEI Titan STEM instrument.
    page.locator(
        "span.instrument-badge-clickable[data-instrument-pid='FEI-Titan-STEM']"
    ).first.click()
    page.wait_for_load_state("networkidle")
    stem_count = record_links.count()
    assert stem_count >= 1
    assert stem_count < total
    assert stem_count < tem_count


def test_record_link_navigates_to_detail(authenticated_page, base_url):
    """Clicking a record link navigates to the detail page."""
    page = authenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    first_link = page.locator("a[href*='/data?id=']").first
    first_link.click()
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r"/data\?id="))
    expect(page.locator(".list-record-title")).to_be_visible()
