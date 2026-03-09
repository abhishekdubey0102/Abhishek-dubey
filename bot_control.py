import asyncio
from datetime import datetime
from logger import logger

class BotControl:
    """Telegram Bot se script control karo"""
    
    def __init__(self):
        self.paused = False
        self.start_time = datetime.now()
        self.stats = {
            "total": 0, "success": 0, "fail": 0,
            "codes_history": [], "balance": {}
        }
    
    def is_paused(self):
        return self.paused

    def add_result(self, code, site_key, success):
        self.stats["total"] += 1
        if success:
            self.stats["success"] += 1
        else:
            self.stats["fail"] += 1
        
        # Last 10 codes
        self.stats["codes_history"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "code": code[:8] + "...",
            "site": site_key,
            "success": success
        })
        if len(self.stats["codes_history"]) > 10:
            self.stats["codes_history"].pop(0)

    def get_status(self):
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        mins = int((uptime.total_seconds() % 3600) // 60)
        return (
            "BOT STATUS\n"
            "Running: %dh %dm\n"
            "State: %s\n"
            "Total codes: %d\n"
            "Success: %d\n"
            "Failed: %d"
        ) % (
            hours, mins,
            "PAUSED" if self.paused else "ACTIVE",
            self.stats["total"],
            self.stats["success"],
            self.stats["fail"]
        )

    def get_history(self):
        if not self.stats["codes_history"]:
            return "No codes yet!"
        lines = ["LAST CODES:"]
        for h in reversed(self.stats["codes_history"]):
            emoji = "✅" if h["success"] else "❌"
            lines.append("%s %s | %s | %s" % (
                emoji, h["time"], h["site"], h["code"]))
        return "\n".join(lines)

    async def start_command_listener(self, client, notify_username):
        """Telegram commands listen karo"""
        from telethon import events

        @client.on(events.NewMessage(pattern='/status'))
        async def status_cmd(event):
            try:
                sender = await event.get_sender()
                username = getattr(sender, 'username', '') or ''
                if notify_username.replace('@', '') in username:
                    await event.respond(self.get_status())
            except Exception as e:
                logger.error("Status cmd error: %s" % str(e))

        @client.on(events.NewMessage(pattern='/pause'))
        async def pause_cmd(event):
            try:
                sender = await event.get_sender()
                username = getattr(sender, 'username', '') or ''
                if notify_username.replace('@', '') in username:
                    self.paused = True
                    await event.respond("Bot PAUSED!")
                    logger.info("Bot paused by user")
            except Exception as e:
                logger.error("Pause cmd error: %s" % str(e))

        @client.on(events.NewMessage(pattern='/resume'))
        async def resume_cmd(event):
            try:
                sender = await event.get_sender()
                username = getattr(sender, 'username', '') or ''
                if notify_username.replace('@', '') in username:
                    self.paused = False
                    await event.respond("Bot RESUMED!")
                    logger.info("Bot resumed by user")
            except Exception as e:
                logger.error("Resume cmd error: %s" % str(e))

        @client.on(events.NewMessage(pattern='/stats'))
        async def stats_cmd(event):
            try:
                sender = await event.get_sender()
                username = getattr(sender, 'username', '') or ''
                if notify_username.replace('@', '') in username:
                    msg = (
                        "TODAY STATS\n"
                        "Total: %d\n"
                        "Success: %d\n"
                        "Failed: %d"
                    ) % (
                        self.stats["total"],
                        self.stats["success"],
                        self.stats["fail"]
                    )
                    await event.respond(msg)
            except Exception as e:
                logger.error("Stats cmd error: %s" % str(e))

        @client.on(events.NewMessage(pattern='/history'))
        async def history_cmd(event):
            try:
                sender = await event.get_sender()
                username = getattr(sender, 'username', '') or ''
                if notify_username.replace('@', '') in username:
                    await event.respond(self.get_history())
            except Exception as e:
                logger.error("History cmd error: %s" % str(e))

        logger.info("Bot commands ready! /status /pause /resume /stats /history")

bot_control = BotControl()
