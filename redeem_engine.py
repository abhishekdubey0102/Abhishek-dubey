import asyncio
import random
import time
import os
from datetime import datetime
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from logger import logger
from config import WEBSITES, RETRY_ATTEMPTS, MIN_DELAY, MAX_DELAY
from human_ai import HumanAI
from ai_fixer import ai_fixer

os.makedirs("screenshots", exist_ok=True)
os.makedirs("history", exist_ok=True)

HISTORY_FILE = "history/codes.txt"
human = HumanAI()

# ============================================================
# UTILS
# ============================================================
async def smart_delay(min_d=None, max_d=None):
    await asyncio.sleep(random.uniform(min_d or MIN_DELAY, max_d or MAX_DELAY))

def save_code_history(code, site_key, success, reason=""):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            status = "SUCCESS" if success else "FAIL"
            f.write("%s | %s | %s | %s | %s\n" % (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                site_key, code[:8] + "...", status, reason))
    except Exception:
        pass

async def take_screenshot(page, name):
    try:
        path = "screenshots/%s_%s.png" % (name, datetime.now().strftime("%H%M%S"))
        await page.screenshot(path=path)
        logger.info("Screenshot: %s" % path)
        return path
    except Exception:
        return None

# ============================================================
# SMART POPUP HANDLER
# ============================================================
async def smart_close_popups(page):
    selectors = [
        'button:has-text("×")', 'button:has-text("✕")', 'button:has-text("✖")',
        'button:has-text("Close")', '[class*="close"]', '[class*="modal-close"]',
        '[class*="popup-close"]', 'button:has-text("Cancel")',
        '[aria-label="close"]', '[aria-label="Close"]',
        '.van-icon-cross', '[class*="icon-close"]',
        '.van-overlay', '[class*="overlay"]',
    ]
    closed = 0
    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            for el in elements:
                try:
                    if await el.is_visible():
                        await el.click()
                        await asyncio.sleep(0.15)
                        closed += 1
                except Exception:
                    continue
        except Exception:
            continue
    return closed

# ============================================================
# SMART ELEMENT FINDER
# ============================================================
async def smart_find(page, selectors, timeout=5):
    for selector in selectors:
        try:
            el = await page.wait_for_selector(selector, timeout=timeout * 1000)
            if el and await el.is_visible():
                return el
        except Exception:
            continue
    return None

# ============================================================
# SLIDER CAPTCHA SOLVER
# ============================================================
async def solve_slider_captcha(page):
    try:
        slider = await smart_find(page, [
            '.slider', '.slide-btn', '[class*="slider"]',
            '[class*="slide-btn"]', '.nc_iconfont',
            '[class*="drag"]', '.verify-drag-block',
        ], timeout=3)
        if not slider:
            return True

        logger.info("Captcha detected - AI solving...")
        box = await slider.bounding_box()
        if not box:
            return False

        start_x = box['x'] + box['width'] / 2
        start_y = box['y'] + box['height'] / 2

        track = await smart_find(page, [
            '.slide-track', '[class*="track"]', '.nc-lang-cnt',
        ], timeout=2)
        end_x = start_x + 300
        if track:
            tb = await track.bounding_box()
            if tb:
                end_x = tb['x'] + tb['width'] - 5

        # Bezier curve slide - human like
        await page.mouse.move(start_x, start_y)
        await asyncio.sleep(random.uniform(0.2, 0.4))
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.1))

        steps = 30
        for i in range(steps):
            t = (i + 1) / steps
            ease = t * t * (3 - 2 * t)
            x = start_x + (end_x - start_x) * ease
            y = start_y + random.uniform(-1.5, 1.5)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.008, 0.025))

        await asyncio.sleep(random.uniform(0.1, 0.2))
        await page.mouse.up()
        await asyncio.sleep(1.5)
        logger.info("Captcha solved!")
        return True
    except Exception as e:
        logger.error("Captcha error: %s" % str(e))
        return False

