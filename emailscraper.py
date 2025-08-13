import asyncio
from playwright.async_api import async_playwright
import csv
import os
import random
import re

async def main():
    letter = input("Enter letter (e.g., a, b, c): ").strip().lower()
    filename = f"{letter}names.txt"

    if not os.path.isfile(filename):
        print(f"❌ File '{filename}' not found.")
        return

    with open(filename, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()]

    output_file = f"emails_{letter}.csv"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/118.0.0.0 Safari/537.36"),
            viewport={"width": 1366, "height": 768}
        )
        page = await context.new_page()

        for username in usernames:
            url = f"https://www.artstation.com/{username}/profile"
            print(f"🔍 Visiting {url} ...")

            email = None
            followers_count = None

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"⚠ {username} → Page load timeout: {e}")
                continue

            await page.wait_for_timeout(random.randint(2000, 4000))  # human-ish pause
            try:
                # Ensure lazy content is rendered
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1200)

                # ---------- FOLLOWERS (robust) ----------
                try:
                    followers_link = page.locator("a[href$='/followers'], a:has-text('Followers')").first
                    if await followers_link.count() > 0:
                        li = followers_link.locator("xpath=ancestor::li[1]")
                        if await li.count() > 0:
                            li_text = (await li.inner_text()).strip()
                            m = re.search(r'(\d[\d,]*)', li_text)
                            if m:
                                followers_count = int(m.group(1).replace(",", ""))
                        # Fallback: previousSibling text node
                        if followers_count is None:
                            prev_text = await followers_link.evaluate(
                                "(el) => (el.previousSibling && el.previousSibling.textContent || '').trim()"
                            )
                            if prev_text:
                                m2 = re.search(r'(\d[\d,]*)', prev_text)
                                if m2:
                                    followers_count = int(m2.group(1).replace(",", ""))
                except:
                    followers_count = None

                # ---------- EMAIL (Contact section only) ----------
                try:
                    # Find the Contact section container
                    contact_h3 = page.locator("h3:has-text('Contact')").first
                    contact = None
                    if await contact_h3.count() > 0:
                        # Contact section wrapper (ancestor with contact-section class if present)
                        contact = contact_h3.locator("xpath=ancestor::div[contains(@class,'contact-section')][1]")
                        if await contact.count() == 0:
                            # Fallback: nearest resume-section
                            contact = contact_h3.locator("xpath=ancestor::div[contains(@class,'resume-section')][1]")

                    # If we have the contact section, restrict all selectors to it
                    section = contact if contact and await contact.count() > 0 else page

                    # Prefer the "Reveal email" flow inside Contact
                    reveal_btn = section.locator("div.email-wrapper button:has-text('Reveal email')").first
                    if await reveal_btn.count() > 0 and await reveal_btn.is_enabled():
                        await reveal_btn.click()

                        # Wait up to 12s for either unmasked span or a mailto within Contact
                        email = None
                        span = section.locator("div.email-wrapper span").first
                        for _ in range(12):  # 12 x 1s = 12s
                            # Case A: a mailto link appears
                            mailto = section.locator("div.email-wrapper a[href^='mailto:']").first
                            if await mailto.count() > 0:
                                href = await mailto.get_attribute("href")
                                if href:
                                    email = href.replace("mailto:", "").strip()
                                    break
                            # Case B: the span text is revealed (no asterisks)
                            if await span.count() > 0:
                                txt = (await span.text_content() or "").strip()
                                if txt and "@" in txt and "*" not in txt:
                                    email = txt
                                    break
                            await page.wait_for_timeout(1000)

                    # If no button, look for direct mailto **inside Contact**
                    if not email:
                        mailto = section.locator("a[href^='mailto:']").first
                        if await mailto.count() > 0:
                            href = await mailto.get_attribute("href")
                            if href:
                                email = href.replace("mailto:", "").strip()

                except:
                    email = None

            except Exception as e:
                print(f"⚠ {username} → Error scraping data: {e}")

            # Always log
            print(f"📄 {username} → Email: {email if email else 'None'}, "
                  f"Followers: {followers_count if followers_count is not None else 'None'}")

            # Save if email exists and followers < 1000 OR followers is None (your request)
            if email and (followers_count is None or followers_count < 1000):
                file_exists = os.path.isfile(output_file)
                with open(output_file, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Username", "Email", "Followers"])
                    writer.writerow([username, email, followers_count if followers_count is not None else "None"])
                print(f"💾 Saved: {username} → {email} "
                      f"({followers_count if followers_count is not None else 'None'} followers)")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
