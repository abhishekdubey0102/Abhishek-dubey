import asyncio
import re
import random
import logging
from telethon import TelegramClient, events
from playwright.async_api import async_playwright
from config import *

# ===== LOGGER =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# ===== GLOBALS =====
browser = None
pages = {}
used_codes = set()

# ===== DETECT SITE =====
def detect_site(text):
    text_lower = text.lower()
    for site_key, keywords in SITE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return site_key
    return None

# ===== DETECT CODES =====
def detect_codes(text):
    return re.findall(r'[A-Fa-f0-9]{32}', text)

# ===== HUMAN DELAY =====
async def delay(a=0.3, b=0.8):
    await asyncio.sleep(random.uniform(a, b))

# ===== CLOSE POPUPS =====
async def close_popups(page):
    selectors = [
        'button:has-text("×")', 'button:has-text("X")',
        'button:has-text("Close")', 'button:has-text("OK")',
        '.van-popup__close', '[class*="close"]',
        '.van-overlay',
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.click()
                await delay(0.3, 0.5)
        except:
            pass

# ===== IS LOGGED IN =====
async def is_logged_in(page):
    try:
        indicators = ['text=Withdraw', 'text=Deposit', 'text=Recharge',
                      '[class*="balance"]', '[class*="wallet"]']
        for sel in indicators:
            try:
                if await page.locator(sel).first.is_visible(timeout=2000):
                    return True
            except:
                pass
        return False
    except:
        return False

# ===== LOGIN =====
async def login(page, site_key):
    try:
        log.info("Login shuru: %s" % site_key)
        url = WEBSITES[site_key]
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await delay(2, 3)
        await close_popups(page)
        await delay(1, 2)

        if await is_logged_in(page):
            log.info("Already logged in: %s" % site_key)
            return True

        # Login button click
        for btn in ['text=Login', 'text=LOGIN', 'button:has-text("Login")', '[class*="login"]']:
            try:
                el = page.locator(btn).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await delay(1, 2)
                    break
            except:
                pass

        await close_popups(page)

        # Phone
        phone_filled = False
        for sel in ['input[type="tel"]', 'input[placeholder*="phone"]',
                    'input[placeholder*="Phone"]', 'input[placeholder*="mobile"]',
                    'input[name="phone"]', 'input[type="number"]']:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    await el.click()
                    await el.fill("")
                    await page.keyboard.type(PHONE, delay=80)
                    phone_filled = True
                    log.info("Phone daala: %s" % site_key)
                    break
            except:
                pass

        if not phone_filled:
            log.error("Phone input nahi mila: %s" % site_key)
            return False

        await delay(0.5, 1)

        # Password
        pass_filled = False
        for sel in ['input[type="password"]', 'input[placeholder*="assword"]',
                    'input[placeholder*="Pass"]']:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    await el.click()
                    await el.fill("")
                    await page.keyboard.type(PASSWORD, delay=80)
                    pass_filled = True
                    log.info("Password daala: %s" % site_key)
                    break
            except:
                pass

        if not pass_filled:
            log.error("Password input nahi mila: %s" % site_key)
            return False

        await delay(0.5, 1)

        # Submit
        for sel in ['button[type="submit"]', 'button:has-text("Login")',
                    'button:has-text("LOGIN")', 'button:has-text("Sign in")']:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    break
            except:
                pass

        await delay(3, 5)
        await close_popups(page)
        await delay(2, 3)

        if await is_logged_in(page):
            log.info("Login SUCCESS: %s" % site_key)
            return True
        else:
            log.warning("Login ho sakta hai, check karo: %s" % site_key)
            return True  # Continue anyway

    except Exception as e:
        log.error("Login error %s: %s" % (site_key, str(e)))
        return False

# ===== REDEEM =====
async def redeem(page, site_key, code):
    try:
        base = WEBSITES[site_key].rstrip('/#/')

        # Gift page try karo
        for gift_url in [base + '/#/gift', base + '/#/welfare/gift',
                         base + '/#/activity/gift']:
            try:
                await page.goto(gift_url, wait_until='domcontentloaded', timeout=15000)
                await delay(2, 3)
                await close_popups(page)

                # Input dhundo
                inp = page.locator('input').first
                if await inp.is_visible(timeout=3000):
                    await inp.click()
                    await inp.fill("")
                    await page.keyboard.type(code, delay=50)
                    log.info("Code daala: %s on %s" % (code[:8], site_key))

                    # Submit
                    for sel in ['button:has-text("Redeem")', 'button:has-text("Submit")',
                                'button:has-text("Confirm")', 'button:has-text("Exchange")',
                                'button[type="submit"]']:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=2000):
                                await btn.click()
                                break
                        except:
                            pass

                    await delay(2, 3)
                    await close_popups(page)
                    log.info("Redeem done: %s - %s" % (site_key, code[:8]))
                    return True
            except:
                pass

        log.error("Gift page nahi mila: %s" % site_key)
        return False

    except Exception as e:
        log.error("Redeem error %s: %s" % (site_key, str(e)))
        return False

# ===== PROCESS CODE =====
async def process(code, site_key):
    if code in used_codes:
        log.info("Already used: %s" % code[:8])
        return
    used_codes.add(code)

    log.info("=" * 50)
    log.info("CODE AAYA! Site: %s | Code: %s" % (site_key, code[:8]))
    log.info("=" * 50)

    page = pages.get(site_key)
    if not page:
        log.error("Page nahi mila: %s" % site_key)
        return

    if not await is_logged_in(page):
        await login(page, site_key)

    await redeem(page, site_key, code)

# ===== MAIN =====
async def main():
    global browser, pages

    log.info("=" * 50)
    log.info("AUTO REDEEM BOT STARTING...")
    log.info("=" * 50)

    # Browser start
    log.info("Browser shuru ho raha hai...")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )

        # Pages banao
        for site_key in WEBSITES.keys():
            context = await browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                is_mobile=True,
                has_touch=True,
            )
            page = await context.new_page()
            pages[site_key] = page
            log.info("Page ready: %s" % site_key)

        # Login all sites
        for site_key in WEBSITES.keys():
            await login(pages[site_key], site_key)
            await asyncio.sleep(1)

        log.info("Sab ready! Telegram monitor shuru...")

        # Telegram client
        client = TelegramClient('bot_session', 
                                int(TELEGRAM_API_ID), 
                                TELEGRAM_API_HASH)
        await client.start(phone=TELEGRAM_PHONE)
        log.info("Telegram connected!")

        @client.on(events.NewMessage())
        async def handler(event):
            try:
                text = event.message.message or ""
                if not text:
                    return

                # Sender name
                sender_name = ""
                try:
                    sender = await event.get_sender()
                    sender_name = getattr(sender, 'title', '') or \
                                  getattr(sender, 'first_name', '') or ""
                except:
                    pass

                combined = (text + " " + sender_name).lower()

                # Site detect
                site_key = detect_site(combined)
                if not site_key:
                    return

                # Codes detect
                codes = detect_codes(text)
                if not codes:
                    return

                log.info("Message aaya! Site: %s | Codes: %d" % (site_key, len(codes)))

                for code in codes:
                    asyncio.create_task(process(code, site_key))

            except Exception as e:
                log.error("Handler error: %s" % str(e))

        log.info("Bot chal raha hai! Groups monitor ho rahe hain...")
        await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
