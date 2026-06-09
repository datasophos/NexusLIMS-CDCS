"""E2E tests for the annotator's sample management UI.

None of the tests in this module save to CDCS, so they are safe to run in parallel
with other annotator test modules.
"""

import re

from playwright.sync_api import expect

from tests.e2e.helpers import add_sample


class TestSampleEditing:
    """Edit an existing sample via the sample modal."""

    def test_edit_opens_prepopulated_modal(self, annotator_page):
        """Clicking Edit on a sample row opens the modal pre-filled with its name."""
        page = annotator_page
        add_sample(page, "Original Name")

        page.locator("#nx-samples-list > div").filter(has_text="Original Name").locator(
            "button:has-text('Edit')"
        ).click()
        page.locator("#nx-sample-modal").wait_for(state="visible")

        expect(page.locator("#nx-sample-modal-title")).to_have_text("Edit Sample")
        expect(page.locator("#nx-sample-name")).to_have_value("Original Name")

    def test_edit_updates_name_in_list(self, annotator_page):
        """Saving an edited sample reflects the new name in the samples list."""
        page = annotator_page
        add_sample(page, "Before Edit")

        page.locator("#nx-samples-list > div").filter(has_text="Before Edit").locator(
            "button:has-text('Edit')"
        ).click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("After Edit")
        save_btn = page.locator("#nx-sample-modal-save")
        expect(save_btn).to_be_enabled()
        save_btn.click()
        expect(page.locator("#nx-sample-modal")).to_be_hidden()
        expect(page.locator("#nx-samples-list")).to_contain_text("After Edit")
        expect(page.locator("#nx-samples-list")).not_to_contain_text("Before Edit")


class TestSampleDeletion:
    """Delete samples, including those assigned to activities."""

    def test_delete_unassigned_sample_removes_from_list(self, annotator_page):
        """Deleting an unassigned sample removes it from the list without a dialog."""
        page = annotator_page
        add_sample(page, "Delete Me")
        expect(page.locator("#nx-samples-list")).to_contain_text("Delete Me")

        page.locator("#nx-samples-list > div").filter(has_text="Delete Me").locator(
            "button[title='Delete sample']"
        ).click()
        expect(page.locator("#nx-samples-list")).not_to_contain_text("Delete Me")

    def test_delete_assigned_sample_shows_confirm_dialog(self, annotator_page):
        """Deleting a sample that is assigned to an activity triggers a confirm dialog."""
        page = annotator_page
        assert page.locator(".nx-activity-sample").count() > 0, (
            "Canonical annotator record has no activity sample dropdowns"
        )

        add_sample(page, "Assigned Sample")
        page.locator(".nx-activity-sample").first.select_option(label="Assigned Sample")

        dialog_seen = []
        page.once("dialog", lambda d: (dialog_seen.append(True), d.dismiss()))
        page.locator("#nx-samples-list > div").filter(has_text="Assigned Sample").locator(
            "button[title='Delete sample']"
        ).click()
        assert dialog_seen, "Expected a confirmation dialog but none appeared"

    def test_dismiss_confirm_keeps_sample_in_list(self, annotator_page):
        """Dismissing the confirmation dialog leaves the sample in the list."""
        page = annotator_page
        assert page.locator(".nx-activity-sample").count() > 0, (
            "Canonical annotator record has no activity sample dropdowns"
        )

        add_sample(page, "Keep Me")
        page.locator(".nx-activity-sample").first.select_option(label="Keep Me")

        page.on("dialog", lambda d: d.dismiss())
        page.locator("#nx-samples-list > div").filter(has_text="Keep Me").locator(
            "button[title='Delete sample']"
        ).click()
        page.locator("#nx-samples-list").wait_for()
        expect(page.locator("#nx-samples-list")).to_contain_text("Keep Me")


class TestSampleValidation:
    """Sample modal enforces a non-empty name."""

    def test_empty_name_adds_invalid_class(self, annotator_page):
        """Saving without a name adds the is-invalid class to the name input."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("")
        page.locator("#nx-sample-modal-save").click()
        expect(page.locator("#nx-sample-name")).to_have_class(
            re.compile(r"is-invalid")
        )

    def test_empty_name_keeps_modal_open(self, annotator_page):
        """Saving without a name does not dismiss the modal."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("")
        page.locator("#nx-sample-modal-save").click()
        expect(page.locator("#nx-sample-modal")).to_be_visible()


class TestSamplePID:
    """PID values render as links when they look like URLs, otherwise as text."""

    def test_url_pid_renders_as_anchor(self, annotator_page):
        """An https:// PID renders as an <a> element with the correct href."""
        page = annotator_page
        add_sample(page, "PID Sample", pid="https://doi.org/10.1234/sample")
        expect(
            page.locator(
                "#nx-samples-list a[href='https://doi.org/10.1234/sample']"
            )
        ).to_be_visible()

    def test_non_url_pid_renders_as_plain_text(self, annotator_page):
        """A PID without an http scheme renders as text (no anchor element)."""
        page = annotator_page
        add_sample(page, "Plain PID Sample", pid="ark:/99999/fk4test")
        expect(page.locator("#nx-samples-list")).to_contain_text("ark:/99999/fk4test")
        expect(
            page.locator("#nx-samples-list a[href='ark:/99999/fk4test']")
        ).to_have_count(0)


class TestSampleElements:
    """Element tag input in the sample modal."""

    def test_add_element_shows_badge_chip(self, annotator_page):
        """Typing a valid symbol and pressing Enter adds a badge in the tags container."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-elements-input").fill("Fe")
        page.locator("#nx-elements-input").press("Enter")
        expect(page.locator("#nx-elements-tags .badge")).to_have_count(1)
        expect(page.locator("#nx-elements-tags")).to_contain_text("Fe")

    def test_remove_element_via_x_button(self, annotator_page):
        """Clicking × on an element badge removes it from the tag list."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-elements-input").fill("Au")
        page.locator("#nx-elements-input").press("Enter")
        page.locator("#nx-elements-tags .badge button").first.click()
        expect(page.locator("#nx-elements-tags")).not_to_contain_text("Au")

    def test_elements_appear_as_chips_in_sample_list(self, annotator_page):
        """Elements saved with a sample appear as code chips in the sample list."""
        page = annotator_page
        add_sample(page, "Alloy Sample", elements=["Ni", "Cr"])
        expect(page.locator("#nx-samples-list")).to_contain_text("Ni")
        expect(page.locator("#nx-samples-list")).to_contain_text("Cr")