# ============================================================
# LOGIN CHECK
# ============================================================
async def is_logged_in(page, site_url=None):
    try:
        url = page.url.lower()
        if "login" in url or "signin" in url:
            return False
        login_form = await smart_find(page, [
            'input[type="tel"]', 'input[placeholder*="phone"]',
        ], timeout=2)
        if login_form:
            return False
        return True
    except Exception:
        return False

# ============================================================
# AUTO LOGIN - WITH AI FIX
# ============================================================
async def auto_login(page, account, site_key):
    try:
        site = WEBSITES[site_key]
        base_url = site['url'].replace('/#/', '')
        logger.info("Auto login: %s" % site_key)

        await page.goto(base_url + '/#/login', timeout=15000)
        await human.simulate_page_visit(page)
        await smart_close_popups(page)

        phone_input = await smart_find(page, [
            'input[type="tel"]', 'input[type="text"][placeholder*="phone"]',
            'input[placeholder*="Phone"]', 'input[placeholder*="number"]',
            'input[placeholder*="mobile"]', 'input[placeholder*="Mobile"]',
        ], timeout=10)

        if not phone_input:
            logger.error("Phone input not found: %s" % site_key)
            return False

        phone = account['phone'].replace('+91', '').replace('+', '')
        await human.natural_type(phone_input, phone)
        await human.think_delay()

        pass_input = await smart_find(page, ['input[type="password"]'], timeout=5)
        if pass_input:
            await human.natural_type(pass_input, account['password'])
            await human.think_delay()

        await solve_slider_captcha(page)

        # Remember password checkbox ON karo
        remember_selectors = [
            'input[type="checkbox"]',
            '[class*="remember"]',
            'label:has-text("Remember")',
            'label:has-text("remember")',
            '.remember-password',
            '[class*="remember-password"]',
        ]
        for sel in remember_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    visible = await el.is_visible()
                    if visible:
                        # Check if already checked
                        checked = await el.is_checked() if sel.startswith('input') else False
                        if not checked:
                            await el.click()
                            await asyncio.sleep(0.2)
                            logger.info("Remember password ON!")
                        break
            except Exception:
                continue

        # Browser mein bhi credentials save karo (JavaScript)
        try:
            await page.evaluate("""() => {
                if (window.localStorage) {
                    localStorage.setItem('rememberLogin', 'true');
                }
            }""")
        except Exception:
            pass

        login_btn = await smart_find(page, [
            'button:has-text("Log in")', 'button:has-text("Login")',
            'button:has-text("Sign in")', 'button[type="submit"]',
            '.login-btn', '[class*="login-btn"]',
        ], timeout=5)

        if login_btn:
            await human.natural_click(page, login_btn)
            await smart_delay(2, 3)

        if await is_logged_in(page):
            logger.info("Login OK: %s" % site_key)
            return True

        await solve_slider_captcha(page)
        await asyncio.sleep(1)
        if await is_logged_in(page):
            logger.info("Login OK (retry): %s" % site_key)
            return True

        logger.error("Login failed: %s" % site_key)
        return False

    except Exception as e:
        logger.error("Login error %s: %s" % (site_key, str(e)))
        # AI Auto Fix
        fixed = await ai_fixer.analyze_and_fix(page, str(e), site_key, account)
        if fixed:
            return await auto_login(page, account, site_key)
        return False

