import asyncio
import random
import re
from logger import logger

# ============================================================
# HUMAN DELAY
# ============================================================
async def human_delay(min_s=0.3, max_s=0.8):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def human_type(page, selector, text):
    await page.click(selector)
    await human_delay(0.2, 0.4)
    await page.fill(selector, "")
    await human_delay(0.1, 0.2)
    for char in text:
        await page.type(selector, char)
        await asyncio.sleep(random.uniform(0.05, 0.15))

# ============================================================
# CLOSE POPUPS
# ============================================================
async def close_popups(page):
    popup_selectors = [
        'button:has-text("Close")',
        'button:has-text("close")',
        'button:has-text("X")',
        'button:has-text("×")',
        '.close-btn',
        '.popup-close',
        '.modal-close',
        '[class*="close"]',
        '.van-popup__close',
        '.van-overlay',
        'button:has-text("OK")',
        'button:has-text("确定")',
        'button:has-text("Cancel")',
    ]
    for sel in popup_selectors:
        try:
            el = page.locator(sel).first
            if await el.is_visible():
                await el.click()
                await human_delay(0.3, 0.5)
        except:
            pass

# ============================================================
# IS LOGGED IN
# ============================================================
async def is_logged_in(page, site_key):
    try:
        logged_in_indicators = [
            '[class*="mine"]',
            '[class*="user"]',
            '[class*="balance"]',
            '[class*="wallet"]',
            'text=Withdraw',
            'text=Deposit',
            'text=Recharge',
        ]
        for indicator in logged_in_indicators:
            try:
                el = page.locator(indicator).first
                if await el.is_visible(timeout=2000):
                    return True
            except:
                pass

        login_indicators = [
            'text=Login',
            'text=Sign in',
            'input[type="tel"]',
            'input[placeholder*="phone"]',
            'input[placeholder*="Phone"]',
            'input[placeholder*="mobile"]',
        ]
        for indicator in login_indicators:
            try:
                el = page.locator(indicator).first
                if await el.is_visible(timeout=2000):
                    return False
            except:
                pass

        return False
    except:
        return False

# ============================================================
# AUTO LOGIN
# ============================================================
async def auto_login(page, site_key, phone, password):
    try:
        from config import WEBSITES
        url = WEBSITES[site_key]['url']

        logger.info("Auto login: %s" % site_key)

        # Page load
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await human_delay(2, 3)
        await close_popups(page)
        await human_delay(1, 2)

        # Already logged in check
        if await is_logged_in(page, site_key):
            logger.info("Already logged in: %s" % site_key)
            return True

        # Login button dhundo
        login_btns = [
            'text=Login',
            'text=Log in',
            'text=Sign in',
            'text=LOGIN',
            '[class*="login-btn"]',
            '[class*="loginBtn"]',
            'button:has-text("Login")',
        ]
        for btn in login_btns:
            try:
                el = page.locator(btn).first
                if await el.is_visible(timeout=3000):
                    await el.click()
                    await human_delay(1, 2)
                    break
            except:
                pass

        await close_popups(page)
        await human_delay(1, 2)

        # Phone input dhundo
        phone_selectors = [
            'input[type="tel"]',
            'input[placeholder*="phone"]',
            'input[placeholder*="Phone"]',
            'input[placeholder*="mobile"]',
            'input[placeholder*="Mobile"]',
            'input[placeholder*="number"]',
            'input[placeholder*="Number"]',
            'input[name="phone"]',
            'input[name="mobile"]',
            'input[type="number"]',
            'input[type="text"]',
        ]

        phone_filled = False
        for sel in phone_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    await human_type(page, sel, phone)
                    phone_filled = True
                    logger.info("Phone filled: %s" % site_key)
                    break
            except:
                pass

        if not phone_filled:
            logger.error("Phone input not found: %s" % site_key)
            return False

        await human_delay(0.5, 1)

        # Password input dhundo
        pass_selectors = [
            'input[type="password"]',
            'input[placeholder*="password"]',
            'input[placeholder*="Password"]',
            'input[placeholder*="pass"]',
            'input[name="password"]',
        ]

        pass_filled = False
        for sel in pass_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    await human_type(page, sel, password)
                    pass_filled = True
                    logger.info("Password filled: %s" % site_key)
                    break
            except:
                pass

        if not pass_filled:
            logger.error("Password input not found: %s" % site_key)
            return False

        await human_delay(0.5, 1)

        # Remember me checkbox
        remember_sels = [
            'input[type="checkbox"]',
            '[class*="remember"]',
            '[class*="Remember"]',
        ]
        for sel in remember_sels:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    checked = await el.is_checked()
                    if not checked:
                        await el.click()
            except:
                pass

        await human_delay(0.5, 1)

        # Submit button
        submit_sels = [
            'button[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            'button:has-text("LOGIN")',
            'button:has-text("Submit")',
            '[class*="login-btn"]',
            '[class*="submit"]',
        ]

        submitted = False
        for sel in submit_sels:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    submitted = True
                    logger.info("Login submitted: %s" % site_key)
                    break
            except:
                pass

        if not submitted:
            await page.keyboard.press('Enter')

        await human_delay(3, 5)
        await close_popups(page)
        await human_delay(2, 3)

        # Slider captcha handle
        await handle_slider(page)
        await human_delay(2, 3)

        if await is_logged_in(page, site_key):
            logger.info("Login SUCCESS: %s" % site_key)
            return True
        else:
            logger.error("Login failed: %s" % site_key)
            return False

    except Exception as e:
        logger.error("Login error %s: %s" % (site_key, str(e)))
        return False

