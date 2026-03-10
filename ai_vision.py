import asyncio
import base64
import json
import aiohttp
from logger import logger
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

class AIVision:
    """Claude AI Vision - Website screenshot dekh ke smart decisions"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    async def analyze_screenshot(self, screenshot_bytes, question):
        """Screenshot bhejo - Claude batayega kya karna hai"""
        try:
            img_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            headers = {
                "Authorization": "Bearer %s" % self.api_key,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com",
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/png;base64,%s" % img_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": question
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    data = await resp.json()
                    answer = data['choices'][0]['message']['content']
                    logger.info("AI Vision: %s" % answer[:100])
                    return answer
                    
        except Exception as e:
            logger.error("AI Vision error: %s" % str(e))
            return None

    async def find_gift_button(self, page):
        """Screenshot le ke Claude se pucho - gift button kahan hai"""
        try:
            screenshot = await page.screenshot()
            answer = await self.analyze_screenshot(
                screenshot,
                "This is a gaming website. Find the 'Gift' or 'Redeem' or 'Gifts' button. "
                "Reply with ONLY the button text you can see. If not found say 'NOT_FOUND'."
            )
            return answer
        except Exception as e:
            logger.error("Find gift button error: %s" % str(e))
            return None

    async def check_success(self, page):
        """Screenshot le ke Claude se pucho - success hua ya nahi"""
        try:
            screenshot = await page.screenshot()
            answer = await self.analyze_screenshot(
                screenshot,
                "Did the gift code redemption succeed? Look for success messages, "
                "congratulation text, or error messages. Reply with only: SUCCESS or FAILED or UNKNOWN"
            )
            if answer:
                return "SUCCESS" in answer.upper()
            return None
        except Exception as e:
            logger.error("Check success error: %s" % str(e))
            return None

    async def detect_site_from_message(self, message_text):
        """Claude message padh ke site detect kare"""
        try:
            headers = {
                "Authorization": "Bearer %s" % self.api_key,
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": "anthropic/claude-3-haiku",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "This is a Telegram message about gaming gift codes. "
                            "Which website is this code for? Options: 91 (91Club/BigMumbai), "
                            "55 (55Club), 999 (IN999). "
                            "Message: '%s' "
                            "Reply with ONLY: 91 or 55 or 999 or UNKNOWN"
                        ) % message_text[:500]
                    }
                ],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    data = await resp.json()
                    answer = data['choices'][0]['message']['content'].strip()
                    logger.info("AI Site Detection: %s" % answer)
                    
                    if "91" in answer:
                        return "91"
                    elif "55" in answer:
                        return "55"
                    elif "999" in answer:
                        return "999"
                    return None
                    
        except Exception as e:
            logger.error("AI site detect error: %s" % str(e))
            return None

ai_vision = AIVision()
