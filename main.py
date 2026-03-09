import asyncio
import re
import time
import os
from datetime import datetime
from logger import logger
from config import (PROFILES, WEBSITES, TELEGRAM_API_ID,
                    TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_GROUPS,
                    LOGIN_CHECK_INTERVAL, NOTIFY_TELEGRAM_USERNAME)
from browser_manager import browser_manager
from redeem_engine import redeem_code, auto_login, is_logged_in
from bot_control import bot_control
from smart_systems import (code_tracker, code_queue, speed_optimizer,
                           auto_backup, heartbeat, time_tracker)

# ============================================================
# INIT
# ============================================================
async def init_all_profiles():
    logger.info("Browser initializing...")
    await browser_manager.init()

    for profile in PROFILES:
        profile_id = profile['profile_id']
        pages = await browser_manager.create_profile_pages(profile_id, WEBSITES)
        for site_key in WEBSITES.keys():
            page = pages[site_key]
            account = profile[site_key]
            logger.info("Login: %s - %s" % (profile_id, site_key))
            await auto_login(page, account, site_key)
            await asyncio.sleep(0.5)

    logger.info("All profiles ready!")

# ============================================================
# HEALTH MONITOR
# ============================================================
async def health_monitor():
    while True:
        try:
            heartbeat.beat()
            for profile in PROFILES:
                profile_id = profile['profile_id']
                for site_key in WEBSITES.keys():
                    page = browser_manager.get_page(profile_id, site_key)
                    if page:
                        if not await is_logged_in(page):
                            logger.warning("Logged out: %s - %s" % (profile_id, site_key))
                            await auto_login(page, profile[site_key], site_key)
        except Exception as e:
            logger.error("Health error: %s" % str(e))
        await asyncio.sleep(LOGIN_CHECK_INTERVAL)

# ============================================================
# QUEUE PROCESSOR
# ============================================================
async def queue_processor():
    """Network wapas aaye toh queue process karo"""
    while True:
        if code_queue.has_items():
            logger.info("Processing queued codes...")
            items = code_queue.get_all()
            for item in items:
                await process_codes(item['codes'], item['site_key'])
        await asyncio.sleep(5)

# ============================================================
# DAILY REPORT
# ============================================================
async def send_daily_report(client):
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                msg = (
                    "DAILY REPORT - %s\n"
                    "%s\n\n"
                    "%s"
                ) % (
                    datetime.now().strftime("%d/%m/%Y"),
                    bot_control.get_status(),
                    time_tracker.get_report()
                )
                await client.send_message(NOTIFY_TELEGRAM_USERNAME, msg)
                logger.info("Daily report sent!")

                # Reset daily stats
                bot_control.stats['total'] = 0
                bot_control.stats['success'] = 0
                bot_control.stats['fail'] = 0

            except Exception as e:
                logger.error("Daily report error: %s" % str(e))
        await asyncio.sleep(60)

# ============================================================
# CORE PROCESS - Ultra fast
# ============================================================
async def process_codes(codes, site_key):
    # Paused check
    if bot_control.is_paused():
        logger.info("Bot paused - queueing codes")
        code_queue.add(codes, site_key)
        return

    # Duplicate filter
    codes = code_tracker.filter_new(codes)
    if not codes:
        logger.info("All codes already used!")
        return

    # Time pattern record
    time_tracker.record(site_key)

    start_time = time.time()

    logger.info("=" * 40)
    logger.info("CODES INCOMING!")
    logger.info("Site: %s | Codes: %d | Profiles: %d" % (
        site_key, len(codes), len(PROFILES)))
    logger.info("=" * 40)

    # Saare tasks ek saath
    all_tasks = []
    for code in codes:
        for profile in PROFILES:
            profile_id = profile['profile_id']
            page = browser_manager.get_page(profile_id, site_key)
            if page:
                task = asyncio.create_task(
                    redeem_code(page, profile[site_key], site_key, code)
                )
                all_tasks.append({'task': task, 'code': code, 'profile_id': profile_id})

    # SAB EK SAATH!
    results = await asyncio.gather(
        *[t['task'] for t in all_tasks],
        return_exceptions=True
    )

    success = 0
    failed = 0
    for i, result in enumerate(results):
        code = all_tasks[i]['code']
        if result is True:
            success += 1
            bot_control.add_result(code, site_key, True)
        else:
            failed += 1
            bot_control.add_result(code, site_key, False)

    # Mark codes as used
    for code in codes:
        code_tracker.mark_used(code)

    elapsed = time.time() - start_time
    speed_optimizer.record(site_key, elapsed)

    logger.info("=" * 40)
    logger.info("DONE! Success: %d | Failed: %d | Time: %.2fs" % (
        success, failed, elapsed))
    logger.info("=" * 40)

    await send_notification(codes, site_key, success, failed, elapsed)

