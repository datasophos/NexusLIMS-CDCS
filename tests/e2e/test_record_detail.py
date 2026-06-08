"""E2E tests for the XSLT-rendered record detail page."""

from playwright.sync_api import expect


def test_detail_page_loads(authenticated_page, base_url, normal_record_id):
    """Detail page renders without error for a known record."""
    page = authenticated_page
    response = page.goto(f"{base_url}/data?id={normal_record_id}")
    page.wait_for_load_state("networkidle")
    assert response.status == 200
    expect(page.locator(".list-record-title")).to_be_visible()


def test_detail_shows_key_fields(authenticated_page, base_url, normal_record_id):
    """Key metadata fields are visible on the rendered detail page."""
    page = authenticated_page
    page.goto(f"{base_url}/data?id={normal_record_id}")
    page.wait_for_load_state("networkidle")
    expect(page.locator(".list-record-title")).not_to_be_empty()
    expect(page.locator("#instr-badge")).not_to_be_empty()
    expect(page.locator(".list-record-experimenter")).not_to_be_empty()
    expect(page.locator("#summary-info")).to_contain_text("data files")


def test_annotate_button_navigates(authenticated_page, base_url, normal_record_id):
    """'Annotate Record' button on the detail page opens the full-page annotator."""
    page = authenticated_page
    page.goto(f"{base_url}/data?id={normal_record_id}")
    page.wait_for_load_state("networkidle")

    annotate_btn = page.locator("#annotate-record-btn")
    annotate_btn.wait_for(state="visible")
    annotate_btn.click()

    expand_btn = page.locator("#annotate-expand-btn")
    expand_btn.wait_for(state="visible")
    expand_btn.click()
    page.wait_for_url(lambda url: "/annotate/" in url)


def test_detail_shows_expected_normal_content(authenticated_page, base_url, normal_record_id):
    """Normal record's XSLT output contains title, instrument, motivation, and counts."""
    page = authenticated_page
    page.goto(f"{base_url}/data?id={normal_record_id}")
    page.wait_for_load_state("networkidle")

    expect(page.locator(".list-record-title")).to_contain_text(
        "Test record with a multi-dataset file"
    )
    expect(page.locator("#instr-badge")).to_contain_text("FEI Titan TEM")
    expect(page.locator(".motivation-text")).to_contain_text(
        "Testing of the NexusLIMS frontend"
    )
    expect(page.locator(".list-record-experimenter")).to_contain_text("Ned Land")
    expect(page.locator("#summary-info")).to_contain_text("48 data files in 8 activities")
    # Normal record must NOT trigger the simple display path.
    assert page.locator(".simple-display").count() == 0
    assert page.locator("#simple-warning-inner-div").count() == 0


def test_simple_display_record_renders_warning(
    authenticated_page, base_url, simple_display_record_id
):
    """Large record triggers the simple display wrapper class and warning alert."""
    page = authenticated_page
    page.goto(f"{base_url}/data?id={simple_display_record_id}")
    page.wait_for_load_state("networkidle")

    assert page.locator(".simple-display").count() > 0, (
        "Expected .simple-display wrapper class on a 200-dataset record"
    )
    expect(page.locator("#simple-display-row")).to_be_visible()
    expect(page.locator("#simple-warning-inner-div")).to_be_visible()
    expect(page.locator("#simple-warning-inner-div")).to_contain_text(
        "simplified representation"
    )


def test_simple_display_shows_expected_content(
    authenticated_page, base_url, simple_display_record_id
):
    """Simple-display record's XSLT output contains title, instrument, motivation, and counts."""
    page = authenticated_page
    page.goto(f"{base_url}/data?id={simple_display_record_id}")
    page.wait_for_load_state("networkidle")

    expect(page.locator(".list-record-title")).to_contain_text(
        "Test record to trigger simple display"
    )
    expect(page.locator("#instr-badge")).to_contain_text("FEI Titan STEM")
    expect(page.locator(".motivation-text")).to_contain_text(
        "200 datasets should trigger simple display"
    )
    expect(page.locator(".list-record-experimenter")).to_contain_text("Ned Land")
    expect(page.locator("#summary-info")).to_contain_text("200 data files in 8 activities")
    # Simple display MUST be active for this record.
    assert page.locator(".simple-display").count() > 0
