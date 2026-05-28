"""E2E tests for the record list and search."""
import pytest


def test_record_list_renders(authenticated_page, base_url):
    """Record list page loads and shows at least one record."""
    page = authenticated_page
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    records = page.locator("a[href*='/rest/data/'], a[href*='/data/'], .list-group-item a").all()
    assert len(records) > 0, "No record links found on the list page"


def test_search_filters_records(authenticated_page, base_url):
    """Typing in the search box filters the record list."""
    page = authenticated_page
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")

    search = page.locator("input[type='search'], input[name='q'], #id_search, input[placeholder*='earch']").first
    initial_count = page.locator("a[href*='/rest/data/'], .list-group-item a").count()

    search.fill("zzznomatch")
    search.press("Enter")
    page.wait_for_load_state("networkidle")

    filtered_count = page.locator("a[href*='/rest/data/'], .list-group-item a").count()
    assert filtered_count < initial_count or page.locator("text=No results, text=no record").count() > 0


def test_record_link_navigates_to_detail(authenticated_page, base_url):
    """Clicking a record link navigates to the detail page."""
    page = authenticated_page
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")

    first_link = page.locator("a[href*='/rest/data/']").first
    first_link.click()
    page.wait_for_load_state("networkidle")
    assert "/rest/data/" in page.url or page.locator("text=Annotate").count() > 0
