"""E2E tests for general annotator behaviour, title editing, keyboard shortcuts, and error banners.

None of the tests in this module save to CDCS, so they are safe to run in parallel
with other annotator test modules.
"""

import re

from playwright.sync_api import expect


class TestAnnotatorGeneral:
    """Smoke tests and basic interactions that apply to the annotator as a whole."""

    def test_annotator_loads(self, annotator_page):
        """Annotator page renders without error."""
        page = annotator_page
        expect(page.locator("#annotate-save-btn")).to_be_visible()
        expect(page.locator("#nx-title-display")).to_be_visible()

    def test_title_inline_edit(self, annotator_page):
        """Clicking the title edit button opens an inline input."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        expect(inline_input).to_be_visible()

    def test_title_edit_marks_dirty(self, annotator_page):
        """Changing the title marks the title bar as dirty."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        inline_input.fill("E2E Test Title Change")
        inline_input.press("Enter")
        expect(page.locator("#nx-title-bar")).to_have_class(
            re.compile(r"nx-title-dirty")
        )

    def test_description_textarea_accepts_input(self, annotator_page):
        """Description textareas accept text input."""
        page = annotator_page
        textareas = page.locator(".annotate-textarea").all()
        assert textareas, "Canonical annotator record has no description textareas"
        first_ta = textareas[0]
        first_ta.fill("E2E test description content")
        expect(first_ta).to_have_value("E2E test description content")

    def test_add_sample(self, annotator_page):
        """Clicking 'Add Sample' opens the sample modal."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        modal = page.locator("#nx-sample-modal")
        expect(modal).to_be_visible()

    def test_save_sample_from_modal(self, annotator_page):
        """Adding a sample via the modal renders it in the sample list."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("E2E Test Sample")
        save_btn = page.locator("#nx-sample-modal-save")
        expect(save_btn).to_be_enabled()
        save_btn.click()
        expect(page.locator("#nx-sample-modal")).to_be_hidden()
        expect(page.locator("#nx-samples-list")).to_contain_text("E2E Test Sample")

    def test_pending_changes_modal_on_navigation(self, annotator_page):
        """Making a change reveals #nx-view-changes-btn which opens the pending-changes modal."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        inline_input.fill("Unsaved E2E Change")
        inline_input.press("Enter")

        view_changes_btn = page.locator("#nx-view-changes-btn")
        view_changes_btn.wait_for(state="visible")
        view_changes_btn.click()
        modal = page.locator("#nx-pending-changes-modal")
        expect(modal).to_be_visible()


class TestTitleEditBehavior:
    """Keyboard and focus behavior of the inline title editor."""

    def test_escape_cancels_edit_without_marking_dirty(self, annotator_page):
        """Pressing Escape discards the typed value and does not mark the bar dirty."""
        page = annotator_page
        original = page.locator("#nx-title-display").inner_text()
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Should Not Be Saved")
        inp.press("Escape")
        inp.wait_for(state="hidden")

        expect(page.locator("#nx-title-bar")).not_to_have_class(
            re.compile(r"nx-title-dirty")
        )
        expect(page.locator("#nx-title-display")).to_have_text(original)

    def test_blur_commits_edit_and_marks_dirty(self, annotator_page):
        """Clicking away from the title input saves the new value and marks dirty."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Blur Committed Title")
        page.locator("body").click()
        inp.wait_for(state="hidden")

        expect(page.locator("#nx-title-display")).to_have_text("Blur Committed Title")
        expect(page.locator("#nx-title-bar")).to_have_class(
            re.compile(r"nx-title-dirty")
        )


class TestKeyboardAndToolbar:
    """Non-saving keyboard shortcut and toolbar interactions."""

    def test_help_modal_opens(self, annotator_page):
        """Clicking the '?' button opens the help modal."""
        page = annotator_page
        page.locator("button[data-bs-target='#annotate-help-modal']").click()
        expect(page.locator("#annotate-help-modal")).to_be_visible()

    def test_cancel_navigates_to_detail_page(self, annotator_page, test_record_id):
        """Clicking Cancel navigates to the record detail page."""
        page = annotator_page
        page.locator("a.btn.btn-outline-secondary:has-text('Cancel')").click()
        expect(page).to_have_url(re.compile(rf"[?&]id={test_record_id}(?:&|$)"))


class TestErrorBanners:
    """Error conditions render the appropriate alert banners."""

    def test_error_query_param_shows_danger_alert(self, annotator_page, base_url, test_record_id):
        """Navigating to the annotator with ?error=1 renders the error alert."""
        page = annotator_page
        page.goto(
            f"{base_url}/annotate/{test_record_id}/?error=1",
            wait_until="domcontentloaded",
        )
        expect(page.locator(".alert-danger")).to_be_visible()
