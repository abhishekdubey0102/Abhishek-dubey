import asyncio
import random
import subprocess
import os
from playwright.async_api import async_playwright
from logger import logger

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.pages = {}

    async def init(self):
        # Install playwright chromium
        try:
            logger.info("Installing Chromium...")
            result = subprocess.run(
                ["python", "-m", "playwright", "install", "chromium"],
                capture_output=True, timeout=120, text=True
            )
            logger.info("Playwright install done!")
        except Exception as e:
            logger.warning("Install warning: %s" % str(e))

        self.playwright = await async_playwright().start()

        common_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--single-process',
            '--no-zygote',
            '--disable-blink-features=AutomationControlled',
        ]

        # Try playwright chromium first (with install-deps)
        try:
            subprocess.run(
                ["python", "-m", "playwright", "install-deps", "chromium"],
                capture_output=True, timeout=120
            )
        except:
            pass

        # Find chromium executable
        chromium_paths = [
            None,  # playwright default
            '/nix/var/nix/profiles/default/bin/chromium',
            '/run/current-system/sw/bin/chromium',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        ]

        # Also check nix store
        try:
            result = subprocess.run(['which', 'chromium'], capture_output=True, text=True)
            if result.stdout.strip():
                chromium_paths.insert(1, result.stdout.strip())
        except:
            pass

        for executable in chromium_paths:
            try:
                opts = {'headless': True, 'args': common_args}
                if executable:
                    if not os.path.exists(executable):
                        continue
                    opts['executable_path'] = executable

                self.browser = await self.playwright.chromium.launch(**opts)
                logger.info("Browser started! Path: %s" % (executable or 'playwright default'))
                return
            except Exception as e:
                logger.warning("Browser option failed: %s" % str(e)[:100])
                continue

        raise Exception("Browser start nahi hua!")

    async def create_profile_pages(self, profile_id, websites):
        user_agents = [
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        ]

        context = await self.browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent=random.choice(user_agents),
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            device_scale_factor=2.0,
            is_mobile=True,
            has_touch=True,
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-IN', 'en', 'hi']});
            window.chrome = {runtime: {}};
        """)

        self.pages[profile_id] = {}
        for site_key in websites.keys():
            page = await context.new_page()
            self.pages[profile_id][site_key] = page
            logger.info("Page ready: %s - %s" % (profile_id, site_key))

        return self.pages[profile_id]

    def get_page(self, profile_id, site_key):
        return self.pages.get(profile_id, {}).get(site_key)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

browser_manager = BrowserManager()
