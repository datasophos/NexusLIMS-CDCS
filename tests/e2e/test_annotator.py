"""E2E tests for the annotator record editor."""
import pytest


@pytest.fixture
def annotator_page(authenticated_page, base_url, test_record_id):
    """Navigate to the annotator for the test record."""
    page = authenticated_page
    page.goto(f"{base_url}/annotate/{test_record_id}/")
    page.wait_for_load_state("networkidle")
    return page


def test_annotator_loads(annotator_page):
    """Annotator page renders without error."""
    page = annotator_page
    assert page.locator("#nx-toolbar-save-btn").count() > 0
    assert page.locator("#nx-title-display").count() > 0


def test_title_inline_edit(annotator_page):
    """Clicking the title edit button opens an inline input."""
    page = annotator_page
    page.locator("#nx-title-edit-btn").click()
    inline_input = page.locator("#nx-title-bar input[type='text']")
    inline_input.wait_for(state="visible")
    assert inline_input.is_visible()


def test_title_edit_marks_dirty(annotator_page):
    """Changing the title marks the title bar as dirty."""
    page = annotator_page
    page.locator("#nx-title-edit-btn").click()
    inline_input = page.locator("#nx-title-bar input[type='text']")
    inline_input.wait_for(state="visible")
    inline_input.fill("E2E Test Title Change")
    inline_input.press("Enter")
    assert page.locator("#nx-title-bar.nx-title-dirty").count() > 0


def test_description_textarea_accepts_input(annotator_page):
    """Description textareas accept text input."""
    page = annotator_page
    textareas = page.locator(".annotate-textarea").all()
    if not textareas:
        pytest.skip("No description textareas found on this record")
    first_ta = textareas[0]
    first_ta.fill("E2E test description content")
    assert first_ta.input_value() == "E2E test description content"


def test_add_sample(annotator_page):
    """Clicking 'Add Sample' opens the sample modal."""
    page = annotator_page
    page.locator("#nx-add-sample-btn").click()
    modal = page.locator("#nx-sample-modal")
    modal.wait_for(state="visible")
    assert modal.is_visible()


def test_save_sample_from_modal(annotator_page):
    """Adding a sample via the modal renders it in the sample list."""
    page = annotator_page
    page.locator("#nx-add-sample-btn").click()
    page.locator("#nx-sample-modal").wait_for(state="visible")
    page.locator("#nx-sample-name").fill("E2E Test Sample")
    page.locator("#nx-sample-modal-save").click()
    page.locator("#nx-sample-modal").wait_for(state="hidden")
    assert page.locator("#nx-samples-list").inner_text().find("E2E Test Sample") >= 0


def test_pending_changes_modal_on_navigation(annotator_page, base_url):
    """Navigating away with unsaved changes shows the pending-changes modal."""
    page = annotator_page
    page.locator("#nx-title-edit-btn").click()
    inline_input = page.locator("#nx-title-bar input[type='text']")
    inline_input.wait_for(state="visible")
    inline_input.fill("Unsaved E2E Change")
    inline_input.press("Enter")

    page.locator("a[href='/'], a[href*='/data/']").first.click()
    modal = page.locator("#nx-pending-changes-modal")
    modal.wait_for(state="visible", timeout=5_000)
    assert modal.is_visible()


def test_save_button_submits(annotator_page):
    """Clicking save with no changes completes without error."""
    page = annotator_page
    page.locator("#nx-toolbar-save-btn").click()
    page.wait_for_load_state("networkidle")
    assert "/annotate/" in page.url
