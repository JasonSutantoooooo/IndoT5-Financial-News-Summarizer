from playwright.sync_api import sync_playwright
import time

APPS = [
    "https://indot5-financial-news-summarizer.streamlit.app/",
]

def keepalive():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in APPS:
            print(f"Visiting {url}...")
            page.goto(url, timeout=60000)
            time.sleep(10)
            # Klik tombol wake-up jika app sedang tidur
            try:
                btn = page.get_by_text("Yes, get this app back up!")
                if btn.is_visible():
                    btn.click()
                    print(f"WAKE: {url}")
                else:
                    print(f"OK: {url}")
            except:
                print(f"OK: {url}")
        browser.close()

keepalive()