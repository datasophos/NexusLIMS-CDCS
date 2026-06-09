"""E2E tests for annotator operations that commit changes to CDCS.

These tests are the only annotator tests that actually save to the database.
Keeping them isolated in one file ensures they run sequentially on a single
worker, preventing concurrent-write conflicts while the non-saving annotator
modules run in parallel.
"""

import datetime
import re

from playwright.sync_api import expect

from tests.e2e.helpers import add_sample, add_new_activity


class TestPersistence:
    """Tests that save mutations to the live CDCS record."""

    def test_save_button_submits(self, annotator_page, base_url, test_record_id):
        """Saving edits redirects to the detail page and displays the updated title."""
        page = annotator_page
        new_title = f"E2E Save Test {datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        inline_input.fill(new_title)
        inline_input.press("Enter")

        with page.expect_navigation():
            page.locator("#annotate-save-btn").click()

        expect(page).to_have_url(re.compile(rf"[?&]id={test_record_id}(?:&|$)"))
        title_el = page.locator(".list-record-title.page-header")
        expect(title_el).to_contain_text(new_title)

    def test_ctrl_enter_submits_form(self, annotator_page, base_url, test_record_id):
        """Pressing Ctrl+Enter saves the form and redirects to the detail page."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Ctrl Enter Save")
        inp.press("Enter")
        with page.expect_navigation():
            page.keyboard.press("Control+Enter")
        expect(page).to_have_url(re.compile(rf"[?&]id={test_record_id}(?:&|$)"))
        expect(page.locator(".list-record-title")).to_contain_text("Ctrl Enter Save")

    def test_toolbar_save_button_submits_form(self, annotator_page, base_url, test_record_id):
        """Clicking the toolbar's Save button submits the form."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Toolbar Save Button")
        inp.press("Enter")
        page.locator("#nx-toolbar-save-btn").wait_for(state="visible")
        with page.expect_navigation():
            page.locator("#nx-toolbar-save-btn").click()
        expect(page).to_have_url(re.compile(rf"[?&]id={test_record_id}(?:&|$)"))
        expect(page.locator(".list-record-title")).to_contain_text(
            "Toolbar Save Button"
        )

    def test_saved_sample_appears_on_reload(self, annotator_page, base_url, test_record_id):
        """A sample added and saved is still present when the annotator reloads."""
        page = annotator_page
        unique = datetime.datetime.now().strftime("%H%M%S%f")
        name = f"Persist-{unique}"
        add_sample(page, name)
        with page.expect_navigation():
            page.locator("#annotate-save-btn").click()

        page.goto(
            f"{base_url}/annotate/{test_record_id}/", wait_until="domcontentloaded"
        )
        expect(page.locator("#nx-samples-list")).to_contain_text(name)

    def test_save_with_pending_move_succeeds(self, annotator_page, base_url, test_record_id):
        """Saving with a pending move redirects to the detail page without an error."""
        page = annotator_page
        assert page.locator(".nx-select-cb").count() > 0, (
            "Canonical annotator record has no datasets to move"
        )

        activity_count = page.locator(".nx-sortable-activity").count()
        moved_name = page.locator(".nx-dataset-name").first.inner_text().strip()
        new_seqno = add_new_activity(page)
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-dropdown-btn").wait_for(state="visible")
        page.locator("#nx-move-dropdown-btn").click()
        page.locator(f"#nx-move-dropdown [data-seqno='{new_seqno}']").click()

        with page.expect_navigation():
            page.locator("#annotate-save-btn").click()

        expect(page).to_have_url(re.compile(rf"[?&]id={test_record_id}(?:&|$)"))
        assert "error" not in page.url

        page.goto(
            f"{base_url}/annotate/{test_record_id}/", wait_until="domcontentloaded"
        )
        expect_count = activity_count + 1
        expect(page.locator(".nx-sortable-activity")).to_have_count(expect_count)
        expect(page.locator(".nx-sortable-activity").last).to_contain_text(moved_name)
