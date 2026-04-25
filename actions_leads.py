import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_engine import EdgeEngine
import pandas as pd
import os

CSV_PATH = r"C:\Users\david\my-ai-agent\bot_files\leads.csv"


def save_lead(center_name, email, city):
    """Writes to CSV only if the lead is unique based on email."""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    # 1. Load existing data
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=["center_name", "email", "city"])

    # 2. CHECK FOR DUPLICATES
    # We check by email because center names can sometimes vary slightly
    if email in df['email'].values:
        print(f"⚠️ Duplicate found for {email}. Skipping save.")
        return f"Skipped {center_name} (Already in database)"

    # 3. Add the new row if it's unique
    new_row = {"center_name": center_name, "email": email, "city": city}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # 4. Save
    df.to_csv(CSV_PATH, index=False)
    return f"Saved {center_name} to leads.csv"


# actions_leads.py - add this function


# Sites to skip - they gate emails behind logins/payments
BLACKLIST = [
    "yelp.com", "bark.com", "tutors.com", "thumbtack.com", "care.com",
    "indeed.com", "linkedin.com", "facebook.com", "instagram.com",
    "twitter.com", "google.com", "yellowpages.com", "trustpilot.com"
]

def find_email_on_page(driver) -> str:
    """Scan page HTML for email addresses using regex."""
    try:
        html = driver.page_source
        # Look for mailto links first (most reliable)
        mailto = re.findall(r'mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', html)
        if mailto:
            return mailto[0]
        # Fallback: raw email pattern in HTML
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', html)
        # Filter out garbage like image files, CSS, etc.
        emails = [e for e in emails if not any(e.endswith(x) for x in ['.png', '.jpg', '.css', '.js', '.svg'])]
        if emails:
            return emails[0]
    except:
        pass
    return None

def hunt_email(driver, base_url) -> str:
    """Visit homepage, then try /contact and /about to find an email."""
    wait = WebDriverWait(driver, 8)
    pages_to_try = [
        base_url,
        base_url.rstrip("/") + "/contact",
        base_url.rstrip("/") + "/contact-us",
        base_url.rstrip("/") + "/about",
    ]

    for page_url in pages_to_try:
        try:
            driver.get(page_url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1)
            email = find_email_on_page(driver)
            if email:
                print(f"--- Found email {email} on {page_url} ---")
                return email
        except:
            continue

    return None


def find_tutoring_leads(city: str) -> str:
    driver = EdgeEngine.get_driver()
    wait = WebDriverWait(driver, 10)
    saved = []
    failed = []

    try:
        # --- Step 1: Google Maps search ---
        query = f"tutoring agencies {city}"
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
        time.sleep(3)  # let map fully load

        # --- Step 2: Scrape business listings from left panel ---
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']")))

        # Scroll the results panel to load more listings
        feed = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
        for _ in range(3):
            driver.execute_script("arguments[0].scrollTop += 1000", feed)
            time.sleep(1)

        # Grab all listing elements
        listings = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] a[href*='maps/place']")

        businesses = []
        seen = set()
        for listing in listings:
            try:
                name = listing.get_attribute("aria-label")
                href = listing.get_attribute("href")
                if name and href and name not in seen:
                    businesses.append((name, href))
                    seen.add(name)
                if len(businesses) >= 50:
                    break
            except:
                continue

        if not businesses:
            return f"No businesses found on Google Maps for {city}."

        print(f"--- Found {len(businesses)} businesses ---")

        # --- Step 3: Click each listing to get website ---
        for i, (name, maps_url) in enumerate(businesses):
            print(f"--- [{i + 1}/{len(businesses)}] {name} ---")
            try:
                driver.get(maps_url)
                time.sleep(2)

                # Look for website button
                website_url = None
                try:
                    website_btn = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-item-id='authority']"))
                    )
                    website_url = website_btn.get_attribute("href")
                except:
                    pass

                if not website_url:
                    print(f"--- No website for {name}, skipping ---")
                    failed.append(f"{name} (no website)")
                    continue

                # --- Step 4: Hunt email on their website ---
                driver.get("about:blank")
                time.sleep(0.5)
                email = hunt_email(driver, website_url)

                if email:
                    save_lead(name, email, city)
                    saved.append(f"{name} → {email}")
                else:
                    failed.append(f"{name} (no email found)")

            except Exception as e:
                failed.append(f"{name} (error: {e})")
                continue

        result = f"✅ Saved {len(saved)} leads for {city}:\n" + "\n".join(saved)
        if failed:
            result += f"\n\n❌ Skipped:\n" + "\n".join(failed)
        return result

    except Exception as e:
        return f"Error finding leads: {e}"

BLOCKED_DOMAINS = [
    "sentry.io", "ingest.sentry.io",
    "cloudflare.com", "amazonaws.com", "jsdelivr.net",
    "googletagmanager.com", "google-analytics.com",
    "hotjar.com", "intercom.io", "hubspot.com",
    "example.com", "test.com",
]

BLOCKED_LOCAL_PARTS = [
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "mailer", "bounce", "notifications", "support",
    "admin", "webmaster", "postmaster", "schema",
]

def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False

    email = email.strip()

    # Must match basic email shape
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', email):
        return False

    local, domain = email.split("@", 1)

    # Domain must not contain version-like segments (e.g. v2.9.0)
    if re.search(r'v\d+\.\d+', domain):
        return False

    # Domain segments must not be pure numbers (e.g. o4504849717526528)
    parts = domain.split(".")
    if any(re.match(r'^\d+$', part) for part in parts):
        return False

    # Block known junk domains
    if any(domain.endswith(bad) for bad in BLOCKED_DOMAINS):
        return False

    # Block junk local parts
    if any(local.lower().startswith(bad) for bad in BLOCKED_LOCAL_PARTS):
        return False

    return True


def clean_leads() -> str:
    if not os.path.exists(CSV_PATH):
        return "❌ leads.csv not found."

    df = pd.read_csv(CSV_PATH)
    required_columns = ["center_name", "email", "city"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    original_count = len(df)

    # Flag and remove invalid emails
    df["_valid"] = df["email"].fillna("").apply(is_valid_email)
    removed = df[~df["_valid"]]
    df = df[df["_valid"]].drop(columns=["_valid"])

    # Deduplicate by email
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["email"], keep="first")
    dupes_removed = before_dedup - len(df)

    # Normalize city casing
    df["city"] = df["city"].fillna("").astype(str).str.strip().str.title()

    df.to_csv(CSV_PATH, index=False)

    removed_names = ", ".join(removed["center_name"].tolist()) if not removed.empty else "none"
    return (
        f"✅ Cleaned leads.csv. "
        f"{original_count} → {len(df)} rows kept. "
        f"Removed {len(removed)} invalid emails ({removed_names}), "
        f"{dupes_removed} duplicates."
    )