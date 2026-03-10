import asyncio
import random
import subprocess
from playwright.async_api import async_playwright
from logger import logger

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.pages = {}

    async def init(self):
        try:
            logger.info("Installing Chromium...")
            subprocess.run(
                ["python", "-m", "playwright", "install", "chromium"],
                capture_output=True, timeout=120
            )
            logger.info("Chromium installed!")
        except Exception as e:
            logger.warning("Install warning: %s" % str(e))

        self.playwright = await async_playwright().start()

        for executable in [
            None,
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/google-chrome',
        ]:
            try:
                opts = {
                    'headless': True,
                    'args': [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-blink-features=AutomationControlled',
                        '--window-size=390,844',
                    ]
                }
                if executable:
                    opts['executable_path'] = executable

                self.browser = await self.playwright.chromium.launch(**opts)
                logger.info("Browser started!")
                return
            except Exception as e:
                logger.warning("Browser option failed: %s" % str(e))
                continue

        raise Exception("Browser start nahi hua!")

    async def create_profile_pages(self, profile_id, websites):
        user_agents = [
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
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