# ============================================================
# ULTRA FAST SMART REDEEM - WITH AI AUTO FIX
# ============================================================
async def redeem_code(page, account, site_key, code):
    site = WEBSITES[site_key]
    base_url = site['url'].replace('/#/', '')

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            logger.info("Redeem | %s | %s... | Try: %d" % (site_key, code[:8], attempt))

            # Account page
            await page.goto(base_url + '/#/mine', timeout=15000)
            await smart_delay(0.4, 0.7)
            await smart_close_popups(page)

            # Login check
            if not await is_logged_in(page):
                logger.warning("Session expired - re-login...")
                if not await auto_login(page, account, site_key):
                    save_code_history(code, site_key, False, "Login failed")
                    continue
                await page.goto(base_url + '/#/mine', timeout=15000)
                await smart_delay(0.4, 0.6)
                await smart_close_popups(page)

            # Gift button
            gift_btn = await smart_find(page, [
                'text=Gifts', 'text=Gift', '[class*="gift"]',
                'a[href*="gift"]', '.gift-item',
            ], timeout=5)

            if gift_btn:
                await human.natural_click(page, gift_btn)
                await smart_delay(0.3, 0.5)
            else:
                await page.goto(base_url + '/#/gift', timeout=15000)
                await smart_delay(0.3, 0.5)

            await smart_close_popups(page)

            # Code input
            code_input = await smart_find(page, [
                'input[placeholder*="gift"]', 'input[placeholder*="Gift"]',
                'input[placeholder*="code"]', 'input[placeholder*="Code"]',
                'input[placeholder*="enter"]', 'input[placeholder*="Enter"]',
                'input[type="text"]', '.gift-input input',
            ], timeout=5)

            if not code_input:
                logger.warning("Code input not found (attempt %d)" % attempt)
                await take_screenshot(page, "no_input_%s" % site_key)

                # AI Auto Fix
                fixed = await ai_fixer.analyze_and_fix(
                    page, "element not found", site_key, account)
                if fixed and attempt < RETRY_ATTEMPTS:
                    await smart_delay(0.5, 1)
                    continue
                save_code_history(code, site_key, False, "Input not found")
                return False

            # ULTRA FAST paste via JavaScript
            await page.evaluate("""
                (el, val) => {
                    el.focus();
                    el.value = val;
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));
                }
            """, code_input, code)
            await smart_delay(0.1, 0.2)

            # Receive button
            receive_btn = await smart_find(page, [
                'button:has-text("Receive")', 'button:has-text("Redeem")',
                'button:has-text("Submit")', 'button:has-text("Confirm")',
                'button:has-text("Claim")', '[class*="receive"]',
                '[class*="redeem"]', '[class*="submit"]',
            ], timeout=5)

            if receive_btn:
                await human.natural_click(page, receive_btn)
                await smart_delay(0.5, 0.9)

            # OK/Confirm button
            confirm_btn = await smart_find(page, [
                'button:has-text("OK")', 'button:has-text("Confirm")',
                'button:has-text("Yes")', '[class*="confirm"]',
            ], timeout=3)
            if confirm_btn:
                await human.natural_click(page, confirm_btn)
                await smart_delay(0.2, 0.4)

            # Result check
            page_text = (await page.content()).lower()
            success_words = ["success", "congratulation", "received",
                           "redeemed", "claimed", "reward", "bonus"]
            fail_words = ["invalid", "expired", "already used",
                         "not exist", "incorrect", "wrong"]

            if any(w in page_text for w in success_words):
                logger.info("SUCCESS! %s | %s..." % (site_key, code[:8]))
                await take_screenshot(page, "success_%s" % site_key)
                save_code_history(code, site_key, True)
                return True
            elif any(w in page_text for w in fail_words):
                logger.warning("Invalid/Expired: %s" % site_key)
                save_code_history(code, site_key, False, "Invalid/Expired")
                return False
            else:
                logger.info("Submitted: %s" % site_key)
                await take_screenshot(page, "submitted_%s" % site_key)
                save_code_history(code, site_key, True, "Assumed success")
                return True

        except Exception as e:
            logger.error("Redeem error (attempt %d) %s: %s" % (attempt, site_key, str(e)))
            await take_screenshot(page, "error_%s" % site_key)

            # AI AUTO FIX!
            fixed = await ai_fixer.analyze_and_fix(page, str(e), site_key, account)
            if fixed and attempt < RETRY_ATTEMPTS:
                logger.info("AI fixed! Retrying...")
                await smart_delay(0.5, 1)
                continue

    save_code_history(code, site_key, False, "All attempts failed")
    return False
