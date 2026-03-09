import asyncio
import random
import math
from logger import logger

class HumanAI:
    """
    AI-powered human behavior simulator
    Website ko lagega real human hai!
    """

    # ---- Random Delays ----
    @staticmethod
    async def think_delay():
        """Human sochta hai - random pause"""
        await asyncio.sleep(random.uniform(0.3, 1.2))

    @staticmethod
    async def read_delay():
        """Human page read karta hai"""
        await asyncio.sleep(random.uniform(0.5, 1.5))

    @staticmethod
    async def type_delay():
        """Typing ke beech pause"""
        await asyncio.sleep(random.uniform(0.03, 0.15))

    @staticmethod
    async def click_delay():
        """Click karne se pehle pause"""
        await asyncio.sleep(random.uniform(0.1, 0.4))

    # ---- Natural Mouse Movement ----
    @staticmethod
    async def natural_mouse_move(page, target_x, target_y):
        """Bezier curve se natural mouse movement"""
        try:
            # Current position
            curr_x = random.randint(100, 300)
            curr_y = random.randint(100, 300)

            # Control points for bezier curve
            cp1_x = curr_x + random.randint(-50, 50)
            cp1_y = curr_y + random.randint(-50, 50)
            cp2_x = target_x + random.randint(-30, 30)
            cp2_y = target_y + random.randint(-30, 30)

            steps = random.randint(15, 25)
            for i in range(steps + 1):
                t = i / steps
                # Cubic bezier formula
                x = (1-t)**3 * curr_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * target_x
                y = (1-t)**3 * curr_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * target_y

                # Slight random jitter
                x += random.uniform(-1, 1)
                y += random.uniform(-1, 1)

                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.01, 0.03))

        except Exception:
            pass

    # ---- Natural Click ----
    @staticmethod
    async def natural_click(page, element):
        """Human jesa click - move then click"""
        try:
            box = await element.bounding_box()
            if not box:
                await element.click()
                return

            # Random click position within element
            x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
            y = box['y'] + box['height'] * random.uniform(0.3, 0.7)

            # Natural mouse move
            await HumanAI.natural_mouse_move(page, x, y)
            await HumanAI.click_delay()

            # Click
            await page.mouse.click(x, y)
            await HumanAI.think_delay()

        except Exception:
            try:
                await element.click()
            except Exception:
                pass

    # ---- Natural Typing ----
    @staticmethod
    async def natural_type(element, text):
        """Human jesi typing - random speed"""
        try:
            await element.click()
            await asyncio.sleep(0.2)
            await element.fill("")

            for i, char in enumerate(text):
                await element.type(char)

                # Random typing speed
                if char == ' ':
                    await asyncio.sleep(random.uniform(0.08, 0.2))
                elif random.random() < 0.05:
                    # Kabhi kabhi thoda ruko
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                else:
                    await asyncio.sleep(random.uniform(0.04, 0.12))

        except Exception as e:
            logger.error("Type error: %s" % str(e))

    # ---- Natural Scroll ----
    @staticmethod
    async def natural_scroll(page, direction="down"):
        """Human jesa scroll"""
        try:
            amount = random.randint(100, 300)
            if direction == "up":
                amount = -amount

            steps = random.randint(3, 7)
            for _ in range(steps):
                await page.mouse.wheel(0, amount // steps)
                await asyncio.sleep(random.uniform(0.05, 0.15))

        except Exception:
            pass

    # ---- Page Visit Simulation ----
    @staticmethod
    async def simulate_page_visit(page):
        """Human jesa page visit - read, scroll, look around"""
        try:
            # Page load hone do
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Thoda scroll karo
            if random.random() < 0.6:
                await HumanAI.natural_scroll(page, "down")
                await asyncio.sleep(random.uniform(0.3, 0.7))
                await HumanAI.natural_scroll(page, "up")

            # Random mouse movement
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, 350)
                y = random.randint(200, 600)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))

        except Exception:
            pass

    # ---- Smart Wait ----
    @staticmethod
    async def smart_wait(page, min_time=0.3, max_time=0.8):
        """Smart wait - network + random"""
        try:
            await asyncio.gather(
                page.wait_for_load_state('domcontentloaded', timeout=5000),
                asyncio.sleep(random.uniform(min_time, max_time))
            )
        except Exception:
            await asyncio.sleep(random.uniform(min_time, max_time))

    # ---- Browser Fingerprint Humanize ----
    @staticmethod
    async def humanize_browser(page):
        """Browser ko human jesa banao"""
        try:
            await page.add_init_script("""
                // WebDriver hide karo
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                
                // Plugins add karo
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin'},
                        {name: 'Chrome PDF Viewer'},
                        {name: 'Native Client'}
                    ]
                });
                
                // Languages set karo
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-IN', 'en', 'hi']
                });
                
                // Hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4
                });
                
                // Platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Linux armv8l'
                });
                
                // Chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
                );
            """)
        except Exception as e:
            logger.error("Humanize error: %s" % str(e))

human_ai = HumanAI()
