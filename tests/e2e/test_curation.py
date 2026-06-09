"""E2E tests for the rating and featuring curation system on the detail page.

Tests are split into four groups:
  - Anonymous display: verify pre-baked curation state is visible (read-only)
  - Editor display: verify hover reveals controls for authenticated editors
  - Editor interaction: click star/circles/clear and verify DOM updates + API calls
  - Persistence: verify state survives page reload

All tests that modify state request the reset_curation fixture, which patches the
record back to canonical XML before the test runs.
"""

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import reset_records


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def reset_curation(auth_state, base_url, curation_record_id):
    """Patch the curation record back to its canonical XML before each test.

    Passes only the curation record title so reset_records() skips all other
    resettable records, keeping this per-test reset fast.
    """
    cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
    reset_records(
        cookies,
        base_url,
        by_title={"Example record curation": curation_record_id},
    )


# ---------------------------------------------------------------------------
# Locator helpers (all operate on flat .nx-name-row index, 0-based)
# ---------------------------------------------------------------------------


def _go(page, base_url, record_id):
    page.goto(f"{base_url}/data?id={record_id}")
    page.wait_for_load_state("networkidle")


def _name_row(page, idx):
    return page.locator(".nx-name-row").nth(idx)


def _tr(page, idx):
    """The <tr> ancestor of dataset idx's name row — the hover target."""
    return _name_row(page, idx).locator("xpath=ancestor::tr[1]")


def _hover_row(page, idx):
    """Scroll a dataset row into view without smooth-scroll action instability."""
    row = _tr(page, idx)
    row.evaluate(
        "el => el.scrollIntoView({behavior: 'instant', block: 'center'})"
    )
    page.evaluate(
        """() => new Promise(resolve =>
            requestAnimationFrame(() => requestAnimationFrame(resolve))
        )"""
    )
    row.hover()


def _star(page, idx):
    return _name_row(page, idx).locator(".nx-star")


def _click_star(page, idx):
    """Dispatch a star click and wait for the feature request to succeed."""
    star = _star(page, idx)
    expect(star).to_be_visible()
    with page.expect_response(lambda response: response.url.endswith("/feature/")) as info:
        star.dispatch_event("click")
    assert info.value.ok
    assert info.value.json()["ok"]


def _group(page, idx):
    return _name_row(page, idx).locator(".nx-rating-group")


def _filled(page, idx):
    return _name_row(page, idx).locator(".nx-rc.nx-rc--filled")


def _circle(page, idx, value):
    """A single rating circle by its data-value (1-5)."""
    return _name_row(page, idx).locator(f".nx-rc[data-value='{value}']")


def _click_circle(page, idx, value):
    """Dispatch a circle click and wait for the rating request to succeed."""
    circle = _circle(page, idx, value)
    expect(circle).to_be_visible()
    with page.expect_response(lambda response: response.url.endswith("/rate/")) as info:
        circle.dispatch_event("click")
    assert info.value.ok
    assert info.value.json()["ok"]


def _clear(page, idx):
    return _name_row(page, idx).locator(".nx-rc-clear")


def _click_clear(page, idx):
    """Dispatch a clear click and wait for the rating request to succeed."""
    clear = _clear(page, idx)
    expect(clear).to_be_visible()
    with page.expect_response(lambda response: response.url.endswith("/rate/")) as info:
        clear.dispatch_event("click")
    assert info.value.ok
    assert info.value.json()["ok"]


# ---------------------------------------------------------------------------
# Anonymous display tests — pre-baked state, unauthenticated_page
# Dataset 0: rated 3 + featured | Dataset 1: rated 5 | Dataset 2: featured only
# Dataset 3: no curation        | Dataset 4: no curation
# ---------------------------------------------------------------------------


def test_anonymous_featured_star_visible(
    reset_curation, unauthenticated_page, base_url, curation_record_id
):
    """Dataset 0 (featured) shows a gold star to anonymous users."""
    page = unauthenticated_page
    _go(page, base_url, curation_record_id)
    expect(_star(page, 0)).to_be_visible()
    expect(_star(page, 0)).to_have_class(re.compile(r"nx-star--featured"))