# ============================================================
# SLIDER CAPTCHA
# ============================================================
async def handle_slider(page):
    try:
        slider_sels = [
            '[class*="slider"]',
            '[class*="drag"]',
            '[class*="swipe"]',
            '.nc_iconfont',
            '#nc_1_n1z',
        ]
        for sel in slider_sels:
            try:
                slider = page.locator(sel).first
                if await slider.is_visible(timeout=2000):
                    box = await slider.bounding_box()
                    if box:
                        start_x = box['x'] + box['width'] / 2
                        start_y = box['y'] + box['height'] / 2
                        await page.mouse.move(start_x, start_y)
                        await page.mouse.down()
                        await human_delay(0.3, 0.5)
                        for i in range(20):
                            await page.mouse.move(
                                start_x + (i * 15),
                                start_y + random.uniform(-2, 2)
                            )
                            await asyncio.sleep(0.05)
                        await page.mouse.up()
                        await human_delay(1, 2)
                        logger.info("Slider handled!")
                        return True
            except:
                pass
    except:
        pass
    return False

# ============================================================
# REDEEM CODE
# ============================================================
async def redeem_code(page, site_key, code, phone, password):
    try:
        from config import WEBSITES

        # Login check
        if not await is_logged_in(page, site_key):
            success = await auto_login(page, site_key, phone, password)
            if not success:
                return False

        base_url = WEBSITES[site_key]['url'].rstrip('/#/')

        # Gift page pe jao
        gift_urls = [
            base_url + '/#/gift',
            base_url + '/#/activity/gift',
            base_url + '/#/welfare/gift',
            base_url + '/#/bonus',
        ]

        gift_found = False
        for gift_url in gift_urls:
            try:
                await page.goto(gift_url, wait_until='domcontentloaded', timeout=15000)
                await human_delay(2, 3)
                await close_popups(page)

                # Gift input check
                gift_input = page.locator('input').first
                if await gift_input.is_visible(timeout=3000):
                    gift_found = True
                    break
            except:
                pass

        if not gift_found:
            # Navigation se gift dhundo
            gift_nav_sels = [
                'text=Gift',
                'text=gift',
                'text=Redeem',
                'text=Bonus',
                '[class*="gift"]',
                '[href*="gift"]',
            ]
            for sel in gift_nav_sels:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        await human_delay(2, 3)
                        gift_found = True
                        break
                except:
                    pass

        await close_popups(page)
        await human_delay(1, 2)

        # Code input dhundo
        code_selectors = [
            'input[placeholder*="gift"]',
            'input[placeholder*="Gift"]',
            'input[placeholder*="code"]',
            'input[placeholder*="Code"]',
            'input[placeholder*="redeem"]',
            'input[type="text"]',
            'input',
        ]

        code_filled = False
        for sel in code_selectors:
            try:
                inputs = page.locator(sel)
                count = await inputs.count()
                for i in range(count):
                    el = inputs.nth(i)
                    if await el.is_visible(timeout=1000):
                        await el.click()
                        await human_delay(0.2, 0.4)
                        await el.fill("")
                        await page.keyboard.type(code, delay=50)
                        code_filled = True
                        logger.info("Code filled: %s - %s" % (site_key, code[:8]))
                        break
                if code_filled:
                    break
            except:
                pass

        if not code_filled:
            logger.error("Code input not found: %s" % site_key)
            return False

        await human_delay(0.5, 1)

        # Submit
        submit_sels = [
            'button:has-text("Redeem")',
            'button:has-text("Submit")',
            'button:has-text("Confirm")',
            'button:has-text("Exchange")',
            'button:has-text("Claim")',
            'button[type="submit"]',
            'button',
        ]

        for sel in submit_sels:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    logger.info("Redeem submitted: %s" % site_key)
                    break
            except:
                pass

        await human_delay(2, 3)
        await close_popups(page)

        # Result check
        success_texts = ['success', 'Success', 'congratul', 'reward', 'Reward', 'claimed', 'received']
        fail_texts = ['invalid', 'Invalid', 'expired', 'Expired', 'used', 'Used', 'wrong', 'Wrong']

        content = await page.content()
        content_lower = content.lower()

        for text in success_texts:
            if text.lower() in content_lower:
                logger.info("REDEEM SUCCESS: %s - %s" % (site_key, code[:8]))
                return True

        for text in fail_texts:
            if text.lower() in content_lower:
                logger.warning("Redeem failed (invalid/used): %s - %s" % (site_key, code[:8]))
                return False

        logger.info("Redeem done (unknown result): %s" % site_key)
        return True

    except Exception as e:
        logger.error("Redeem error %s: %s" % (site_key, str(e)))
        return False
