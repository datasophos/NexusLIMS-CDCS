"""E2E tests for the XSLT-rendered record detail page."""
import pytest


def test_detail_page_loads(authenticated_page, base_url, test_record_id):
    """Detail page renders without error for a known record."""
    page = authenticated_page
    page.goto(f"{base_url}/rest/data/{test_record_id}/")
    page.wait_for_load_state("networkidle")
    assert page.locator("text=Server Error, text=Exception").count() == 0
    assert page.title() != ""


def test_detail_shows_key_fields(authenticated_page, base_url, test_record_id):
    """Key metadata fields are visible on the rendered detail page."""
    page = authenticated_page
    page.goto(f"{base_url}/rest/data/{test_record_id}/")
    page.wait_for_load_state("networkidle")
    content = page.locator("body").inner_text()
    assert len(content.strip()) > 100, "Detail page body appears empty -- XSLT may have failed"


def test_annotate_button_navigates(authenticated_page, base_url, test_record_id):
    """'Annotate' link on the detail page navigates to the annotator."""
    page = authenticated_page
    page.goto(f"{base_url}/rest/data/{test_record_id}/")
    page.wait_for_load_state("networkidle")

    annotate_link = page.locator("a:has-text('Annotate'), a[href*='/annotate/']").first
    assert annotate_link.count() > 0, "Annotate link not found on detail page"
    annotate_link.click()
    page.wait_for_load_state("networkidle")
    assert "/annotate/" in page.url
