import asyncio
from playwright.async_api import async_playwright
import re
import os

async def scrape_usernames(letter):
    url = f"https://www.artstation.com/search/artists?sort_by=followers&query={letter}"
    output_file = f"{letter}names.txt"
    usernames = set()

    # Load already existing usernames from file
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            usernames = set(line.strip() for line in f if line.strip())

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            java_script_enabled=True
        )
        page = await context.new_page()

        await page.goto(url, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector("a.text-white[href*='artstation.com/']", timeout=15000)
        except:
            print(f"❌ No usernames found for '{letter}' after waiting.")
            await browser.close()
            return

        prev_height = 0
        stuck_count = 0

        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

            links = await page.locator("a.text-white").element_handles()
            new_found = False

            for link in links:
                href = await link.get_attribute("href")
                if href and href.startswith("https://www.artstation.com/"):
                    username = href.split("/")[-1]
                    if re.match(r"^[a-zA-Z0-9_]+$", username) and username not in usernames:
                        usernames.add(username)
                        new_found = True

            # Save immediately if we found something new
            if new_found:
                with open(output_file, "w", encoding="utf-8") as f:
                    for name in sorted(usernames):
                        f.write(name + "\n")

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                stuck_count += 1
            else:
                stuck_count = 0
            prev_height = new_height

            if stuck_count >= 3:
                break

        await browser.close()

    print(f"✅ Total usernames in {output_file}: {len(usernames)}")


if __name__ == "__main__":
    letter = input("Enter search letter: ").strip().lower()
    asyncio.run(scrape_usernames(letter))
