from playwright.sync_api import sync_playwright


def apply_to_job(url, button_text, resume_path):
    with sync_playwright() as p:
        # Launching with 'headless=False' so you can see it working (useful for debugging)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url)
            # Wait for the page to load
            page.wait_for_load_state("networkidle")

            # Try to find and click the apply button
            page.click(f"text={button_text}")

            # If there is a file upload input:
            # page.set_input_files('input[type="file"]', resume_path)

            return f"Successfully clicked {button_text} on {url}. (Manual check recommended for first run)"
        except Exception as e:
            return f"Job application failed: {e}"
        finally:
            # We keep the browser open for a few seconds so it doesn't look like a bot
            page.wait_for_timeout(3000)
            browser.close()