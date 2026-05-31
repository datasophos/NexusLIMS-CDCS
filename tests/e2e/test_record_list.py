"""E2E tests for the record list and search."""

from playwright.sync_api import expect


def test_record_list_renders(unauthenticated_page, base_url):
    """Record list page loads and shows at least one record.

    By default all three records in the test data are in the public
    workspace, so no login is needed to see them on the list page.
    """
    page = unauthenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")
    records = page.locator("a[href*='/data?id=']").all()
    assert len(records) > 0, "No record links found on the list page"


def test_search_filters_records(authenticated_page, base_url):
    """Typing in the search box filters the record list."""
    page = authenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    record_links = "a[href*='/data?id=']"

    # The keyword field is a jQuery Tag-it widget: the real input is hidden and
    # the visible field registers a tag on Enter before the search is submitted.
    keyword_input = page.locator("input.ui-autocomplete-input")
    keyword_input.fill("zzznomatch")
    keyword_input.press("Enter")
    page.locator("button:has-text('Search')").click()
    page.wait_for_load_state("networkidle")

    filtered_count = page.locator(record_links).count()
    assert filtered_count == 0


def test_keyword_search_returns_matching_record(unauthenticated_page, base_url):
    """Searching for a keyword returns only the records that match it.

    Of the three public test records, only one mentions "simple" (the record
    whose 200 datasets trigger the simple display), so the search narrows the
    list to that single record.
    """
    page = unauthenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    record_links = page.locator("a[href*='/data?id=']")
    expect(record_links).to_have_count(3)

    # The keyword field is a jQuery Tag-it widget: the real input is hidden and
    # the visible field registers a tag on Enter before the search is submitted.
    keyword_input = page.locator("input.ui-autocomplete-input")
    keyword_input.fill("simple")
    keyword_input.press("Enter")
    page.locator("button:has-text('Search')").click()

    expect(record_links).to_have_count(1)


def test_instrument_badge_filters_records(unauthenticated_page, base_url):
    """Clicking an instrument badge filters the record list to that instrument.

    The three public test records span two instruments: two on the FEI Titan
    TEM and one on the FEI Titan STEM. Clicking a badge adds an
    ``instrument-pid:`` tag to the keyword search and re-runs it.
    """
    page = unauthenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    record_links = page.locator("a[href*='/data?id=']")
    expect(record_links).to_have_count(3)

    # Filter to the FEI Titan TEM instrument -> two records.
    page.locator(
        "span.instrument-badge-clickable[data-instrument-pid='FEI-Titan-TEM']"
    ).first.click()
    expect(record_links).to_have_count(2)

    # Clear the filter: remove the keyword tag and re-run the search to show
    # all records again (the STEM badge is only present once they are shown).
    page.locator(".tagit-choice .tagit-close").first.click()
    page.locator("button:has-text('Search')").click()
    expect(record_links).to_have_count(3)

    # Filter to the FEI Titan STEM instrument -> one record.
    page.locator(
        "span.instrument-badge-clickable[data-instrument-pid='FEI-Titan-STEM']"
    ).click()
    expect(record_links).to_have_count(1)


def test_record_link_navigates_to_detail(authenticated_page, base_url):
    """Clicking a record link navigates to the detail page."""
    page = authenticated_page
    page.goto(f"{base_url}/explore/keyword/")
    page.wait_for_load_state("networkidle")

    first_link = page.locator("a[href*='/data?id=']").first
    first_link.click()
    page.wait_for_load_state("networkidle")
    assert "/data?id=" in page.url or page.locator("text=Annotate").count() > 0
