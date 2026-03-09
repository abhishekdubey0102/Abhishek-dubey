import asyncio
import random
from playwright.async_api import async_playwright
from logger import logger

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.pages = {}

    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--window-size=390,844',
            ]
        )
        logger.info("Browser started!")

    async def create_profile_pages(self, profile_id, websites):
        # Random mobile user agents
        user_agents = [
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
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

        # Human AI fingerprint
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [
                {name: 'Chrome PDF Plugin'},
                {name: 'Chrome PDF Viewer'},
                {name: 'Native Client'}
            ]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-IN', 'en', 'hi']});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
            window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
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
