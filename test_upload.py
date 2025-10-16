import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def cleanup_downloaded_file():
    yield
    tmp_dir = Path("tmp_downloads")
    if tmp_dir.exists():
        for file in tmp_dir.iterdir():
            if file.is_file():
                file.unlink()
                print(f"Deleted: {file}")

@pytest.mark.parametrize(
    "search_term,media_type",
    [
        ("Flowers", "photo"),
        ("Flowers", "video")
    ]
)
def test_download_media(search_term, media_type, cleanup_downloaded_file):
    
    tmp_dir = Path("tmp_downloads")
    tmp_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        # Navigate to Pexels search page
        search_url = f"https://www.pexels.com/search/{'videos' if media_type=='video' else ''}/{search_term}/"
        page.goto(search_url)
        page.wait_for_load_state("networkidle")
        
        # Click on the first media item
        media_locator = page.locator("//a[@data-testid='next-link']//img").first
        media_locator.scroll_into_view_if_needed()
        media_locator.click()

        # Wait for download button
        download_locator = page.wait_for_selector("(//a[.//span[contains(text(), 'Free download')]])[last()]")
        with page.expect_download() as download_info:
            download_locator.click()
        media_download = download_info.value
        media_path = tmp_dir / media_download.suggested_filename
        media_download.save_as(media_path)
        print(f"{media_type.capitalize()} downloaded: {media_path}")

        # Upload to file.io
        page.goto("https://www.file.io/")
        page.wait_for_load_state("networkidle")
        upload_input = page.locator('//input[@id="select-files-input"]').first
        upload_input.set_input_files(media_path)

        # Wait for upload to complete
        page.wait_for_selector("text=Your files are ready", timeout=120000)
        
        page.get_by_role("button", name="Share").click()
        shareable_link = page.locator("//input[@type='text']").input_value()
        print(f"{media_type.capitalize()} Shareable link: {shareable_link}")
    
        browser.close()
