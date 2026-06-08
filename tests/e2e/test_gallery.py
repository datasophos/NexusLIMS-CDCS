"""E2E tests for the nexuslims_gallery jumbotron page."""

import pytest
from playwright.sync_api import expect


@pytest.fixture
def gallery_page(unauthenticated_page, base_url):
    """Load the gallery page without authentication."""
    page = unauthenticated_page
    page.goto(f"{base_url}/gallery/")
    return page


def test_gallery_loads_without_auth(unauthenticated_page, base_url):
    """Gallery page returns 200 and loads without requiring login."""
    response = unauthenticated_page.goto(f"{base_url}/gallery/")
    assert response.status == 200


def test_gallery_uses_nexuslims_favicon(gallery_page):
    """Standalone gallery page declares the NexusLIMS favicon."""
    favicon = gallery_page.locator("link[rel='icon']")
    expect(favicon).to_have_attribute(
        "href", "/static/nexuslims/img/favicon.png"
    )


def test_fullscreen_button_has_tooltip(gallery_page):
    """Fullscreen control tells users what the button does."""
    btn = gallery_page.locator("#nx-fullscreen-btn")
    expect(btn).to_have_attribute("title", "Make gallery full screen")
    expect(btn).to_have_attribute("aria-label", "Make gallery full screen")


def test_gallery_shows_preview_image(gallery_page):
    """After the first API call, a preview image downloads and renders."""
    img = gallery_page.locator("#nx-gallery-img")
    gallery_page.wait_for_function(
        "() => document.getElementById('nx-gallery-img').complete"
        " && document.getElementById('nx-gallery-img').naturalWidth > 0"
    )
    assert img.get_attribute("src")


def test_gallery_shows_record_title(gallery_page):
    """A record title appears in the info badge."""
    gallery_page.wait_for_function(
        "() => document.getElementById('nx-gallery-title').textContent.trim() !== ''"
    )
    title = gallery_page.locator("#nx-gallery-title").text_content()
    assert title.strip() != ""
    expect(gallery_page.locator("#nx-gallery-title")).to_have_attribute("title", title)


def test_gallery_title_never_exceeds_two_lines(gallery_page):
    """Narrow layouts clip the record title after two complete lines."""
    gallery_page.set_viewport_size({"width": 980, "height": 1160})
    gallery_page.wait_for_function(
        "() => document.getElementById('nx-gallery-title').textContent.trim() !== ''"
    )
    dimensions = gallery_page.locator("#nx-gallery-title").evaluate(
        """el => ({
            height: el.getBoundingClientRect().height,
            lineHeight: parseFloat(getComputedStyle(el).lineHeight),
        })"""
    )
    assert dimensions["height"] <= dimensions["lineHeight"] * 2 + 1


def test_gallery_labels_dataset_description(gallery_page):
    """The second footer line is identified as a dataset description."""
    gallery_page.wait_for_function(
        "() => document.getElementById('nx-gallery-title').textContent.trim() !== ''"
    )
    expect(gallery_page.locator(".nx-gallery-desc-label")).to_have_text("Dataset:")
    expect(gallery_page.locator("#nx-gallery-desc-text")).not_to_be_empty()


def test_right_arrow_key_advances_slide(gallery_page):
    """ArrowRight fetches a slide and renders the returned title and preview."""
    gallery_page.wait_for_function(
        "() => document.getElementById('nx-gallery-title').textContent.trim() !== ''"
    )
    with gallery_page.expect_response(
        lambda r: "/gallery/api/next/" in r.url, timeout=5000
    ) as response_info:
        gallery_page.keyboard.press("ArrowRight")
    slide = response_info.value.json()
    assert "error" not in slide
    expect(gallery_page.locator("#nx-gallery-title")).to_have_text(slide["title"])
    expect(gallery_page.locator("#nx-gallery-img")).to_have_attribute(
        "src", slide["preview_url"]
    )
    featured_badge = gallery_page.locator("#nx-gallery-featured")
    if slide["featured"]:
        expect(featured_badge).to_be_visible()
        expect(featured_badge).to_contain_text("Featured")
    else:
        expect(featured_badge).to_be_hidden()


def test_view_record_link_opens_record(gallery_page):
    """'View record' opens the corresponding public detail page."""
    gallery_page.wait_for_function(
        "() => document.getElementById('nx-gallery-link').getAttribute('href') !== '#'"
    )
    with gallery_page.expect_popup() as popup_info:
        gallery_page.locator("#nx-gallery-link").click()
    detail_page = popup_info.value
    detail_page.wait_for_load_state("networkidle")
    assert "/data?id=" in detail_page.url
    expect(detail_page.locator(".list-record-title")).not_to_be_empty()
