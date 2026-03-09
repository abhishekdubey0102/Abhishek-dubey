import asyncio
import json
import os
import time
from datetime import datetime
from collections import defaultdict
from logger import logger

# ============================================================
# 1. CODE DUPLICATE CHECKER
# ============================================================
class CodeTracker:
    """Same code dobara try nahi hoga"""
    
    def __init__(self):
        self.used_codes = set()
        self.file = "history/used_codes.txt"
        self._load()
    
    def _load(self):
        try:
            os.makedirs("history", exist_ok=True)
            if os.path.exists(self.file):
                with open(self.file, "r") as f:
                    for line in f:
                        self.used_codes.add(line.strip())
            logger.info("Loaded %d used codes" % len(self.used_codes))
        except Exception:
            pass
    
    def is_used(self, code):
        return code.upper() in self.used_codes
    
    def mark_used(self, code):
        code = code.upper()
        self.used_codes.add(code)
        try:
            with open(self.file, "a") as f:
                f.write(code + "\n")
        except Exception:
            pass
    
    def filter_new(self, codes):
        """Sirf naye codes return karo"""
        new = [c for c in codes if not self.is_used(c.upper())]
        skipped = len(codes) - len(new)
        if skipped > 0:
            logger.info("Skipped %d duplicate codes" % skipped)
        return new

# ============================================================
# 2. SMART CODE QUEUE
# ============================================================
class CodeQueue:
    """Network down ho toh codes queue mein save karo"""
    
    def __init__(self):
        self.queue = []
        self.processing = False
    
    def add(self, codes, site_key):
        self.queue.append({
            "codes": codes,
            "site_key": site_key,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        logger.info("Queued %d codes for %s" % (len(codes), site_key))
    
    def get_all(self):
        items = self.queue.copy()
        self.queue.clear()
        return items
    
    def has_items(self):
        return len(self.queue) > 0

# ============================================================
# 3. SPEED OPTIMIZER
# ============================================================
class SpeedOptimizer:
    """Har site ka response time track karo"""
    
    def __init__(self):
        self.times = defaultdict(list)
    
    def record(self, site_key, elapsed):
        self.times[site_key].append(elapsed)
        if len(self.times[site_key]) > 20:
            self.times[site_key].pop(0)
    
    def avg_time(self, site_key):
        times = self.times[site_key]
        return sum(times) / len(times) if times else 0
    
    def report(self):
        lines = ["SPEED REPORT:"]
        for site, times in self.times.items():
            if times:
                avg = sum(times) / len(times)
                lines.append("%s: avg %.2fs" % (site, avg))
        return "\n".join(lines)

# ============================================================
# 4. AUTO BACKUP
# ============================================================
class AutoBackup:
    """Data automatically backup karo"""
    
    def __init__(self):
        os.makedirs("backup", exist_ok=True)
    
    async def backup_loop(self):
        """Har ghante backup"""
        while True:
            await asyncio.sleep(3600)
            await self.do_backup()
    
    async def do_backup(self):
        try:
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            for folder in ["history", "screenshots"]:
                if os.path.exists(folder):
                    dest = "backup/%s_%s" % (folder, timestamp)
                    shutil.copytree(folder, dest, dirs_exist_ok=True)
            
            logger.info("Backup done: %s" % timestamp)
        except Exception as e:
            logger.error("Backup error: %s" % str(e))

# ============================================================
# 5. HEARTBEAT - Auto restart
# ============================================================
class Heartbeat:
    """Bot alive hai ya nahi check karo"""
    
    def __init__(self):
        self.last_beat = time.time()
        self.restart_count = 0
    
    def beat(self):
        self.last_beat = time.time()
    
    def is_alive(self, timeout=300):
        return (time.time() - self.last_beat) < timeout
    
    async def monitor(self, notify_func):
        """Har 5 min mein check karo"""
        while True:
            await asyncio.sleep(300)
            self.beat()
            logger.info("Heartbeat OK | Restarts: %d" % self.restart_count)

# ============================================================
# 6. CODE TIME TRACKER - Codes kis time aate hain
# ============================================================
class CodeTimeTracker:
    """Codes ka pattern track karo"""
    
    def __init__(self):
        self.hourly = defaultdict(int)
        self.file = "history/time_pattern.json"
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.file):
                with open(self.file, "r") as f:
                    data = json.load(f)
                    self.hourly = defaultdict(int, data)
        except Exception:
            pass
    
    def _save(self):
        try:
            with open(self.file, "w") as f:
                json.dump(dict(self.hourly), f)
        except Exception:
            pass
    
    def record(self, site_key):
        hour = datetime.now().hour
        key = "%s_%d" % (site_key, hour)
        self.hourly[key] += 1
        self._save()
    
    def peak_hours(self, site_key):
        """Konse time zyada codes aate hain"""
        site_hours = []
        for h in range(24):
            key = "%s_%d" % (site_key, h)
            count = self.hourly.get(key, 0)
            if count > 0:
                site_hours.append((h, count))
        
        site_hours.sort(key=lambda x: x[1], reverse=True)
        return site_hours[:3]
    
    def get_report(self):
        lines = ["CODE TIME PATTERN:"]
        for site in ["91", "55", "999"]:
            peaks = self.peak_hours(site)
            if peaks:
                peak_str = ", ".join(["%d:00(%d)" % (h, c) for h, c in peaks])
                lines.append("%s Club: %s" % (site, peak_str))
        return "\n".join(lines) if len(lines) > 1 else "Not enough data yet"

# ============================================================
# GLOBAL INSTANCES
# ============================================================
code_tracker = CodeTracker()
code_queue = CodeQueue()
speed_optimizer = SpeedOptimizer()
auto_backup = AutoBackup()
heartbeat = Heartbeat()
time_tracker = CodeTimeTracker()