def test_anonymous_featured_star_tooltip(
    reset_curation, unauthenticated_page, base_url, curation_record_id
):
    """Star on dataset 0 has the XSLT read-only tooltip 'Featured dataset'."""
    page = unauthenticated_page
    _go(page, base_url, curation_record_id)
    expect(_star(page, 0)).to_have_attribute("title", "Featured dataset")


def test_anonymous_rating_circles_visible(
    reset_curation, unauthenticated_page, base_url, curation_record_id
):
    """Dataset 0 shows 3 filled circles; dataset 1 shows 5 filled circles."""
    page = unauthenticated_page
    _go(page, base_url, curation_record_id)

    expect(_group(page, 0)).to_be_visible()
    expect(_group(page, 0)).to_have_attribute("data-current-rating", "3")
    expect(_filled(page, 0)).to_have_count(3)

    expect(_group(page, 1)).to_be_visible()
    expect(_group(page, 1)).to_have_attribute("data-current-rating", "5")
    expect(_filled(page, 1)).to_have_count(5)


def test_anonymous_unfeatured_unrated_controls_hidden(
    reset_curation, unauthenticated_page, base_url, curation_record_id
):
    """Dataset 3 (no curation) shows no gold star and no visible rating group."""
    page = unauthenticated_page
    _go(page, base_url, curation_record_id)

    expect(_star(page, 3)).not_to_have_class(re.compile(r"nx-star--featured"))
    expect(_star(page, 3)).not_to_be_visible()

    expect(_group(page, 3)).to_have_attribute("data-current-rating", "0")
    expect(_group(page, 3)).not_to_be_visible()


def test_anonymous_clear_button_never_visible(
    reset_curation, unauthenticated_page, base_url, curation_record_id
):
    """The clear button is never visible to anonymous users, even for rated datasets."""
    page = unauthenticated_page
    _go(page, base_url, curation_record_id)
    # Dataset 0 is rated 3 — clear button must still be hidden
    expect(_clear(page, 0)).not_to_be_visible()
    # Dataset 1 is rated 5 — same expectation
    expect(_clear(page, 1)).not_to_be_visible()


def test_anonymous_controls_not_interactive(
    reset_curation, unauthenticated_page, base_url, curation_record_id
):
    """Star and circles use cursor:default for anonymous users (no annotate.css loaded)."""
    page = unauthenticated_page
    _go(page, base_url, curation_record_id)

    star_cursor = _star(page, 0).evaluate(
        "el => window.getComputedStyle(el).cursor"
    )
    assert star_cursor in ("default", "auto"), (
        f"Expected cursor:default on star, got {star_cursor!r}"
    )

    circle_cursor = _circle(page, 0, 1).evaluate(
        "el => window.getComputedStyle(el).cursor"
    )
    assert circle_cursor in ("default", "auto"), (
        f"Expected cursor:default on circle, got {circle_cursor!r}"
    )


# ---------------------------------------------------------------------------
# Editor display tests — authenticated_page, hover reveals controls
# ---------------------------------------------------------------------------