# ============================================================
# NOTIFICATION
# ============================================================
async def send_notification(codes, site_key, success, failed, elapsed):
    try:
        from telethon import TelegramClient
        client = TelegramClient('notify_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.connect()

        emoji = "✅" if success > 0 else "❌"
        msg = (
            "%s RESULT\n"
            "Site: %s\n"
            "Codes: %d\n"
            "Success: %d | Failed: %d\n"
            "Time: %.2fs"
        ) % (emoji, site_key, len(codes), success, failed, elapsed)

        await client.send_message(NOTIFY_TELEGRAM_USERNAME, msg)
        await client.disconnect()
    except Exception as e:
        logger.error("Notification error: %s" % str(e))

# ============================================================
# TELEGRAM MONITOR
# ============================================================
async def start_telegram_monitor():
    from telethon import TelegramClient, events

    logger.info("Telegram connecting...")
    client = TelegramClient('main_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start(phone=TELEGRAM_PHONE)
    logger.info("Telegram connected!")

    # Bot commands register
    await bot_control.start_command_listener(client, NOTIFY_TELEGRAM_USERNAME)

    # Daily report start
    asyncio.create_task(send_daily_report(client))

    group_entities = []
    for group_link in TELEGRAM_GROUPS:
        try:
            entity = await client.get_entity(group_link)
            group_entities.append(entity)
            logger.info("Group: %s" % group_link)
        except Exception as e:
            logger.error("Group error: %s" % str(e))

    @client.on(events.NewMessage(chats=group_entities))
    async def on_message(event):
        text = event.message.text or ""

        # Codes extract
        all_codes = re.findall(r'[A-Fa-f0-9]{32}', text)
        if not all_codes:
            return

        codes = list(dict.fromkeys([c.upper() for c in all_codes]))

        # Sender name
        sender_name = ""
        try:
            sender = await event.get_sender()
            sender_name = (getattr(sender, 'title', '') or
                          getattr(sender, 'first_name', '') or "")
        except Exception:
            pass

        combined = (text + " " + sender_name).lower()

        # Site detect
        if "91" in combined and "club" in combined:
            site_key = "91"
        elif "55" in combined and "club" in combined:
            site_key = "55"
        elif "in999" in combined or "999" in combined:
            site_key = "999"
        elif "91" in combined:
            site_key = "91"
        elif "55" in combined:
            site_key = "55"
        else:
            logger.warning("Site detect nahi hua | Sender: %s" % sender_name)
            return

        logger.info("DETECTED! Site: %s | Codes: %d" % (site_key, len(codes)))
        asyncio.create_task(process_codes(codes, site_key))

    logger.info("All systems GO! Waiting for codes...")
    await client.run_until_disconnected()

# ============================================================
# MAIN
# ============================================================
async def main():
    logger.info("=" * 50)
    logger.info("AUTO REDEEM BOT - SUPER EDITION")
    logger.info("Profiles: %d | Sites: %d" % (len(PROFILES), len(WEBSITES)))
    logger.info("=" * 50)

    await init_all_profiles()

    # Start all background systems
    asyncio.create_task(health_monitor())
    asyncio.create_task(queue_processor())
    asyncio.create_task(auto_backup.backup_loop())
    asyncio.create_task(heartbeat.monitor(None))

    logger.info("All systems started!")
    logger.info("Commands: /status /pause /resume /stats /history")

    await start_telegram_monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped!")
        asyncio.run(browser_manager.close())
    except Exception as e:
        logger.error("Fatal: %s" % str(e))
