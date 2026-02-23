import time
import random
from browser_engine import EdgeEngine
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def deep_research(query: str, client) -> str:
    driver = EdgeEngine.get_driver()
    # HARD FIX: Set global timeout
    driver.set_page_load_timeout(15)

    collected = []
    SKIP_DOMAINS = ["pinterest.com", "quora.com", "amazon.com", "ebay.com"]

    def scrape_smart(url):
        try:
            print(f"--- 🚀 Navigating to: {url} ---")
            try:
                driver.get(url)
            except TimeoutException:
                print(f"⚠️ {url} hung. Force-stopping to read partial content...")
                driver.execute_script("window.stop();")

            time.sleep(random.uniform(1, 2))
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")

            driver.execute_script("""
                const junk = document.querySelectorAll('nav, footer, script, style, .ads, .cookie-banner');
                junk.forEach(el => el.remove());
            """)

            elements = driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, article")
            text_blocks = [el.text for el in elements if len(el.text) > 60]
            content = "\n\n".join(text_blocks)

            if len(content) > 200:
                collected.append(f"Source: {url}\n{content[:4000]}")
                print(f"✅ Scraped: {url}")
        except Exception as e:
            print(f"❌ Aborted {url}: {e}")

    try:
        # --- FIXED SEARCH BLOCK ---
        print(f"--- 🔍 Searching DuckDuckGo for: {query} ---")
        try:
            driver.get(f"https://duckduckgo.com/?q={query}")
        except TimeoutException:
            driver.execute_script("window.stop();")

        try:
            wait = WebDriverWait(driver, 8)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.result__a, [data-testid='result-title-a']")))
        except:
            return "Search timed out or failed to load results."

        anchors = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a'], a.result__a")
        links = []
        for a in anchors:
            href = a.get_attribute("href")
            if href and "http" in href and not any(s in href for s in SKIP_DOMAINS):
                links.append(href)
            if len(links) >= 8: break

        for link in links:
            scrape_smart(link)
            if len(collected) >= 5: break

        if not collected: return "Research failed: No content retrieved."

        response = client.chat.completions.create(
            model="llama3.1",
            messages=[
                {"role": "system", "content": "Analyze web data and provide a detailed report."},
                {"role": "user", "content": f"Topic: {query}\n\nData:\n{''.join(collected)}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"System Error: {e}"