def test_editor_controls_hidden_until_hover(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Star and circles on dataset 3 are not visible before the row is hovered."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    expect(_star(page, 3)).not_to_be_visible()
    expect(_group(page, 3)).not_to_be_visible()


def test_editor_hover_reveals_star(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Hovering dataset 3's table row makes the .nx-star visible."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    expect(_star(page, 3)).not_to_be_visible()
    _hover_row(page, 3)
    expect(_star(page, 3)).to_be_visible()


def test_editor_hover_reveals_circles(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Hovering dataset 3's table row makes the .nx-rating-group visible."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    expect(_group(page, 3)).not_to_be_visible()
    _hover_row(page, 3)
    expect(_group(page, 3)).to_be_visible()


# ---------------------------------------------------------------------------
# Editor interaction — featuring
# ---------------------------------------------------------------------------


def test_editor_click_star_features_dataset(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Clicking the star on dataset 3 (unfeatured) adds nx-star--featured and updates tooltip."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 3)
    star = _star(page, 3)
    expect(star).to_have_attribute("title", "Click to mark as featured")
    _click_star(page, 3)
    expect(star).to_have_class(re.compile(r"nx-star--featured"))
    expect(star).to_have_attribute("title", "Featured — click to unfeature")


def test_editor_click_featured_star_unfeatures(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Clicking the featured star on dataset 0 removes nx-star--featured."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 0)
    star = _star(page, 0)
    expect(star).to_have_class(re.compile(r"nx-star--featured"))
    _click_star(page, 0)
    expect(star).not_to_have_class(re.compile(r"nx-star--featured"))
    expect(star).to_have_attribute("title", "Click to mark as featured")


# ---------------------------------------------------------------------------
# Editor interaction — rating
# ---------------------------------------------------------------------------


def test_editor_click_circle_sets_rating(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Clicking circle 3 on dataset 4 (unrated) fills 3 circles and sets data-current-rating."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 4)
    _click_circle(page, 4, 3)
    expect(_group(page, 4)).to_have_attribute("data-current-rating", "3")
    expect(_filled(page, 4)).to_have_count(3)


def test_editor_hover_preview_fill(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Hovering circle 5 on unrated dataset 4 transiently fills all 5; moving away restores 0."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 4)
    circle = _circle(page, 4, 5)
    expect(circle).to_be_visible()
    circle.dispatch_event("mouseover")
    expect(_filled(page, 4)).to_have_count(5)
    _group(page, 4).dispatch_event("mouseleave")
    expect(_filled(page, 4)).to_have_count(0)


def test_editor_click_same_circle_clears_rating(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Clicking circle N on a dataset already rated N clears the rating to 0."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    # Dataset 0 starts rated 3; clicking circle 3 toggles it off
    _hover_row(page, 0)
    _click_circle(page, 0, 3)
    expect(_group(page, 0)).to_have_attribute("data-current-rating", "0")
    expect(_filled(page, 0)).to_have_count(0)


def test_editor_clear_button_hidden_when_unrated(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """The clear button is not visible on hover for an unrated dataset (dataset 3)."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 3)
    expect(_clear(page, 3)).not_to_be_visible()


def test_editor_clear_button_visible_when_rated(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """The clear button is visible on hover for dataset 0 (rated 3)."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 0)
    expect(_clear(page, 0)).to_be_visible()


def test_editor_clear_button_clears_rating(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Clicking clear on dataset 0 (rated 3) posts rating=0 and empties the circles."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 0)
    _click_clear(page, 0)
    expect(_group(page, 0)).to_have_attribute("data-current-rating", "0")
    expect(_filled(page, 0)).to_have_count(0)


# ---------------------------------------------------------------------------
# Persistence tests — set state, reload, verify saved
# The expect() on the DOM update after click implicitly waits for the server
# to confirm the save (JS only updates the DOM inside the .then() callback).
# ---------------------------------------------------------------------------


def test_rating_persists_after_reload(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Rating 4 set on dataset 4 survives a page reload."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 4)
    _click_circle(page, 4, 4)
    expect(_group(page, 4)).to_have_attribute("data-current-rating", "4")
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(_filled(page, 4)).to_have_count(4)
    expect(_group(page, 4)).to_have_attribute("data-current-rating", "4")


def test_featured_persists_after_reload(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Featuring dataset 3 survives a page reload."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 3)
    _click_star(page, 3)
    expect(_star(page, 3)).to_have_class(re.compile(r"nx-star--featured"))
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(_star(page, 3)).to_have_class(re.compile(r"nx-star--featured"))


def test_clear_rating_persists_after_reload(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Clearing rating via clear button on dataset 0 survives a page reload."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 0)
    _click_clear(page, 0)
    expect(_group(page, 0)).to_have_attribute("data-current-rating", "0")
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(_filled(page, 0)).to_have_count(0)
    expect(_group(page, 0)).to_have_attribute("data-current-rating", "0")


def test_unfeature_persists_after_reload(
    reset_curation, authenticated_page, base_url, curation_record_id
):
    """Unfeaturing dataset 0 (initially featured) survives a page reload."""
    page = authenticated_page
    _go(page, base_url, curation_record_id)
    _hover_row(page, 0)
    _click_star(page, 0)
    expect(_star(page, 0)).not_to_have_class(re.compile(r"nx-star--featured"))
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(_star(page, 0)).not_to_have_class(re.compile(r"nx-star--featured"))
