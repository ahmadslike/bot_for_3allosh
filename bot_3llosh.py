import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import traceback
import random
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# ======================
# 🔧 إعدادات البوت العامة
# ======================
BOT_TOKEN = "8672456217:AAFRqjW1BVklZcQkI1TuucLjfsXxXZx-Hj8" 
CHAT_IDS = ["-5248175111", "-1003793131150"]
DB_PATH = "bot.db"
FORCE_SUB_ENABLED = False
BOT_ACTIVE = True
REFRESH_INTERVAL = 1
TIMEOUT = 100
MAX_RETRIES = 5
RETRY_DELAY = 5
MAX_WORKERS = 6  # عدد الحسابات الكلي (3 + 3)

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN must be set")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS must be configured")

# ======================
# 🌍 رموز الدول (كاملاً - اختصرت بعض الأجزاء للطول، لكن يجب وضع القاموس الكامل)
# ======================
COUNTRY_CODES = {
    "1": ("𝐔𝐒𝐀/𝐂𝐚𝐧𝐚𝐝𝐚", "『🇺🇸』", "𝐔𝐒𝐀/𝐂𝐀𝐍𝐀𝐃𝐀"),
    "7": ("𝐊𝐚𝐳𝐚𝐤𝐡𝐬𝐭𝐚𝐧", "『🇰🇿』", "𝐊𝐀𝐙𝐀𝐊𝐇𝐒𝐓𝐀𝐍"),
    "79": ("𝐑𝐔𝐒𝐒𝐈𝐀", "『🇷🇺』", "𝗥𝗨𝗦𝗦𝗜𝗔"),
    "20": ("𝐄𝐠𝐲𝐩𝐭", "『🇪🇬』", "𝐄𝐆𝐘𝐏𝐓"),
    "27": ("𝐒𝐨𝐮𝐭𝐡 𝐀𝐟𝐫𝐢𝐜𝐚", "『🇿🇦』", "𝐒𝐎𝐔𝐓𝐇 𝐀𝐅𝐑𝐈𝐂𝐀"),
    "30": ("𝐆𝐫𝐞𝐞𝐜𝐞", "『🇬🇷』", "𝐆𝐑𝐄𝐄𝐂𝐄"),
    "31": ("𝐍𝐞𝐭𝐡𝐞𝐫𝐥𝐚𝐧𝐝𝐬", "『🇳🇱』", "𝐍𝐄𝐓𝐇𝐄𝐑𝐋𝐀𝐍𝐃𝐒"),
    "32": ("𝐁𝐞𝐥𝐠𝐢𝐮𝐦", "『🇧🇪』", "𝐁𝐄𝐋𝐆𝐈𝐔𝐌"),
    "33": ("𝐅𝐫𝐚𝐧𝐜𝐞", "『🇫🇷』", "𝐅𝐑𝐀𝐍𝐂𝐄"),
    "34": ("𝐒𝐩𝐚𝐢𝐧", "『🇪🇸』", "𝐒𝐏𝐀𝐈𝐍"),
    "36": ("𝐇𝐮𝐧𝐠𝐚𝐫𝐲", "『🇭🇺』", "𝐇𝐔𝐍𝐆𝐀𝐑𝐘"),
    "39": ("𝐈𝐭𝐚𝐥𝐲", "『🇮🇹』", "𝐈𝐓𝐀𝐋𝐘"),
    "40": ("𝐑𝐨𝐦𝐚𝐧𝐢𝐚", "『🇷🇴』", "𝐑𝐎𝐌𝐀𝐍𝐈𝐀"),
    "41": ("𝐒𝐰𝐢𝐭𝐳𝐞𝐫𝐥𝐚𝐧𝐝", "『🇨🇭』", "𝐒𝐖𝐈𝐓𝐙𝐄𝐑𝐋𝐀𝐍𝐃"),
    "43": ("𝐀𝐮𝐬𝐭𝐫𝐢𝐚", "『🇦🇹』", "𝐀𝐔𝐒𝐓𝐑𝐈𝐀"),
    "44": ("𝐔𝐊", "『🇬🇧』", "𝐔𝐊"),
    "45": ("𝐃𝐞𝐧𝐦𝐚𝐫𝐤", "『🇩🇰』", "𝐃𝐄𝐍𝐌𝐀𝐑𝐊"),
    "46": ("𝐒𝐰𝐞𝐝𝐞𝐧", "『🇸🇪』", "𝐒𝐖𝐄𝐃𝐄𝐍"),
    "47": ("𝐍𝐨𝐫𝐰𝐚𝐲", "『🇳🇴』", "𝐍𝐎𝐑𝐖𝐀𝐘"),
    "48": ("𝐏𝐨𝐥𝐚𝐧𝐝", "『🇵🇱』", "𝐏𝐎𝐋𝐀𝐍𝐃"),
    "49": ("𝐆𝐞𝐫𝐦𝐚𝐧𝐲", "『🇩🇪』", "𝐆𝐄𝐑𝐌𝐀𝐍𝐘"),
    "51": ("𝐏𝐞𝐫𝐮", "『🇵🇪』", "𝐏𝐄𝐑𝐔"),
    "52": ("𝐌𝐞𝐱𝐢𝐜𝐨", "『🇲🇽』", "𝐌𝐄𝐗𝐈𝐂𝐎"),
    "53": ("𝐂𝐮𝐛𝐚", "『🇨🇺』", "𝐂𝐔𝐁𝐀"),
    "54": ("𝐀𝐫𝐠𝐞𝐧𝐭𝐢𝐧𝐚", "『🇦🇷』", "𝐀𝐑𝐆𝐄𝐍𝐓𝐈𝐍𝐀"),
    "55": ("𝐁𝐫𝐚𝐳𝐢𝐥", "『🇧🇷』", "𝐁𝐑𝐀𝐙𝐈𝐋"),
    "56": ("𝐂𝐡𝐢𝐥𝐞", "『🇨🇱』", "𝐂𝐇𝐈𝐋𝐄"),
    "57": ("𝐂𝐨𝐥𝐨𝐦𝐛𝐢𝐚", "『🇨🇴』", "𝐂𝐎𝐋𝐎𝐌𝐁𝐈𝐀"),
    "58": ("𝐕𝐞𝐧𝐞𝐳𝐮𝐞𝐥𝐚", "『🇻🇪』", "𝐕𝐄𝐍𝐄𝐙𝐔𝐄𝐋𝐀"),
    "60": ("𝐌𝐚𝐥𝐚𝐲𝐬𝐢𝐚", "『🇲🇾』", "𝐌𝐀𝐋𝐀𝐘𝐒𝐈𝐀"),
    "61": ("𝐀𝐮𝐬𝐭𝐫𝐚𝐥𝐢𝐚", "『🇦🇺』", "𝐀𝐔𝐒𝐓𝐑𝐀𝐋𝐈𝐀"),
    "62": ("𝐈𝐧𝐝𝐨𝐧𝐞𝐬𝐢𝐚", "『🇮🇩』", "𝐈𝐍𝐃𝐎𝐍𝐄𝐒𝐈𝐀"),
    "63": ("𝐏𝐡𝐢𝐥𝐢𝐩𝐩𝐢𝐧𝐞𝐬", "『🇵🇭』", "𝐏𝐇𝐈𝐋𝐈𝐏𝐏𝐈𝐍𝐄𝐒"),
    "64": ("𝐍𝐞𝐰 𝐙𝐞𝐚𝐥𝐚𝐧𝐝", "『🇳🇿』", "𝐍𝐄𝐖 𝐙𝐄𝐀𝐋𝐀𝐍𝐃"),
    "65": ("𝐒𝐢𝐧𝐠𝐚𝐩𝐨𝐫𝐞", "『🇸🇬』", "𝐒𝐈𝐍𝐆𝐀𝐏𝐎𝐑𝐄"),
    "66": ("𝐓𝐡𝐚𝐢𝐥𝐚𝐧𝐝", "『🇹🇭』", "𝐓𝐇𝐀𝐈𝐋𝐀𝐍𝐃"),
    "81": ("𝐉𝐚𝐩𝐚𝐧", "『🇯🇵』", "𝐉𝐀𝐏𝐀𝐍"),
    "82": ("𝐒𝐨𝐮𝐭𝐡 𝐊𝐨𝐫𝐞𝐚", "『🇰🇷』", "𝐒𝐎𝐔𝐓𝐇 𝐊𝐎𝐑𝐄𝐀"),
    "84": ("𝐕𝐢𝐞𝐭𝐧𝐚𝐦", "『🇻🇳』", "𝐕𝐈𝐄𝐓𝐍𝐀𝐌"),
    "86": ("𝐂𝐡𝐢𝐧𝐚", "『🇨🇳』", "𝐂𝐇𝐈𝐍𝐀"),
    "90": ("𝐓𝐮𝐫𝐤𝐞𝐲", "『🇹🇷』", "𝐓𝐔𝐑𝐊𝐄𝐘"),
    "91": ("𝐈𝐧𝐝𝐢𝐚", "『🇮🇳』", "𝐈𝐍𝐃𝐈𝐀"),
    "92": ("𝐏𝐚𝐤𝐢𝐬𝐭𝐚𝐧", "『🇵🇰』", "𝐏𝐀𝐊𝐈𝐒𝐓𝐀𝐍"),
    "93": ("𝐀𝐟𝐠𝐡𝐚𝐧𝐢𝐬𝐭𝐚𝐧", "『🇦🇫』", "𝐀𝐅𝐆𝐇𝐀𝐍𝐈𝐒𝐓𝐀𝐍"),
    "94": ("𝐒𝐫𝐢 𝐋𝐚𝐧𝐤𝐚", "『🇱🇰』", "𝐒𝐑𝐈 𝐋𝐀𝐍𝐊𝐀"),
    "95": ("𝐌𝐲𝐚𝐧𝐦𝐚𝐫", "『🇲🇲』", "𝐌𝐘𝐀𝐍𝐌𝐀𝐑"),
    "98": ("𝐈𝐫𝐚𝐧", "『🇮🇷』", "𝐈𝐑𝐀𝐍"),
    "211": ("𝐒𝐨𝐮𝐭𝐡 𝐒𝐮𝐝𝐚𝐧", "『🇸🇸』", "𝐒𝐎𝐔𝐓𝐇 𝐒𝐔𝐃𝐀𝐍"),
    "212": ("𝐌𝐨𝐫𝐨𝐜𝐜𝐨", "『🇲🇦』", "𝐌𝐎𝐑𝐎𝐂𝐂𝐎"),
    "213": ("𝐀𝐥𝐠𝐞𝐫𝐢𝐚", "『🇩🇿』", "𝐀𝐋𝐆𝐄𝐑𝐈𝐀"),
    "216": ("𝐓𝐮𝐧𝐢𝐬𝐢𝐚", "『🇹🇳』", "𝐓𝐔𝐍𝐈𝐒𝐈𝐀"),
    "218": ("𝐋𝐢𝐛𝐲𝐚", "『🇱🇾』", "𝐋𝐈𝐁𝐘𝐀"),
    "220": ("𝐆𝐚𝐦𝐛𝐢𝐚", "『🇬🇲』", "𝐆𝐀𝐌𝐁𝐈𝐀"),
    "221": ("𝐒𝐞𝐧𝐞𝐠𝐚𝐥", "『🇸🇳』", "𝐒𝐄𝐍𝐄𝐆𝐀𝐋"),
    "222": ("𝐌𝐚𝐮𝐫𝐢𝐭𝐚𝐧𝐢𝐚", "『🇲🇷』", "𝐌𝐀𝐔𝐑𝐈𝐓𝐀𝐍𝐈𝐀"),
    "223": ("𝐌𝐚𝐥𝐢", "『🇲🇱』", "𝐌𝐀𝐋𝐈"),
    "224": ("𝐆𝐮𝐢𝐧𝐞𝐚", "『🇬🇳』", "𝐆𝐔𝐈𝐍𝐄𝐀"),
    "225": ("𝐈𝐯𝐨𝐫𝐲 𝐂𝐨𝐚𝐬𝐭", "『🇨🇮』", "𝐈𝐕𝐎𝐑𝐘 𝐂𝐎𝐀𝐒𝐓"),
    "226": ("𝐁𝐮𝐫𝐤𝐢𝐧𝐚 𝐅𝐚𝐬𝐨", "『🇧🇫』", "𝐁𝐔𝐑𝐊𝐈𝐍𝐀 𝐅𝐀𝐒𝐎"),
    "227": ("𝐍𝐢𝐠𝐞𝐫", "『🇳🇪』", "𝐍𝐈𝐆𝐄𝐑"),
    "228": ("𝐓𝐨𝐠𝐨", "『🇹🇬』", "𝐓𝐎𝐆𝐎"),
    "229": ("𝐁𝐞𝐧𝐢𝐧", "『🇧🇯』", "𝐁𝐄𝐍𝐈𝐍"),
    "230": ("𝐌𝐚𝐮𝐫𝐢𝐭𝐢𝐮𝐬", "『🇲🇺』", "𝐌𝐀𝐔𝐑𝐈𝐓𝐈𝐔𝐒"),
    "231": ("𝐋𝐢𝐛𝐞𝐫𝐢𝐚", "『🇱🇷』", "𝐋𝐈𝐁𝐄𝐑𝐈𝐀"),
    "232": ("𝐒𝐢𝐞𝐫𝐫𝐚 𝐋𝐞𝐨𝐧𝐞", "『🇸🇱』", "𝐒𝐈𝐄𝐑𝐑𝐀 𝐋𝐄𝐎𝐍𝐄"),
    "233": ("𝐆𝐡𝐚𝐧𝐚", "『🇬🇭』", "𝐆𝐇𝐀𝐍𝐀"),
    "234": ("𝐍𝐢𝐠𝐞𝐫𝐢𝐚", "『🇳🇬』", "𝐍𝐈𝐆𝐄𝐑𝐈𝐀"),
    "235": ("𝐂𝐡𝐚𝐝", "『🇹🇩』", "𝐂𝐇𝐀𝐃"),
    "236": ("𝐂𝐀𝐑", "『🇨🇫』", "𝐂𝐄𝐍𝐓𝐑𝐀𝐋 𝐀𝐅𝐑𝐈𝐂𝐀𝐍 𝐑𝐄𝐏"),
    "237": ("𝐂𝐚𝐦𝐞𝐫𝐨𝐨𝐧", "『🇨🇲』", "𝐂𝐀𝐌𝐄𝐑𝐎𝐎𝐍"),
    "238": ("𝐂𝐚𝐩𝐞 𝐕𝐞𝐫𝐝𝐞", "『🇨🇻』", "𝐂𝐀𝐏𝐄 𝐕𝐄𝐑𝐃𝐄"),
    "239": ("𝐒𝐚𝐨 𝐓𝐨𝐦𝐞", "『🇸🇹』", "𝐒𝐀𝐎 𝐓𝐎𝐌𝐄"),
    "240": ("𝐄𝐪. 𝐆𝐮𝐢𝐧𝐞𝐚", "『🇬🇶』", "𝐄𝐐𝐔𝐀𝐓𝐎𝐑𝐈𝐀𝐋 𝐆𝐔𝐈𝐍𝐄𝐀"),
    "241": ("𝐆𝐚𝐛𝐨𝐧", "『🇬🇦』", "𝐆𝐀𝐁𝐎𝐍"),
    "242": ("𝐂𝐨𝐧𝐠𝐨", "『🇨🇬』", "𝐂𝐎𝐍𝐆𝐎"),
    "243": ("𝐃𝐑 𝐂𝐨𝐧𝐠𝐨", "『🇨🇩』", "𝐃𝐑 𝐂𝐎𝐍𝐆𝐎"),
    "244": ("𝐀𝐧𝐠𝐨𝐥𝐚", "『🇦🇴』", "𝐀𝐍𝐆𝐎𝐋𝐀"),
    "245": ("𝐆𝐮𝐢𝐧𝐞𝐚-𝐁𝐢𝐬𝐬𝐚𝐮", "『🇬🇼』", "𝐆𝐔𝐈𝐍𝐄𝐀-𝐁𝐈𝐒𝐒𝐀𝐔"),
    "248": ("𝐒𝐞𝐲𝐜𝐡𝐞𝐥𝐥𝐞𝐬", "『🇸🇨』", "𝐒𝐄𝐘𝐂𝐇𝐄𝐋𝐋𝐄𝐒"),
    "249": ("𝐒𝐮𝐝𝐚𝐧", "『🇸🇩』", "𝐒𝐔𝐃𝐀𝐍"),
    "250": ("𝐑𝐰𝐚𝐧𝐝𝐚", "『🇷🇼』", "𝐑𝐖𝐀𝐍𝐃𝐀"),
    "251": ("𝐄𝐭𝐡𝐢𝐨𝐩𝐢𝐚", "『🇪🇹』", "𝐄𝐓𝐇𝐈𝐎𝐏𝐈𝐀"),
    "252": ("𝐒𝐨𝐦𝐚𝐥𝐢𝐚", "『🇸🇴』", "𝐒𝐎𝐌𝐀𝐋𝐈𝐀"),
    "253": ("𝐃𝐣𝐢𝐛𝐨𝐮𝐭𝐢", "『🇩🇯』", "𝐃𝐉𝐈𝐁𝐎𝐔𝐓𝐈"),
    "254": ("𝐊𝐞𝐧𝐲𝐚", "『🇰🇪』", "𝐊𝐄𝐍𝐘𝐀"),
    "255": ("𝐓𝐚𝐧𝐳𝐚𝐧𝐢𝐚", "『🇹🇿』", "𝐓𝐀𝐍𝐙𝐀𝐍𝐈𝐀"),
    "256": ("𝐔𝐠𝐚𝐧𝐝𝐚", "『🇺🇬』", "𝐔𝐆𝐀𝐍𝐃𝐀"),
    "257": ("𝐁𝐮𝐫𝐮𝐧𝐝𝐢", "『🇧🇮』", "𝐁𝐔𝐑𝐔𝐍𝐃𝐈"),
    "258": ("𝐌𝐨𝐳𝐚𝐦𝐛𝐢𝐪𝐮𝐞", "『🇲🇿』", "𝐌𝐎𝐙𝐀𝐌𝐁𝐈𝐐𝐔𝐄"),
    "260": ("𝐙𝐚𝐦𝐛𝐢𝐚", "『🇿🇲』", "𝐙𝐀𝐌𝐁𝐈𝐀"),
    "261": ("𝐌𝐚𝐝𝐚𝐠𝐚𝐬𝐜𝐚𝐫", "『🇲🇬』", "𝐌𝐀𝐃𝐀𝐆𝐀𝐒𝐂𝐀𝐑"),
    "262": ("𝐑𝐞𝐮𝐧𝐢𝐨𝐧", "『🇷🇪』", "𝐑𝐄𝐔𝐍𝐈𝐎𝐍"),
    "263": ("𝐙𝐢𝐦𝐛𝐚𝐛𝐰𝐞", "『🇿🇼』", "𝐙𝐈𝐌𝐁𝐀𝐁𝐖𝐄"),
    "264": ("𝐍𝐚𝐦𝐢𝐛𝐢𝐚", "『🇳🇦』", "𝐍𝐀𝐌𝐈𝐁𝐈𝐀"),
    "265": ("𝐌𝐚𝐥𝐚𝐰𝐢", "『🇲🇼』", "𝐌𝐀𝐋𝐀𝐖𝐈"),
    "266": ("𝐋𝐞𝐬𝐨𝐭𝐡𝐨", "『🇱🇸』", "𝐋𝐄𝐒𝐎𝐓𝐇𝐎"),
    "267": ("𝐁𝐨𝐭𝐬𝐰𝐚𝐧𝐚", "『🇧🇼』", "𝐁𝐎𝐓𝐒𝐖𝐀𝐍𝐀"),
    "268": ("𝐄𝐬𝐰𝐚𝐭𝐢𝐧𝐢", "『🇸🇿』", "𝐄𝐒𝐖𝐀𝐓𝐈𝐍𝐈"),
    "269": ("𝐂𝐨𝐦𝐨𝐫𝐨𝐬", "『🇰🇲』", "𝐂𝐎𝐌𝐎𝐑𝐎𝐒"),
    "350": ("𝐆𝐢𝐛𝐫𝐚𝐥𝐭𝐚𝐫", "『🇬🇮』", "𝐆𝐈𝐁𝐑𝐀𝐋𝐓𝐀𝐑"),
    "351": ("𝐏𝐨𝐫𝐭𝐮𝐠𝐚𝐥", "『🇵🇹』", "𝐏𝐎𝐑𝐓𝐔𝐆𝐀𝐋"),
    "352": ("𝐋𝐮𝐱𝐞𝐦𝐛𝐨𝐮𝐫𝐠", "『🇱🇺』", "𝐋𝐔𝐗𝐄𝐌𝐁𝐎𝐔𝐑𝐆"),
    "353": ("𝐈𝐫𝐞𝐥𝐚𝐧𝐝", "『🇮🇪』", "𝐈𝐑𝐄𝐋𝐀𝐍𝐃"),
    "354": ("𝐈𝐜𝐞𝐥𝐚𝐧𝐝", "『🇮🇸』", "𝐈𝐂𝐄𝐋𝐀𝐍𝐃"),
    "355": ("𝐀𝐥𝐛𝐚𝐧𝐢𝐚", "『🇦🇱』", "𝐀𝐋𝐁𝐀𝐍𝐈𝐀"),
    "356": ("𝐌𝐚𝐥𝐭𝐚", "『🇲🇹』", "𝐌𝐀𝐋𝐓𝐀"),
    "357": ("𝐂𝐲𝐩𝐫𝐮𝐬", "『🇨🇾』", "𝐂𝐘𝐏𝐑𝐔𝐒"),
    "358": ("𝐅𝐢𝐧𝐥𝐚𝐧𝐝", "『🇫🇮』", "𝐅𝐈𝐍𝐋𝐀𝐍𝐃"),
    "359": ("𝐁𝐮𝐥𝐠𝐚𝐫𝐢𝐚", "『🇧🇬』", "𝐁𝐔𝐋𝐆𝐀𝐑𝐈𝐀"),
    "370": ("𝐋𝐢𝐭𝐡𝐮𝐚𝐧𝐢𝐚", "『🇱🇹』", "𝐋𝐈𝐓𝐇𝐔𝐀𝐍𝐈𝐀"),
    "371": ("𝐋𝐚𝐭𝐯𝐢𝐚", "『🇱🇻』", "𝐋𝐀𝐓𝐕𝐈𝐀"),
    "372": ("𝐄𝐬𝐭𝐨𝐧𝐢𝐚", "『🇪🇪』", "𝐄𝐒𝐓𝐎𝐍𝐈𝐀"),
    "373": ("𝐌𝐨𝐥𝐝𝐨𝐯𝐚", "『🇲🇩』", "𝐌𝐎𝐋𝐃𝐎𝐕𝐀"),
    "374": ("𝐀𝐫𝐦𝐞𝐧𝐢𝐚", "『🇦🇲』", "𝐀𝐑𝐌𝐄𝐍𝐈𝐀"),
    "375": ("𝐁𝐞𝐥𝐚𝐫𝐮𝐬", "『🇧🇾』", "𝐁𝐄𝐋𝐀𝐑𝐔𝐒"),
    "376": ("𝐀𝐧𝐝𝐨𝐫𝐫𝐚", "『🇦🇩』", "𝐀𝐍𝐃𝐎𝐑𝐑𝐀"),
    "377": ("𝐌𝐨𝐧𝐚𝐜𝐨", "『🇲🇨』", "𝐌𝐎𝐍𝐀𝐂𝐎"),
    "378": ("𝐒𝐚𝐧 𝐌𝐚𝐫𝐢𝐧𝐨", "『🇸🇲』", "𝐒𝐀𝐍 𝐌𝐀𝐑𝐈𝐍𝐎"),
    "380": ("𝐔𝐤𝐫𝐚𝐢𝐧𝐞", "『🇺🇦』", "𝐔𝐊𝐑𝐀𝐈𝐍𝐄"),
    "381": ("𝐒𝐞𝐫𝐛𝐢𝐚", "『🇷🇸』", "𝐒𝐄𝐑𝐁𝐈𝐀"),
    "382": ("𝐌𝐨𝐧𝐭𝐞𝐧𝐞𝐠𝐫𝐨", "『🇲🇪』", "𝐌𝐎𝐍𝐓𝐄𝐍𝐄𝐆𝐑𝐎"),
    "383": ("𝐊𝐨𝐬𝐨𝐯𝐨", "『🇽🇰』", "𝐊𝐎𝐒𝐎𝐕𝐎"),
    "385": ("𝐂𝐫𝐨𝐚𝐭𝐢𝐚", "『🇭🇷』", "𝐂𝐑𝐎𝐀𝐓𝐈𝐀"),
    "386": ("𝐒𝐥𝐨𝐯𝐞𝐧𝐢𝐚", "『🇸🇮』", "𝐒𝐋𝐎𝐕𝐄𝐍𝐈𝐀"),
    "387": ("𝐁𝐨𝐬𝐧𝐢𝐚", "『🇧🇦』", "𝐁𝐎𝐒𝐍𝐈𝐀"),
    "389": ("𝐍. 𝐌𝐚𝐜𝐞𝐝𝐨𝐧𝐢𝐚", "『🇲🇰』", "𝐍𝐎𝐑𝐓𝐇 𝐌𝐀𝐂𝐄𝐃𝐎𝐍𝐈𝐀"),
    "420": ("𝐂𝐳𝐞𝐜𝐡 𝐑𝐞𝐩", "『🇨🇿』", "𝐂𝐙𝐄𝐂𝐇 𝐑𝐄𝐏𝐔𝐁𝐋𝐈𝐂"),
    "421": ("𝐒𝐥𝐨𝐯𝐚𝐤𝐢𝐚", "『🇸🇰』", "𝐒𝐋𝐎𝐕𝐀𝐊𝐈𝐀"),
    "423": ("𝐋𝐢𝐞𝐜𝐡𝐭𝐞𝐧𝐬𝐭𝐞𝐢𝐧", "『🇱🇮』", "𝐋𝐈𝐄𝐂𝐇𝐓𝐄𝐍𝐒𝐓𝐄𝐈𝐍"),
    "500": ("𝐅𝐚𝐥𝐤𝐥𝐚𝐧𝐝", "『🇫🇰』", "𝐅𝐀𝐋𝐊𝐋𝐀𝐍𝐃 𝐈𝐒𝐋𝐀𝐍𝐃𝐒"),
    "501": ("𝐁𝐞𝐥𝐢𝐳𝐞", "『🇧🇿』", "𝐁𝐄𝐋𝐈𝐙𝐄"),
    "502": ("𝐆𝐮𝐚𝐭𝐞𝐦𝐚𝐥𝐚", "『🇬🇹』", "𝐆𝐔𝐀𝐓𝐄𝐌𝐀𝐋𝐀"),
    "503": ("𝐄𝐥 𝐒𝐚𝐥𝐯𝐚𝐝𝐨𝐫", "『🇸🇻』", "𝐄𝐋 𝐒𝐀𝐋𝐕𝐀𝐃𝐎𝐑"),
    "504": ("𝐇𝐨𝐧𝐝𝐮𝐫𝐚𝐬", "『🇭🇳』", "𝐇𝐎𝐍𝐃𝐔𝐑𝐀𝐒"),
    "505": ("𝐍𝐢𝐜𝐚𝐫𝐚𝐠𝐮𝐚", "『🇳🇮』", "𝐍𝐈𝐂𝐀𝐑𝐀𝐆𝐔𝐀"),
    "506": ("𝐂𝐨𝐬𝐭𝐚 𝐑𝐢𝐜𝐚", "『🇨🇷』", "𝐂𝐎𝐒𝐓𝐀 𝐑𝐈𝐂𝐀"),
    "507": ("𝐏𝐚𝐧𝐚𝐦𝐚", "『🇵🇦』", "𝐏𝐀𝐍𝐀𝐌𝐀"),
    "509": ("𝐇𝐚𝐢𝐭𝐢", "『🇭🇹』", "𝐇𝐀𝐈𝐓𝐈"),
    "591": ("𝐁𝐨𝐥𝐢𝐯𝐢𝐚", "『🇧🇴』", "𝐁𝐎𝐋𝐈𝐕𝐈𝐀"),
    "592": ("𝐆𝐮𝐲𝐚𝐧𝐚", "『🇬🇾』", "𝐆𝐔𝐘𝐀𝐍𝐀"),
    "593": ("𝐄𝐜𝐮𝐚𝐝𝐨𝐫", "『🇪🇨』", "𝐄𝐂𝐔𝐀𝐃𝐎𝐑"),
    "595": ("𝐏𝐚𝐫𝐚𝐠𝐮𝐚𝐲", "『🇵🇾』", "𝐏𝐀𝐑𝐀𝐆𝐔𝐀𝐘"),
    "597": ("𝐒𝐮𝐫𝐢𝐧𝐚𝐦𝐞", "『🇸🇷』", "𝐒𝐔𝐑𝐈𝐍𝐀𝐌𝐄"),
    "598": ("𝐔𝐫𝐮𝐠𝐮𝐚𝐲", "『🇺🇾』", "𝐔𝐑𝐔𝐆𝐔𝐀𝐘"),
    "670": ("𝐓𝐢𝐦𝐨𝐫-𝐋𝐞𝐬𝐭𝐞", "『🇹🇱』", "𝐓𝐈𝐌𝐎𝐑-𝐋𝐄𝐒𝐓𝐄"),
    "673": ("𝐁𝐫𝐮𝐧𝐞𝐢", "『🇧🇳』", "𝐁𝐑𝐔𝐍𝐄𝐈"),
    "674": ("𝐍𝐚𝐮𝐫𝐮", "『🇳🇷』", "𝐍𝐀𝐔𝐑𝐔"),
    "675": ("𝐏𝐍𝐆", "『🇵🇬』", "𝐏𝐀𝐏𝐔𝐀 𝐍𝐄𝐖 𝐆𝐔𝐈𝐍𝐄𝐀"),
    "676": ("𝐓𝐨𝐧𝐠𝐚", "『🇹🇴』", "𝐓𝐎𝐍𝐆𝐀"),
    "677": ("𝐒𝐨𝐥𝐨𝐦𝐨𝐧 𝐈𝐬", "『🇸🇧』", "𝐒𝐎𝐋𝐎𝐌𝐎𝐍 𝐈𝐒𝐋𝐀𝐍𝐃𝐒"),
    "678": ("𝐕𝐚𝐧𝐮𝐚𝐭𝐮", "『🇻🇺』", "𝐕𝐀𝐍𝐔𝐀𝐓𝐔"),
    "679": ("𝐅𝐢𝐣𝐢", "『🇫🇯』", "𝐅𝐈𝐉𝐈"),
    "680": ("𝐏𝐚𝐥𝐚𝐮", "『🇵🇼』", "𝐏𝐀𝐋𝐀𝐔"),
    "685": ("𝐒𝐚𝐦𝐨𝐚", "『🇼🇸』", "𝐒𝐀𝐌𝐎𝐀"),
    "686": ("𝐊𝐢𝐫𝐢𝐛𝐚𝐭𝐢", "『🇰🇮』", "𝐊𝐈𝐑𝐈𝐁𝐀𝐓𝐈"),
    "687": ("𝐍𝐞𝐰 𝐂𝐚𝐥𝐞𝐝𝐨𝐧𝐢𝐚", "『🇳🇨』", "𝐍𝐄𝐖 𝐂𝐀𝐋𝐄𝐃𝐎𝐍𝐈𝐀"),
    "688": ("𝐓𝐮𝐯𝐚𝐥𝐮", "『🇹🇻』", "𝐓𝐔𝐕𝐀𝐋𝐔"),
    "689": ("𝐅𝐫 𝐏𝐨𝐥𝐲𝐧𝐞𝐬𝐢𝐚", "『🇵🇫』", "𝐅𝐑𝐄𝐍𝐂𝐇 𝐏𝐎𝐋𝐘𝐍𝐄𝐒𝐈𝐀"),
    "691": ("𝐌𝐢𝐜𝐫𝐨𝐧𝐞𝐬𝐢𝐚", "『🇫🇲』", "𝐌𝐈𝐂𝐑𝐎𝐍𝐄𝐒𝐈𝐀"),
    "692": ("𝐌𝐚𝐫𝐬𝐡𝐚𝐥𝐥 𝐈𝐬", "『🇲🇭』", "𝐌𝐀𝐑𝐒𝐇𝐀𝐋𝐋 𝐈𝐒𝐋𝐀𝐍𝐃𝐒"),
    "850": ("𝐍𝐨𝐫𝐭𝐡 𝐊𝐨𝐫𝐞𝐚", "『🇰🇵』", "𝐍𝐎𝐑𝐓𝐇 𝐊𝐎𝐑𝐄𝐀"),
    "852": ("𝐇𝐨𝐧𝐠 𝐊𝐨𝐧𝐠", "『🇭🇰』", "𝐇𝐎𝐍𝐆 𝐊𝐎𝐍𝐆"),
    "853": ("𝐌𝐚𝐜𝐚𝐮", "『🇲🇴』", "𝐌𝐀𝐂𝐀𝐔"),
    "855": ("𝐂𝐚𝐦𝐛𝐨𝐝𝐢𝐚", "『🇰🇭』", "𝐂𝐀𝐌𝐁𝐎𝐃𝐈𝐀"),
    "856": ("𝐋𝐚𝐨𝐬", "『🇱🇦』", "𝐋𝐀𝐎𝐒"),
    "880": ("𝗯𝗮𝗻𝗴𝗹𝗮𝗱𝗲𝘀𝗵", "『🇧🇩』", "𝐁𝐀𝐍𝐆𝐋𝐀𝐃𝐄𝐒𝐇"), 
    "960": ("𝐌𝐚𝐥𝐝𝐢𝐯𝐞𝐬", "『🇲🇻』", "𝐌𝐀𝐋𝐃𝐈𝐕𝐄𝐒"),
    "961": ("𝐋𝐞𝐛𝐚𝐧𝐨𝐧", "『🇱🇧』", "𝐋𝐄𝐁𝐀𝐍𝐎𝐍"),
    "962": ("𝐉𝐨𝐫𝐝𝐚𝐧", "『🇯🇴』", "𝐉𝐎𝐑𝐃𝐀𝐍"),
    "963": ("𝐒𝐲𝐫𝐢𝐚", "『🇸🇾』", "𝐒𝐘𝐑𝐈𝐀"),
    "964": ("𝐈𝐫𝐚𝐪", "『🇮🇶』", "𝐈𝐑𝐀𝐐"),
    "965": ("𝐊𝐮𝐰𝐚𝐢𝐭", "『🇰🇼』", "𝐊𝐔𝐖𝐀𝐈𝐓"),
    "966": ("𝐒𝐚𝐮𝐝𝐢 𝐀𝐫𝐚𝐛𝐢𝐚", "『🇸🇦』", "𝐒𝐀𝐔𝐃𝐈 𝐀𝐑𝐀𝐁𝐈𝐀"),
    "967": ("𝐘𝐞𝐦𝐞𝐧", "『🇾🇪』", "𝐘𝐄𝐌𝐄𝐍"),
    "968": ("𝐎𝐦𝐚𝐧", "『🇴🇲』", "𝐎𝐌𝐀𝐍"),
    "970": ("𝐏𝐚𝐥𝐞𝐬𝐭𝐢𝐧𝐞", "『🇵🇸』", "𝐏𝐀𝐋𝐄𝐒𝐓𝐈𝐍𝐄"),
    "971": ("𝐔𝐀𝐄", "『🇦🇪』", "𝐔𝐀𝐄"),
    "972": ("𝐀𝐙𝐑𝐀𝐁𝐈𝐋", "『 🤮🐌 』", "𝐀𝐙𝐑𝐀𝐁𝐈𝐋"),
    "973": ("𝐁𝐚𝐡𝐫𝐚𝐢𝐧", " 🇧🇭』", "𝐁𝐀𝐇𝐑𝐀𝐈𝐍"),
    "974": ("𝐐𝐚𝐭𝐚𝐫", "『🇶🇦』", "𝐐𝐀𝐓𝐀𝐑"),
    "975": ("𝐁𝐡𝐮𝐭𝐚𝐧", "『🇧🇹』", "𝐁𝐇𝐔𝐓𝐀𝐍"),
    "976": ("𝐌𝐨𝐧𝐠𝐨𝐥𝐢𝐚", "『🇲🇳』", "𝐌𝐎𝐍𝐆𝐎𝐋𝐈𝐀"),
    "977": ("𝐍𝐞𝐩𝐚𝐥", "『🇳🇵』", "𝐍𝐄𝐏𝐀𝐋"),
    "992": ("𝐓𝐚𝐣𝐢𝐤𝐢𝐬𝐭𝐚𝐧", "『🇹🇯』", "𝐓𝐀𝐉𝐈𝐊𝐈𝐒𝐓𝐀𝐍"),
    "993": ("𝐓𝐮𝐫𝐤𝐦𝐞𝐧𝐢𝐬𝐭𝐚𝐧", "『🇹🇲』", "𝐓𝐔𝐑𝐊𝐌𝐄𝐍𝐈𝐒𝐓𝐀𝐍"),
    "994": ("𝐀𝐳𝐞𝐫𝐛𝐚𝐢𝐣𝐚𝐧", "『🇦🇿』", "𝐀𝐙𝐄𝐑𝐁𝐀𝐈𝐉𝐀𝐍"),
    "995": ("𝐆𝐞𝐨𝐫𝐠𝐢𝐚", "『🇬🇪』", "𝐆𝐄𝐎𝐑𝐆𝐈𝐀"),
    "996": ("𝐊𝐲𝐫𝐠𝐲𝐳𝐬𝐭𝐚𝐧", "『🇰🇬』", "𝐊𝐘𝐑𝐆𝐘𝐙𝐒𝐓𝐀𝐍"),
    "998": ("𝐔𝐳𝐛𝐞𝐤𝐢𝐬𝐭𝐚𝐧", "『🇺🇿』", "𝐔𝐙𝐁𝐄𝐊𝐈𝐒𝐓𝐀𝐍"),
}
# ======================
# 📁 إنشاء المجلدات اللازمة
# ======================
os.makedirs("sessions", exist_ok=True)
os.makedirs("sent_messages", exist_ok=True)

# ======================
# 🖥️ إعداد حسابات iVasms المتعددة
# ======================
IVASMS_ACCOUNTS = [
    {
        "id": 1,
        "name": "iVasms-1",
        "type": "ivasms",
        "login_url": "https://www.ivasms.com/login",
        "base_url": "https://ivas.tempnum.qzz.io",
        "sms_api_endpoint": "https://ivas.tempnum.qzz.io/portal/sms/received/getsms",
        "username": "ddama9026@gmail.com",  # غير حسب حسابك الأول
        "password": "LkPePo77@",  # غير حسب حسابك الأول
        "session": requests.Session(),
        "is_logged_in": False,
        "cookies": None,
        "csrf_token": None,
        "last_check": None,
        "sent_messages_file": f"sent_messages/ivasms_1.json",
        "sent_messages": set(),
        "consecutive_errors": 0
    },
    {
        "id": 2,
        "name": "iVasms-2",
        "type": "ivasms",
        "login_url": "https://www.ivasms.com/login",
        "base_url": "https://ivas.tempnum.qzz.io",
        "sms_api_endpoint": "https://ivas.tempnum.qzz.io/portal/sms/received/getsms",
        "username": "ziadmohmmed2011@gmail.com",  # ضع حسابك الثاني
        "password": "ziad2016",  # ضع كلمة المرور الثانية
        "session": requests.Session(),
        "is_logged_in": False,
        "cookies": None,
        "csrf_token": None,
        "last_check": None,
        "sent_messages_file": f"sent_messages/ivasms_2.json",
        "sent_messages": set(),
        "consecutive_errors": 0
    },
    {
        "id": 3,
        "name": "iVasms-3",
        "type": "ivasms",
        "login_url": "https://www.ivasms.com/login",
        "base_url": "https://ivas.tempnum.qzz.io",
        "sms_api_endpoint": "https://ivas.tempnum.qzz.io/portal/sms/received/getsms",
        "username": "ddama9026@gmail.com",  # ضع حسابك الثالث
        "password": "LkPePo77@",  # ضع كلمة المرور الثالثة
        "session": requests.Session(),
        "is_logged_in": False,
        "cookies": None,
        "csrf_token": None,
        "last_check": None,
        "sent_messages_file": f"sent_messages/ivasms_3.json",
        "sent_messages": set(),
        "consecutive_errors": 0
    }
]

# ======================
# 🖥️ إعداد حسابات TimeSMS المتعددة
# ======================
TIMESMS_ACCOUNTS = [
    {
        "id": 4,
        "name": "TimeSMS-1",
        "type": "timesms",
        "base_url": "http://www.timesms.org",
        "login_page_url": "/login",
        "login_post_url": "/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "username": "HAMOELNOS7",
        "password": "6634032038",
        "session": requests.Session(),
        "is_logged_in": False,
        "cookies": None,
        "last_check": None,
        "sent_messages_file": f"sent_messages/timesms_1.json",
        "sent_messages": set(),
        "idx_date": 0,
        "idx_number": 2,
        "idx_sms": 5,
        "consecutive_errors": 0
    },
    {
        "id": 5,
        "name": "TimeSMS-2",
        "type": "timesms",
        "base_url": "http://www.timesms.org",
        "login_page_url": "/login",
        "login_post_url": "/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "username": "BODYELYOUTUBER",  # ضع حسابك الثاني
        "password": "01556185980m",  # ضع كلمة المرور الثانية
        "session": requests.Session(),
        "is_logged_in": False,
        "cookies": None,
        "last_check": None,
        "sent_messages_file": f"sent_messages/timesms_2.json",
        "sent_messages": set(),
        "idx_date": 0,
        "idx_number": 2,
        "idx_sms": 5,
        "consecutive_errors": 0
    },
    {
        "id": 6,
        "name": "TimeSMS-3",
        "type": "timesms",
        "base_url": "http://www.timesms.org",
        "login_page_url": "/login",
        "login_post_url": "/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "username": "BODYELYOUTUBER",  # ضع حسابك الثالث
        "password": "01556185980m",  # ضع كلمة المرور الثالثة
        "session": requests.Session(),
        "is_logged_in": False,
        "cookies": None,
        "last_check": None,
        "sent_messages_file": f"sent_messages/timesms_3.json",
        "sent_messages": set(),
        "idx_date": 0,
        "idx_number": 2,
        "idx_sms": 5,
        "consecutive_errors": 0
    }
]

# دمج جميع الحسابات
ALL_ACCOUNTS = IVASMS_ACCOUNTS + TIMESMS_ACCOUNTS

# ======================
# 🧰 دوال إدارة قاعدة البيانات (محدثة مع جدول المشرفين)
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )
    ''')
    
    # جدول الكومبوهات العامة
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            combo_index INTEGER DEFAULT 1,
            numbers TEXT,
            UNIQUE(country_code, combo_index)
        )
    ''')
    
    # جدول سجل OTP
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER,
            account_name TEXT
        )
    ''')
    
    # جدول إعدادات اللوحات
    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            username TEXT,
            password TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # جدول الإعدادات العامة
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # جدول الكومبوهات الخاصة
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')
    
    # جدول قنوات الاشتراك الإجباري
    c.execute('''
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        )
    ''')
    
    # جدول المشرفين
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول حالة الحسابات
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts_status (
            account_id INTEGER PRIMARY KEY,
            account_name TEXT,
            last_check TIMESTAMP,
            total_messages INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # إدراج المشرفين الافتراضيين
    default_admins = [7008351727]
    for uid in default_admins:
        c.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (uid, 0))
    
    conn.commit()
    conn.close()

# باقي دوال قاعدة البيانات (نفسها مع إضافة account_name في log_otp)
def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

# باقي دوال قاعدة البيانات (نفس الكود السابق)
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing_data = get_user(user_id)
    if existing_data:
        if country_code is None:
            country_code = existing_data[4]
        if assigned_number is None:
            assigned_number = existing_data[5]
        if private_combo_country is None:
            private_combo_country = existing_data[7]
    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (user_id, username, first_name, last_name, country_code, assigned_number, user_id, private_combo_country))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def is_maintenance_mode():
    return not BOT_ACTIVE

def set_maintenance_mode(status):
    global BOT_ACTIVE
    BOT_ACTIVE = not status

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo(country_code, combo_index=1, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    c.execute("SELECT numbers FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("SELECT MAX(combo_index) FROM combos WHERE country_code=?", (country_code,))
        max_index = c.fetchone()[0]
        next_index = 1 if max_index is None else max_index + 1
        c.execute("INSERT INTO combos (country_code, combo_index, numbers) VALUES (?, ?, ?)",
                  (country_code, next_index, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(country_code, combo_index=None, user_id=None):
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    c = conn.cursor()
    try:
        if user_id:
            c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        elif combo_index:
            c.execute("DELETE FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
        else:
            c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ خطأ SQLite في delete_combo: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_all_combos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code, combo_index FROM combos ORDER BY country_code, combo_index")
    combos = c.fetchall()
    conn.close()
    return combos

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def release_number(old_number):
    if not old_number:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs ORDER BY timestamp DESC LIMIT 1000")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_force_sub_channels(enabled_only=True):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id = ?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_available_numbers(country_code, combo_index=1, user_id=None):
    all_numbers = get_combo(country_code, combo_index, user_id)
    if not all_numbers:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_numbers = set(row[0] for row in c.fetchall())
    conn.close()
    available = [num for num in all_numbers if num not in used_numbers]
    return available

# ======================
# 👥 دوال إدارة المشرفين
# ======================
def add_admin(user_id, added_by=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO admins (user_id, added_by) VALUES (?, ?)", (user_id, added_by))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_all_admins():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins ORDER BY added_at")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def is_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row is not None

# تهيئة قاعدة البيانات
init_db()

# ======================
# 🧰 دوال مساعدة عامة
# ======================
def safe_html(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text

def clean_html(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text

def clean_number(number):
    if not number:
        return ""
    number = re.sub(r'\D', '', str(number))
    return number

def get_country_info(number):
    number = number.strip().replace("+", "").replace(" ", "").replace("-", "")
    for code, (name, flag, short) in COUNTRY_CODES.items():
        if number.startswith(code):
            return name, flag, short
    return "Unknown", "🌍", "UN"

def mask_number(number):
    number = number.strip()
    if len(number) > 8:
        return number[:4] + "⁦⁦••••" + number[-3:]
    return number

def extract_otp(message):
    patterns = [
        r'(?:code|رمز|كود|verification|otp|pin)[:\s]+[‎]?(\d{3,8}(?:[- ]\d{3,4})?)',
        r'(\d{3})[- ](\d{3,4})',
        r'\b(\d{4,8})\b',
        r'[‎](\d{3,8})',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                return ''.join(match.groups())
            return match.group(1).replace(' ', '').replace('-', '')
    all_numbers = re.findall(r'\d{4,8}', message)
    if all_numbers:
        return all_numbers[0]
    return "N/A"

def detect_service(message):
    message_lower = message.lower()
    services = {
        "#WP": ["whatsapp", "واتساب", "واتس"],
        "#FB": ["facebook", "فيسبوك", "fb"],
        "#IG": ["instagram", "انستقرام", "انستا"],
        "#TG": ["telegram", "تيليجرام", "تلي"],
        "#TW": ["twitter", "تويتر", "x"],
        "#GG": ["google", "gmail", "جوجل", "جميل"],
        "#DC": ["discord", "ديسكورد"],
        "#LN": ["line", "لاين"],
        "#VB": ["viber", "فايبر"],
        "#SK": ["skype", "سكايب"],
        "#SC": ["snapchat", "سناب"],
        "#TT": ["tiktok", "تيك توك", "تيك"],
        "#AMZ": ["amazon", "امازون"],
        "#APL": ["apple", "ابل", "icloud"],
        "#MS": ["microsoft", "مايكروسوفت"],
        "#IN": ["linkedin", "لينكد"],
        "#UB": ["uber", "اوبر"],
        "#AB": ["airbnb", "ايربنب"],
        "#NF": ["netflix", "نتفلكس"],
        "#SP": ["spotify", "سبوتيفاي"],
        "#YT": ["youtube", "يوتيوب"],
        "#GH": ["github", "جيت هاب"],
        "#PT": ["pinterest", "بنتريست"],
        "#PP": ["paypal", "باي بال"],
        "#BK": ["booking", "بوكينج"],
        "#TL": ["tala", "تالا"],
        "#OLX": ["olx", "اوليكس"],
        "#STC": ["stcpay", "stc"],
    }
    for service_code, keywords in services.items():
        for keyword in keywords:
            if keyword in message_lower:
                return service_code
    if "code" in message_lower or "verification" in message_lower:
        if "telegram" in message_lower:
            return "#TG"
        if "whatsapp" in message_lower:
            return "#WP"
        if "facebook" in message_lower:
            return "#FB"
        if "instagram" in message_lower:
            return "#IG"
        if "google" in message_lower or "gmail" in message_lower:
            return "#GG"
        if "twitter" in message_lower or "x.com" in message_lower:
            return "#TW"
    return "Unknown"

def format_message(date_str, number, sms):
    country_name, country_flag, country_code = get_country_info(number)
    masked_num = mask_number(number)
    otp_code = extract_otp(sms)
    service = detect_service(sms)
    combo_index = 1 # قيمة افتراضية للكومبو في التنسيق

    # التنسيق الجديد بالملي مع كود OTP قابل للنسخ (داخل البرواز مع مسافات أمان للنسخ)
    message = (
        f"╭───────────────╮\n"
        f"│  ▂ ▄ ▅ ▆ 𝐎𝐓𝐏 ▆ ▅ ▄ ▂  │\n"
        f"│───────────────│\n"
        f"│◈𝐂𝐎𝐔𝐍𝐓𝐑𝐘: {country_name}\n"
        f"│◈𝐒𝐂𝐈𝐄𝐍𝐂𝐄:   {country_flag}\n"
        f"│◈𝐒𝐄𝐑𝐕𝐈𝐂𝐄: {service}\n"
        f"│◈𝐍𝐔𝐌𝐁𝐄𝐑: {masked_num}\n"
        f"│◈𝐂𝐎𝐌𝐁𝐎: {combo_index}\n"
        f"╰───────────────\n"
        f"│🎯 𝐑𝐄𝐂𝐈𝐕𝐄 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 ✅\n"
        f"│◈🔐𝐂𝐎𝐃𝐄: <code>{otp_code}</code>\n"
        f"╰───────────────╯"
     )
    return message

def delete_message_after_delay(chat_id, message_id, delay=150):
    time.sleep(delay)
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": message_id}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ فشل حذف الرسالة: {e}")

def send_to_telegram_group(text, otp_code):
    success_count = 0
    try:
        keyboard = {
            "inline_keyboard": [
                # الزر الأول: نسخ الكود (أزرق - primary)
                [{"text": f"🔑 {otp_code}", "copy_text": {"text": str(otp_code)}, "style": "primary"}],
                
                # الصف الثاني: زر القناة وزر لوحة البوت (أخضر - success)
                [
                    {"text": "💬𝐎𝐓𝐏 𝐆𝐑𝐎𝐔𝐏", "url": "https://t.me/otp3llosh2", "style": "success"},
                    {"text": "🤖𝗕𝗢𝗧", "url": "https://t.me/Y_I_l_l56BOT", "style": "success"}
                ],
                
                # الصف الثالث: زر المطور (أحمر - danger)
                [
                    {"text": "👤𝑴:𝑩𝑶𝑻", "url": "https://t.me/Y_I_l_l56BOT", "style": "danger"},
                    {"text": "💬𝖣𝖤𝖵", "url": "https://t.me/Y_I_l_l", "style": "danger"}
                ]
            ]
        }
    except Exception as e:
        print(f"❌ خطأ في إعداد الأزرار: {e}")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }
            resp = requests.post(url, data=payload, timeout=10)
            if resp.status_code == 200:
                print(f"[+] تم إرسال الرسالة إلى: {chat_id}")
                success_count += 1
                msg_id = resp.json()["result"]["message_id"]
                threading.Thread(target=delete_message_after_delay, args=(chat_id, msg_id, 150), daemon=True).start()
            else:
                print(f"[!] فشل إرسال إلى {chat_id}: {resp.status_code}")
        except Exception as e:
            print(f"[!] خطأ في الإرسال لـ {chat_id}: {e}")
    return success_count > 0

def send_otp_to_user_and_group(date_str, number, sms, account_name):
    otp_code = extract_otp(sms)
    country_name, country_flag, country_code = get_country_info(number)
    service = detect_service(sms)
    user_id = get_user_by_number(number)
    log_otp(number, otp_code, sms, user_id)
    
    if user_id:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("𝑶𝑾𝑵𝑬𝑹⚙️", url="https://t.me/Y_I_l_l"),
                types.InlineKeyboardButton("💬𝐎𝐓𝐏 𝐆𝐑𝐎𝐔𝐏", url="https://t.me/otp3llosh2")
            )
            bot.send_message(
                user_id,
                f"""✨ <b><u>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐃𝐀𝐑𝐊 𝐍𝐔𝐌𝐁𝐄𝐑𝐒</u></b>\n🌍 <b>Country:</b> {safe_html(country_name)} {country_flag}\n⚙ <b>Service:</b> {safe_html(service)}\n☎ <b>Number:</b> {safe_html(number)}\n🕒 <b>Time:</b> {safe_html(date_str)}\n📡 <b>Account:</b> {safe_html(account_name)}\n\n🔐 <b>Code:</b> {safe_html(otp_code)}\n\n<b>كود {safe_html(service)} {safe_html(otp_code[:3])}-{safe_html(otp_code[3:])} ؟</b>""",
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[!] فشل إرسال OTP للمستخدم {user_id}: {e}")
    
    text = format_message(date_str, number, sms)
    send_to_telegram_group(text, otp_code)

# ======================
# 📡 دوال خاصة بحسابات iVasms
# ======================
def login_to_ivasms(account):
    try:
        login_url = account["login_url"]
        base_url = account["base_url"]
        username = account["username"]
        password = account["password"]
        session = account["session"]

        # حقن الكوكيز مباشرة لحساب iVasms الأول
        if username == "ddama9026@gmail.com":
            IVASMS_COOKIES = {
                'ivas_sms_session': 'eyJpdiI6InRhMGtBVVpCKzNwMEx5cW1EZzhlV0E9PSIsInZhbHVlIjoiK0RRby93NnlSOTRrZ3FYYSsrZDZLakNkQXNWS3NrakM4ZThBWUJCenFreHlVT2Uwd2RaODdFVVJDMDVVSVZVSGJ6OW1BOVplNVVzNVduSEgxajRmTHM5MjJmQUVhNjJidEl0VjZKaHFrQXB6b2NSV1hrWlpaMXU5QnI2R0psNEUiLCJtYWMiOiIzYjBhYzYzMWI0ZjdiMWRkMDAxMDI3MTVkY2MxNWZjNjg4NmI0ZDY0NTI0YWI4YzA2MTBkNzMyNzkxYTgxZTM1IiwidGFnIjoiIn0%3D',
                'XSRF-TOKEN': 'eyJpdiI6Iml1bGhKaVhRUnU4QUtwMXkxR0NLeUE5PSIsInZhbHVlIjoiMFhJQXoyYmdnQjI4azFGU1FucmxwV2YvNWpsREdtWktLQmhweURmb2QyR2h2WWtSa3RueGFGTzRyYnBYSXMycnV2b21Xam5WcjI1OEFiSFloSFdHVldzSm5HOUdWNUo3a2t5Q2tnZGp1QVRLYm1XUjN2d1pFWkpDc1o4L3lScnUiLCJtYWMiOiJmZGM4ZTAyYWM2NzBiYjk4ODRjZTUwY2MyMzczYzdkNjEwYWQ4NmFkZWEzY2ZlNDYwMTdjMzhkMjJkMjc5ZGE3IiwidGFnIjoiIn0%3D',
            }
            for name, value in IVASMS_COOKIES.items():
                session.cookies.set(name, value, domain='www.ivasms.com')
            
            print(f"[{account['name']}] محاولة تسجيل الدخول عبر Cookies...")
            test = session.get("https://www.ivasms.com/portal/sms/received", timeout=30)
            if "login" not in test.url.lower():
                print(f"[{account['name']}] ✅ تسجيل الدخول ناجح عبر Cookies")
                soup = BeautifulSoup(test.text, 'html.parser')
                csrf_meta = soup.find('meta', {'name': 'csrf-token'})
                if csrf_meta:
                    account['csrf_token'] = csrf_meta.get('content')
                account['is_logged_in'] = True
                return True
            print(f"[{account['name']}] ⚠️ الكوكيز منتهية، محاولة بالإيميل...")

        print(f"[{account['name']}] محاولة تسجيل الدخول...")
        login_page_resp = session.get(login_url, timeout=30)
        login_page_resp.raise_for_status()
        
        soup = BeautifulSoup(login_page_resp.text, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        csrf_token = token_input['value'] if token_input else None
        
        login_data = {'email': username, 'password': password}
        if csrf_token:
            login_data['_token'] = csrf_token
        
        login_resp = session.post(login_url, data=login_data, timeout=30)
        
        if "login" not in login_resp.url.lower():
            print(f"[{account['name']}] ✅ تسجيل الدخول ناجح")
            dashboard_soup = BeautifulSoup(login_resp.text, 'html.parser')
            csrf_meta = dashboard_soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                account['csrf_token'] = csrf_meta.get('content')
            account['is_logged_in'] = True
            account['cookies'] = session.cookies.get_dict()
            return True
        else:
            print(f"[{account['name']}] ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{account['name']}] ❌ خطأ في تسجيل الدخول: {e}")
        return False

def fetch_ivasms_messages(account):
    if not account.get('is_logged_in', False):
        if not login_to_ivasms(account):
            return []
    try:
        session = account['session']
        base_url = account['base_url']
        sms_api_url = account['sms_api_endpoint']
        csrf_token = account.get('csrf_token')
        if not csrf_token:
            print(f"[{account['name']}] ⚠️ CSRF token غير متوفر")
            return []
        
        headers = {'Referer': f"{base_url}/portal/sms/received", 'X-Requested-With': 'XMLHttpRequest'}
        today = datetime.utcnow()
        start_date = (today - timedelta(days=1)).strftime('%m/%d/%Y')
        end_date = today.strftime('%m/%d/%Y')
        
        summary_payload = {'from': start_date, 'to': end_date, '_token': csrf_token}
        summary_resp = session.post(sms_api_url, headers=headers, data=summary_payload, timeout=30)
        summary_resp.raise_for_status()
        
        summary_soup = BeautifulSoup(summary_resp.text, 'html.parser')
        country_groups = summary_soup.find_all('div', {'class': 'pointer'})
        if not country_groups:
            return []
        
        group_ids = []
        for group in country_groups:
            onclick = group.get('onclick', '')
            match = re.search(r"getDetials\('(.+?)'\)", onclick)
            if match:
                group_ids.append(match.group(1))
        
        all_messages = []
        numbers_url = urljoin(base_url, "portal/sms/received/getsms/number")
        sms_details_url = urljoin(base_url, "portal/sms/received/getsms/number/sms")
        
        for group_id in group_ids:
            numbers_payload = {'start': start_date, 'end': end_date, 'range': group_id, '_token': csrf_token}
            numbers_resp = session.post(numbers_url, headers=headers, data=numbers_payload, timeout=30)
            numbers_soup = BeautifulSoup(numbers_resp.text, 'html.parser')
            number_divs = numbers_soup.select("div[onclick*='getDetialsNumber']")
            phone_numbers = [div.text.strip() for div in number_divs]
            
            for phone in phone_numbers:
                sms_payload = {'start': start_date, 'end': end_date, 'Number': phone, 'Range': group_id, '_token': csrf_token}
                sms_resp = session.post(sms_details_url, headers=headers, data=sms_payload, timeout=30)
                sms_soup = BeautifulSoup(sms_resp.text, 'html.parser')
                sms_cards = sms_soup.find_all('div', class_='card-body')
                for card in sms_cards:
                    sms_text_p = card.find('p', class_='mb-0')
                    if sms_text_p:
                        sms_text = sms_text_p.get_text(separator='\n').strip()
                        message_id = f"{account['id']}-{phone}-{sms_text[:50]}"
                        country_name = group_id.strip()
                        all_messages.append({
                            'id': message_id,
                            'number': phone,
                            'text': sms_text,
                            'country': country_name,
                            'timestamp': datetime.utcnow().isoformat()
                        })
        print(f"[{account['name']}] ✅ تم جلب {len(all_messages)} رسالة")
        return all_messages
    except Exception as e:
        print(f"[{account['name']}] ❌ خطأ في جلب الرسائل: {e}")
        traceback.print_exc()
        account['is_logged_in'] = False
        return []
        
# ======================
# 📡 دوال خاصة بحسابات TimeSMS
# ======================
def login_to_timesms(account):
    try:
        session = account['session']
        login_page_url = account['base_url'] + account['login_page_url']
        login_post_url = account['base_url'] + account['login_post_url']
        username = account['username']
        password = account['password']

        print(f"[{account['name']}] محاولة تسجيل الدخول...")
        resp = session.get(login_page_url, timeout=TIMEOUT, allow_redirects=True)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            match = re.search(r'(\d+)\s*\+\s*(\d+)', resp.text)
        if match:
            num1, num2 = int(match.group(1)), int(match.group(2))
            captcha = str(num1 + num2)
            print(f"[*] حل captcha: {num1} + {num2} = {captcha}")
        else:
            captcha = ""
            print("[!] لم يُعثر على captcha")
        
        payload = {"username": username, "password": password, "capt": captcha}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": login_page_url,
            "Origin": account['base_url'],
            "Accept": "text/html,application/xhtml+xml,*/*",
        }
        resp = session.post(login_post_url, data=payload, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 200 and ("logout" in resp.text.lower() or "agent" in resp.url.lower() or "dashboard" in resp.text.lower() or resp.url != login_page_url):
            print(f"[{account['name']}] ✅ تسجيل الدخول ناجح")
            account['is_logged_in'] = True
            account['cookies'] = session.cookies.get_dict()
            return True
        else:
            print(f"[{account['name']}] ❌ فشل تسجيل الدخول")
            account['is_logged_in'] = False
            return False
    except Exception as e:
        print(f"[{account['name']}] ❌ خطأ في تسجيل الدخول: {e}")
        account['is_logged_in'] = False
        return False

def fetch_timesms_messages(account, wide_range=True):
    if not account.get('is_logged_in', False):
        if not login_to_timesms(account):
            return []
    
    try:
        session = account['session']
        base_url = account['base_url']
        ajax_path = account['ajax_path']
        
        today = date.today()
        if wide_range:
            start_date = today - timedelta(days=3650)
            end_date = today + timedelta(days=1)
        else:
            start_date = today
            end_date = today + timedelta(days=1)
        
        fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
        ts = int(time.time() * 1000)
        
        params = (
            f"fdate1={quote_plus(fdate1)}"
            f"&fdate2={quote_plus(fdate2)}"
            f"&frange=&fclient=&fnum=&fcli="
            f"&fgdate=&fgmonth=&fgrange=&fgclient=&fgnumber=&fgcli="
            f"&fg=0"
            f"&sEcho=1"
            f"&iColumns=9"
            f"&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C"
            f"&iDisplayStart=0"
            f"&iDisplayLength=5000"
            f"&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3"
            f"&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8"
            f"&sSearch=&bRegex=false"
            f"&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1"
            f"&_={ts}"
        )
        url = base_url + ajax_path + "?" + params
        
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": base_url + "/agent/SMSCDRStats",
        }
        
        r = session.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        
        if r.url and "login" in r.url.lower():
            print(f"[{account['name']}] الجلسة انتهت - إعادة تسجيل الدخول...")
            account['is_logged_in'] = False
            return fetch_timesms_messages(account, wide_range)
        
        if r.status_code != 200:
            print(f"[{account['name']}] HTTP {r.status_code}")
            return []
        
        body = r.text.strip()
        if not body:
            return []
        
        cleaned = body
        for prefix in (")]}',\n", "while(1);", "for(;;);"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r'(\{"(?:aaData|data|rows)":.+\})\s*$', cleaned, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                except:
                    print(f"[{account['name']}] فشل تحليل JSON")
                    return []
            else:
                print(f"[{account['name']}] ليس JSON - أول 300 حرف:\n{body[:300]}")
                return []
        
        rows = []
        if isinstance(data, dict):
            for key in ("aaData", "data", "rows"):
                if key in data:
                    rows = data[key]
                    break
        elif isinstance(data, list):
            rows = data
        
        messages = []
        for row in rows:
            if isinstance(row, (list, tuple)):
                if len(row) > account['idx_date']:
                    date_str = clean_html(row[account['idx_date']])
                else:
                    date_str = ""
                if len(row) > account['idx_number']:
                    number = clean_number(row[account['idx_number']])
                else:
                    number = ""
                if len(row) > account['idx_sms']:
                    sms_text = clean_html(row[account['idx_sms']])
                else:
                    sms_text = ""
                if date_str and number and sms_text:
                    msg_id = f"{account['id']}-{number}-{sms_text[:50]}"
                    messages.append({
                        'id': msg_id,
                        'number': number,
                        'text': sms_text,
                        'timestamp': date_str
                    })
        print(f"[{account['name']}] ✅ تم جلب {len(messages)} رسالة")
        return messages
    except Exception as e:
        print(f"[{account['name']}] ❌ خطأ في جلب الرسائل: {e}")
        account['is_logged_in'] = False
        return []

# ======================
# 🔄 دالة معالجة حساب واحد (للاستخدام مع ThreadPoolExecutor)
# ======================
def process_account(account):
    try:
        print(f"[{account['name']}] ⏱️ جلب الرسائل...")
        
        if account['type'] == 'ivasms':
            messages = fetch_ivasms_messages(account)
        elif account['type'] == 'timesms':
            messages = fetch_timesms_messages(account, wide_range=True)
        else:
            return account['name'], 0
        
        new_messages = 0
        if messages:
            for msg in messages:
                msg_id = msg['id']
                if msg_id not in account['sent_messages']:
                    number = clean_number(msg['number'])
                    sms_text = msg['text']
                    date_str = msg['timestamp']
                    
                    send_otp_to_user_and_group(date_str, number, sms_text, account['name'])
                    
                    account['sent_messages'].add(msg_id)
                    new_messages += 1
            
            if new_messages > 0:
                print(f"[{account['name']}] ✅ تم إرسال {new_messages} رسالة جديدة")
                
                sent_file = account.get('sent_messages_file')
                if sent_file:
                    try:
                        with open(sent_file, 'w') as f:
                            json.dump(list(account['sent_messages'])[-1000:], f)
                    except Exception as e:
                        print(f"⚠️ خطأ في حفظ {sent_file}: {e}")
            
            account['consecutive_errors'] = 0
        else:
            print(f"[{account['name']}] [=] لا توجد رسائل جديدة")
        
        # تنظيف الذاكرة
        if len(account['sent_messages']) > 2000:
            account['sent_messages'] = set(list(account['sent_messages'])[-1000:])
        
        return account['name'], new_messages
    
    except Exception as e:
        account['consecutive_errors'] += 1
        print(f"[{account['name']}] ❌ خطأ ({account['consecutive_errors']}): {e}")
        if account['consecutive_errors'] >= 5:
            print(f"[{account['name']}] ⛔ إعادة تسجيل الدخول بعد 5 أخطاء")
            account['is_logged_in'] = False
            account['consecutive_errors'] = 0
        return account['name'], -1

# ======================
# 🔄 الحلقة الرئيسية (معالجة متوازية لجميع الحسابات)
# ======================
def main_loop():
    # تحميل الرسائل المرسلة سابقاً لكل حساب
    for account in ALL_ACCOUNTS:
        sent_file = account.get('sent_messages_file')
        if sent_file and os.path.exists(sent_file):
            try:
                with open(sent_file, 'r') as f:
                    account['sent_messages'] = set(json.load(f))
                print(f"📂 تم تحميل {len(account['sent_messages'])} رسالة سابقة لـ {account['name']}")
            except Exception as e:
                print(f"⚠️ خطأ في تحميل {sent_file}: {e}")
    
    print("=" * 60)
    print("🚀 بدء مراقبة جميع الحسابات بالتوازي")
    print(f"📊 عدد الحسابات الكلي: {len(ALL_ACCOUNTS)}")
    print(f"⚡ عدد العمال (workers): {MAX_WORKERS}")
    print("=" * 60)
    
    # تسجيل الدخول الأولي لجميع الحسابات
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for account in ALL_ACCOUNTS:
            if account['type'] == 'ivasms':
                futures.append(executor.submit(login_to_ivasms, account))
            elif account['type'] == 'timesms':
                futures.append(executor.submit(login_to_timesms, account))
        
        for future in as_completed(futures):
            try:
                future.result(timeout=60)
            except Exception as e:
                print(f"❌ خطأ في تسجيل الدخول الأولي: {e}")
    
    print("✅ تم الانتهاء من تسجيل الدخول الأولي")
    print("=" * 60)
    
    while True:
        start_time = time.time()
        
        # معالجة جميع الحسابات بالتوازي
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_account, account) for account in ALL_ACCOUNTS]
            
            total_new = 0
            for future in as_completed(futures):
                try:
                    account_name, new_count = future.result(timeout=60)
                    if new_count > 0:
                        total_new += new_count
                except Exception as e:
                    print(f"❌ خطأ في معالجة حساب: {e}")
        
        # حساب وقت الدورة
        cycle_time = time.time() - start_time
        print(f"🔄 انتهت دورة الجلب في {cycle_time:.2f} ثانية | إجمالي الرسائل الجديدة: {total_new}")
        
        # انتظار الوقت المتبقي إذا كانت الدورة أسرع من REFRESH_INTERVAL
        if cycle_time < REFRESH_INTERVAL:
            time.sleep(REFRESH_INTERVAL - cycle_time)

# ======================
# 🤖 بوت تيليجرام التفاعلي (نفس الكود السابق)
# ======================
bot = telebot.TeleBot(BOT_TOKEN)

# دوال الاشتراك الإجباري
def force_sub_check(user_id):
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True
    for _, url, _ in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"[!] خطأ في التحقق من القناة {url}: {e}")
            return False
    return True

def force_sub_markup():
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None
    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. فحص وضع الصيانة
    if is_maintenance_mode() and not is_admin(user_id):
        maintenance_caption = (
            "<b>❍<u>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝗕𝗢𝗧 𝐃𝐀𝐑𝐊 𝐍𝐔𝐌𝐁𝐄𝐑𝐒</u>❍</b>\n\n"
            "<b>⚠️ عذراً عزيزي المستخدم..</b>\n"
            "<b>البوت الآن في وضع الصيانة لتحديث الخدمات.</b>\n\n"
            "<b>⏳ يرجى المحاولة مرة أخرى لاحقاً.</b>\n"
            "<b>────────────────────</b>"
        )
        # استبدل الرابط أدناه برابط صورتك الخاصة أو file_id
        maintenance_photo = "https://i.ibb.co/2352v1FN/file-000000004f20720aaa70039fcd26faab-1.png" 
        try:
            bot.send_photo(chat_id, maintenance_photo, caption=maintenance_caption, parse_mode="HTML")
        except:
            bot.send_message(chat_id, maintenance_caption, parse_mode="HTML")
        return

    # 2. فحص الحظر
    if is_banned(user_id):
        bot.reply_to(message, "<b>🚫 عذراً، لقد تم حظرك من استخدام البوت.</b>", parse_mode="HTML")
        return

    # 3. فحص الاشتراك الإجباري
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(chat_id, "<b>🔒 يجب الاشتراك في القنوات لاستخدام البوت.</b>", parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, "<b>🔒 الاشتراك الإجباري مفعل لكن لم يتم تحديد قناة!</b>", parse_mode="HTML")
        return

    # 4. حفظ المستخدم الجديد
    if not get_user(user_id):
        save_user(
            user_id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )
        for admin in get_all_admins():
            try:
                caption = (
                    f"🆕 <b>مستخدم جديد دخل البوت:</b>\n"
                    f"<b>🆔:</b> <code>{user_id}</code>\n"
                    f"<b>👤:</b> @{safe_html(message.from_user.username or 'None')}\n"
                    f"<b>الاسم:</b> {safe_html(message.from_user.first_name or '')}"
                )
                bot.send_message(admin, caption, parse_mode="HTML")
            except:
                pass
    
    # 5. بناء قائمة الأزرار
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    user_data = get_user(user_id)
    private_combo = user_data[7] if user_data else None
    all_combos = get_all_combos()

    country_combos = {}
    for country_code, combo_index in all_combos:
        if country_code not in country_combos:
            country_combos[country_code] = []
        country_combos[country_code].append(combo_index)

    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        buttons.append(types.InlineKeyboardButton(f"{flag} {name} (Private)", callback_data=f"country_{private_combo}_1"))

    for country_code, indices in country_combos.items():
        if country_code in COUNTRY_CODES and country_code != private_combo:
            name, flag, _ = COUNTRY_CODES[country_code]
            for idx in indices:
                if len(indices) == 1:
                    btn_text = f"{flag} {name}"
                else:
                    btn_text = f"{flag} {name} ({idx})"
                buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"country_{country_code}_{idx}"))

    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])

    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))

    fancy_text = (
        "<b>❍<u>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 3llosh 𝐁𝐎𝐓</u>❍</b>\n\n"
        "<b> ☠️ <u>𝐅𝐚𝐬𝐭  • 𝐒𝐞𝐜𝐮𝐫𝐞  • 𝐨𝐧𝐥𝐢𝐧𝐞</u></b>\n\n"
        "<b>🎓 <u>𝐎𝐖𝐍𝐄𝐑</u>  • <a href='https://t.me/Y_I_l_l'>3llosh</a></b>\n\n"
        "<b>────────────────────</b>\n"
        "<b><u>𝐂𝐇𝐎𝐎𝐒𝐄 𝐓𝐇𝐄 𝐂𝐎𝐔𝐍𝐓𝐑𝐈𝐄𝐒 𝐘𝐎𝐔 𝐖𝐀𝐍𝐓 𝐅𝐑𝐎𝐌 𝐓𝐇𝐄 𝐁𝐔𝐓𝐓𝐎𝐍 𝐁𝐄𝐋𝐎𝐖</u>⬇️</b>"
    )
    bot.send_message(chat_id, fancy_text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق! يمكنك استخدام البوت الآن.", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        bot.send_message(chat_id, "<b>🔒 يجب الاشتراك في القناة لاستخدام البوت.</b>", parse_mode="HTML", reply_markup=markup)
        return

    parts = call.data.split("_")
    country_code = parts[1]
    combo_index = int(parts[2]) if len(parts) > 2 else 1
    
    available_numbers = get_available_numbers(country_code, combo_index, user_id)
    
    if not available_numbers:
        error_msg = "<b>❌ نعتذر، جميع الأرقام قيد الاستخدام حالياً لهذه الدولة.</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 العودة لاختيار دولة أخرى", callback_data="back_to_countries"))
        bot.edit_message_text(error_msg, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        return

    assigned = random.choice(available_numbers)
    old_user = get_user(user_id)
    if old_user and old_user[5]:
        release_number(old_user[5])
    
    assign_number_to_user(user_id, assigned)
    save_user(user_id, country_code=country_code, assigned_number=assigned)
    
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = (
        f"<b>◈𝐘𝐎𝐔𝐑 𝐍𝐔𝐌𝐁𝐄𝐑 :</b> <code>{assigned}</code>\n"
        f"<b>◈𝐂𝐎𝐔𝐍𝐓𝐑𝐘 :</b> {flag} {name}\n"
        f"<b>◈𝐂𝐎𝐌𝐁𝐎 :</b> {combo_index}\n"
        f"<b>◈𝐒𝐓𝐀𝐓𝐔𝐒 :</b>⏳𝐖𝐀𝐈𝐓𝐈𝐍𝐆 𝐅𝐎𝐑 𝐎𝐓𝐏....🔑"
    )

      # 5. بناء الأزرار المحدثة (كل زر تحت الثاني)
    markup = types.InlineKeyboardMarkup()
    
    # زر الجروب
    markup.add(types.InlineKeyboardButton("🔍𝐎𝐓𝐏 𝐆𝐑𝐎𝐔𝐏", url="https://t.me/otp3llosh2"))
    
    # أزرار التحكم - كل زر في صف منفصل
    markup.add(types.InlineKeyboardButton("🔄𝐂𝐇𝐀𝐍𝐆𝐄 𝐍𝐔𝐌𝐁𝐄𝐑", callback_data=f"change_num_{country_code}_{combo_index}"))
    markup.add(types.InlineKeyboardButton("🔙𝐁𝐀𝐂𝐊", callback_data="back_to_countries"))

    # 6. تحديث الرسالة (ذكي: تعديل أو حذف وإرسال)

    try:
        bot.edit_message_text(text=msg_text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
        bot.answer_callback_query(call.id, "✅ تم استلام الرقم بنجاح")
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        return
    if not force_sub_check(user_id):
        return
        
    parts = call.data.split("_")
    country_code = parts[2]
    combo_index = int(parts[3]) if len(parts) > 3 else 1
    
    available_numbers = get_available_numbers(country_code, combo_index, user_id)
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ نعتذر، جميع الأرقام قيد الاستخدام حالياً.", show_alert=True)
        return

    old_user = get_user(user_id)
    if old_user and old_user[5]:
        release_number(old_user[5])
        
    assigned = random.choice(available_numbers)
    assign_number_to_user(user_id, assigned)
    save_user(user_id, assigned_number=assigned)
    
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = (
        f"<b>◈𝐘𝐎𝐔𝐑 𝐍𝐔𝐌𝐁𝐄𝐑 :</b> <code>{assigned}</code>\n"
        f"<b>◈𝐂𝐎𝐔𝐍𝐓𝐑𝐘 :</b> {flag} {name}\n"
        f"<b>◈𝐂𝐎𝐌𝐁𝐎 :</b> {combo_index}\n"
        f"<b>◈𝐒𝐓𝐀𝐓𝐔𝐒 :</b>⏳𝐖𝐀𝐈𝐓𝐈𝐍𝐆 𝐅𝐎𝐑 𝐎𝐓𝐏....🔑"
    )

      # 5. بناء الأزرار المحدثة (كل زر تحت الثاني)
    markup = types.InlineKeyboardMarkup()
    
    # زر الجروب
    markup.add(types.InlineKeyboardButton("👁️𝐎𝐓𝐏 𝐆𝐑𝐎𝐔𝐏", url="https://t.me/otp3llosh2"))
    
    # أزرار التحكم - كل زر في صف منفصل
    markup.add(types.InlineKeyboardButton("🔄𝐂𝐇𝐀𝐍𝐆𝐄 𝐍𝐔𝐌𝐁𝐄𝐑", callback_data=f"change_num_{country_code}_{combo_index}"))
    markup.add(types.InlineKeyboardButton("🔙𝐁𝐀𝐂𝐊", callback_data="back_to_countries"))

    # 6. تحديث الرسالة (ذكي: تعديل أو حذف وإرسال)

    try:
        bot.edit_message_text(text=msg_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
        bot.answer_callback_query(call.id, "تـم تـغـيـر رقـم يـحـب💯")
    except Exception as e:
        print(f"Error in change_number: {e}")
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    user = get_user(call.from_user.id)
    private_combo = user[7] if user else None
    all_combos = get_all_combos()

    country_combos = {}
    for country_code, combo_index in all_combos:
        if country_code not in country_combos:
            country_combos[country_code] = []
        country_combos[country_code].append(combo_index)

    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        buttons.append(types.InlineKeyboardButton(f"{flag} {name} (Private)", callback_data=f"country_{private_combo}_1"))

    for country_code, indices in country_combos.items():
        if country_code in COUNTRY_CODES and country_code != private_combo:
            name, flag, _ = COUNTRY_CODES[country_code]
            for idx in indices:
                if len(indices) == 1:
                    btn_text = f"{flag} {name}"
                else:
                    btn_text = f"{flag} {name} ({idx})"
                buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"country_{country_code}_{idx}"))

    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])

    if is_admin(call.from_user.id):
        admin_btn = types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")
        markup.add(admin_btn)

    fancy_text = (
        "<b>❍<u>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 3llosh 𝐁𝐎𝐓</u>❍</b>\n\n"
        "<b>☠️ <u>𝐅𝐚𝐬𝐭  • 𝐒𝐞𝐜𝐮𝐫𝐞  • 𝐨𝐧𝐥𝐢𝐧𝐞</u></b>\n\n"
        "<b>🎓 <u>𝐎𝐖𝐍𝐄𝐑</u>  • <a href='https://t.me/Y_I_l_l'>3llosh</a></b>\n\n"
        "<b>────────────────────</b>\n"
        "<b><u>𝐂𝐇𝐎𝐎𝐒𝐄 𝐓𝐇𝐄 𝐂𝐎𝐔𝐍𝐓𝐑𝐈𝐄𝐒 𝐘𝐎𝐔 𝐖𝐀𝐍𝐓 𝐅𝐑𝐎𝐌 𝐓𝐇𝐄 𝐁𝐔𝐓𝐓𝐎𝐍 𝐁𝐄𝐋𝐎𝐖</u>⬇️</b>"
    )

    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=fancy_text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)
    except Exception as e:
        print(f"Error editing message: {e}")
        bot.answer_callback_query(call.id)

# ======================
# 🔐 لوحة التحكم الإدارية (محدثة)
# ======================
user_states = {}

def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    status_icon = "🟢" if not is_maintenance_mode() else "🔴"
    status_text = "الآن: يعمل بنجاح" if not is_maintenance_mode() else "الآن: قيد الصيانة"
    markup.add(types.InlineKeyboardButton(f"{status_icon} {status_text} {status_icon}", callback_data="toggle_maintenance"))
    
    # إدارة الكومبوهات
    markup.row(
        types.InlineKeyboardButton("📥 إضافة كومبو", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف كومبو", callback_data="admin_del_combo")
    )
    
    # الإحصائيات والتقارير
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report")
    )
    
    # الإذاعة
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user")
    )
    
    # إدارة المستخدمين
    markup.row(
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("👤 معلومات", callback_data="admin_user_info")
    )
    
    # إعدادات متقدمة
    markup.row(
        types.InlineKeyboardButton("🔗 إشتراك", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("📊 حالة الحسابات", callback_data="admin_accounts_status"),
        types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo")
    )
    
    # إدارة المشرفين
    markup.row(
        types.InlineKeyboardButton("👥 إدارة المشرفين", callback_data="admin_manage_admins")
    )
    
    markup.add(types.InlineKeyboardButton("🔙 مغادرة لوحة التحكم", callback_data="back_to_countries"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ عذراً، هذا القسم للمطورين فقط.", show_alert=True)
        return
    admin_text = (
        "<b>❍<u>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝗕𝗢𝗧 𝐃𝐀𝐑𝐊 𝐍𝐔𝐌𝐁𝐄𝐑𝐒</u>❍</b>\n\n"
        "<b>👋 مرحباً بك يا مطور في لوحة التحكم.</b>\n\n"
        "<b>⚙️ يمكنك التحكم في كامل وظائف البوت من هنا.</b>\n"
        "<b>⚠️ تنبيه: أي تغيير في الإعدادات يؤثر على المستخدمين فوراً.</b>\n\n"
        "<b>────────────────────</b>\n"
        "<b>إحصائيات سريعة:</b>\n"
        "<b>• حالة السيرفر: <u>Online</u> ✅</b>\n"
        f"<b>• الوقت الحالي: <u>{datetime.now().strftime('%H:%M')}</u></b>\n"
        "<b>────────────────────</b>"
    )
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=admin_text, parse_mode="HTML", reply_markup=admin_main_menu(), disable_web_page_preview=True)
    except Exception as e:
        print(f"Admin Panel Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def handle_maintenance_toggle(call):
    if not is_admin(call.from_user.id): return
    current_status = is_maintenance_mode()
    set_maintenance_mode(not current_status)
    new_status_text = "🔓 تم فتح البوت للجميع" if current_status else "🔒 تم قفل البوت (وضع الصيانة)"
    bot.answer_callback_query(call.id, new_status_text, show_alert=True)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "admin_accounts_status")
def admin_accounts_status(call):
    if not is_admin(call.from_user.id): return
    
    text = "📊 حالة الحسابات:\n\n"
    for account in ALL_ACCOUNTS:
        status_icon = "✅" if account.get('is_logged_in', False) else "❌"
        msg_count = len(account.get('sent_messages', set()))
        errors = account.get('consecutive_errors', 0)
        text += f"{status_icon} {account['name']}\n"
        text += f"   📨 الرسائل: {msg_count}\n"
        text += f"   ⚠️ الأخطاء: {errors}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 إعادة تسجيل الكل", callback_data="admin_relogin_all"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_relogin_all")
def admin_relogin_all(call):
    if not is_admin(call.from_user.id): return
    
    bot.answer_callback_query(call.id, "🔄 جاري إعادة تسجيل الدخول لجميع الحسابات...", show_alert=True)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for account in ALL_ACCOUNTS:
            account['is_logged_in'] = False
            if account['type'] == 'ivasms':
                futures.append(executor.submit(login_to_ivasms, account))
            elif account['type'] == 'timesms':
                futures.append(executor.submit(login_to_timesms, account))
        
        for future in as_completed(futures):
            try:
                future.result(timeout=60)
            except Exception as e:
                print(f"❌ خطأ في إعادة تسجيل الدخول: {e}")
    
    bot.send_message(call.from_user.id, "✅ تم إعادة تسجيل الدخول لجميع الحسابات")
    admin_accounts_status(call)

# باقي دوال الإدارة (نفس الكود السابق)
@bot.callback_query_handler(func=lambda call: call.data == "admin_manage_admins")
def admin_manage_admins(call):
    if not is_admin(call.from_user.id): return
    admins = get_all_admins()
    text = "👥 قائمة المشرفين الحاليين:\n"
    for uid in admins:
        text += f"• <code>{uid}</code>\n"
    text += "\nاختر إجراء:"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة مشرف", callback_data="admin_add_admin"))
    for uid in admins:
        if uid != call.from_user.id:
            markup.add(types.InlineKeyboardButton(f"❌ حذف {uid}", callback_data=f"admin_remove_admin_{uid}"))
    markup.add(types.InlineKeyboardButton("🔙 العودة للوحة", callback_data="admin_panel"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_admin")
def admin_add_admin_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_admin"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="admin_manage_admins"))
    bot.edit_message_text("أرسل معرف المستخدم (user_id) لإضافته كمشرف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_admin")
def admin_add_admin_step2(message):
    try:
        uid = int(message.text.strip())
        if add_admin(uid, added_by=message.from_user.id):
            bot.reply_to(message, f"✅ تم إضافة المستخدم {uid} كمشرف بنجاح.")
        else:
            bot.reply_to(message, "❌ المستخدم موجود مسبقاً في قائمة المشرفين.")
    except ValueError:
        bot.reply_to(message, "❌ معرف غير صالح. يجب أن يكون رقماً.")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_remove_admin_"))
def admin_remove_admin(call):
    if not is_admin(call.from_user.id): return
    try:
        uid = int(call.data.split("_")[3])
    except:
        return
    if uid == call.from_user.id:
        bot.answer_callback_query(call.id, "❌ لا يمكنك حذف نفسك!", show_alert=True)
        return
    if remove_admin(uid):
        bot.answer_callback_query(call.id, f"✅ تم حذف المشرف {uid}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ فشل الحذف أو المشرف غير موجود", show_alert=True)
    admin_manage_admins(call)

# باقي دوال الإدارة (نفس الكود السابق) - أضفها هنا
@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id): return
    channels = get_all_force_sub_channels(enabled_only=False)
    text = "⚙️ إدارة قنوات الاشتراك الإجباري:\n"
    text += f"إجمالي القنوات: {len(channels)}\n──────────────────\n"
    markup = types.InlineKeyboardMarkup()
    for ch_id, url, desc in channels:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT enabled FROM force_sub_channels WHERE id=?", (ch_id,))
        enabled = c.fetchone()[0]
        conn.close()
        status = "✅" if enabled else "❌"
        btn_text = f"{status} {desc or url[:25]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"edit_force_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_force_ch"))
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_force_ch_"))
def edit_force_ch(call):
    if not is_admin(call.from_user.id): return
    try:
        ch_id = int(call.data.split("_", 3)[3])
    except:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description, enabled FROM force_sub_channels WHERE id=?", (ch_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "❌ القناة غير موجودة!", show_alert=True)
        return
    url, desc, enabled = row
    status = "مفعلة" if enabled else "معطلة"
    text = f"🔧 إدارة القناة:\nالرابط: {url}\nالوصف: {desc or '—'}\nالحالة: {status}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل الوصف", callback_data=f"edit_desc_{ch_id}"))
    if enabled:
        markup.add(types.InlineKeyboardButton("❌ تعطيل", callback_data=f"toggle_ch_{ch_id}"))
    else:
        markup.add(types.InlineKeyboardButton("✅ تفعيل", callback_data=f"toggle_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_ch_"))
def toggle_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    toggle_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "🔄 تم تغيير حالة القناة", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ch_"))
def del_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    if delete_force_sub_channel(ch_id):
        bot.answer_callback_query(call.id, "✅ تم الحذف!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ فشل الحذف!", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_desc_"))
def edit_desc_step1(call):
    ch_id = int(call.data.split("_", 2)[2])
    user_states[call.from_user.id] = f"edit_desc_{ch_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data=f"edit_force_ch_{ch_id}"))
    bot.edit_message_text("أدخل الوصف الجديد:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), str) and user_states[msg.from_user.id].startswith("edit_desc_"))
def edit_desc_step2(message):
    try:
        ch_id = int(user_states[message.from_user.id].split("_")[2])
        desc = message.text.strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE force_sub_channels SET description = ? WHERE id = ?", (desc, ch_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ تم تحديث الوصف!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "add_force_ch")
def add_force_ch_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_force_ch_url"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_force_sub"))
    bot.edit_message_text("أرسل رابط القناة (مثل: https://t.me/xxx أو @xxx):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_force_ch_url")
def add_force_ch_step2(message):
    url = message.text.strip()
    if not (url.startswith("@") or url.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح! يجب أن يبدأ بـ @ أو https://t.me/")
        return
    user_states[message.from_user.id] = {"step": "add_force_ch_desc", "url": url}
    bot.reply_to(message, "أدخل وصفًا للقناة (أو اترك فارغًا):")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "add_force_ch_desc")
def add_force_ch_step3(message):
    data = user_states[message.from_user.id]
    url = data["url"]
    desc = message.text.strip()
    if add_force_sub_channel(url, desc):
        bot.reply_to(message, f"✅ تم إضافة القناة:\n{url}\nالوصف: {desc or '—'}")
    else:
        bot.reply_to(message, "❌ القناة موجودة مسبقًا!")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "waiting_combo_file"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("📤 أرسل ملف الكومبو بصيغة TXT", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    if not is_admin(message.from_user.id): return
    if user_states.get(message.from_user.id) != "waiting_combo_file": return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            bot.reply_to(message, "❌ الملف فارغ!")
            return
        first_num = clean_number(lines[0])
        country_code = None
        for code in COUNTRY_CODES:
            if first_num.startswith(code):
                country_code = code
                break
        if not country_code:
            bot.reply_to(message, "❌ لا يمكن تحديد الدولة من الأرقام!")
            return
        save_combo(country_code, lines)
        name, flag, _ = COUNTRY_CODES[country_code]
        bot.reply_to(message, f"✅ تم حفظ الكومبو لدولة {flag} {name}\n🔢 عدد الأرقام: {len(lines)}")
        del user_states[message.from_user.id]
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id): return
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد كومبوهات!")
        return
    markup = types.InlineKeyboardMarkup()
    country_combos = {}
    for country_code, combo_index in combos:
        if country_code not in country_combos:
            country_combos[country_code] = []
        country_combos[country_code].append(combo_index)
    for country_code, indices in country_combos.items():
        if country_code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[country_code]
            for idx in indices:
                if len(indices) == 1:
                    btn_text = f"{flag} {name}"
                else:
                    btn_text = f"{flag} {name} ({idx})"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"del_combo_{country_code}_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("اختر الكومبو للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split("_")
    country_code = parts[2]
    combo_index = int(parts[3]) if len(parts) > 3 else 1
    success = delete_combo(country_code, combo_index)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    if success:
        bot.answer_callback_query(call.id, f"✅ تم حذف الكومبو: {flag} {name} ({combo_index})", show_alert=True)
    else:
        bot.answer_callback_query(call.id, f"❌ فشل حذف الكومبو!", show_alert=True)
    admin_del_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id): return
    total_users = len(get_all_users())
    combos = get_all_combos()
    unique_countries = set()
    total_combos = 0
    for country_code, combo_index in combos:
        unique_countries.add(country_code)
        total_combos += 1
    total_numbers = 0
    for country_code, combo_index in combos:
        total_numbers += len(get_combo(country_code, combo_index))
    otp_count = len(get_otp_logs())
    
    # إحصائيات الحسابات
    active_accounts = sum(1 for a in ALL_ACCOUNTS if a.get('is_logged_in', False))
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text(
        f"📊 إحصائيات البوت:\n"
        f"👥 المستخدمين النشطين: {total_users}\n"
        f"🌐 الدول المضافة: {len(unique_countries)}\n"
        f"📦 الكومبوهات: {total_combos}\n"
        f"📞 إجمالي الأرقام: {total_numbers}\n"
        f"🔑 إجمالي الأكواد المستلمة: {otp_count}\n"
        f"🖥️ الحسابات النشطة: {active_accounts}/{len(ALL_ACCOUNTS)}",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id): return
    try:
        report = "📊 تقرير شامل عن البوت\n" + "="*40 + "\n\n"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        for u in users:
            status = "محظور" if u[6] else "نشط"
            report += f"ID: {u[0]} | @{u[1] or 'N/A'} | الرقم: {u[5] or 'N/A'} | الحالة: {status}\n"
        report += "\n" + "="*40 + "\n\n"
        c.execute("SELECT * FROM otp_logs ORDER BY timestamp DESC LIMIT 500")
        logs = c.fetchall()
        for log in logs:
            user_info = get_user_info(log[5]) if log[5] else None
            user_tag = f"@{user_info[1]}" if user_info and user_info[1] else f"ID:{log[5] or 'N/A'}"
            report += f"الرقم: {log[1]} | الكود: {log[2]} | الحساب: {log[6] or 'N/A'} | المستخدم: {user_tag} | الوقت: {log[4]}\n"
        report += "\n" + "="*40 + "\n\n"
        c.execute("SELECT country_code, combo_index, LENGTH(numbers) FROM combos")
        combos_data = c.fetchall()
        for country_code, combo_index, num_length in combos_data:
            name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
            num_count = len(json.loads(get_combo(country_code, combo_index)))
            report += f"{flag} {name} ({combo_index}): {num_count} رقم\n"
        report += "\n" + "="*40 + "\n\n"
        report += "📊 حالة الحسابات:\n"
        for acc in ALL_ACCOUNTS:
            status = "✅" if acc.get('is_logged_in', False) else "❌"
            report += f"{status} {acc['name']}: {len(acc.get('sent_messages', set()))} رسالة\n"
        conn.close()
        report += "\n" + "="*40 + "\n\n"
        report += "تم إنشاء التقرير في: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("bot_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        with open("bot_report.txt", "rb") as f:
            bot.send_document(call.from_user.id, f)
        os.remove("bot_report.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لحظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid)
        bot.reply_to(message, f"✅ تم حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لفك حظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.reply_to(message, f"✅ تم فك حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ المستخدم غير موجود!")
            return
        status = "محظور" if user[6] else "نشط"
        info = f"👤 معلومات المستخدم:\n"
        info += f"🆔: {user[0]}\n"
        info += f".Username: @{user[1] or 'N/A'}\n"
        info += f"الاسم: {user[2] or ''} {user[3] or ''}\n"
        info += f"الرقم المخصص: {user[5] or 'N/A'}\n"
        info += f"الحالة: {status}"
        bot.reply_to(message, info)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("أرسل الرسالة للإرسال للجميع:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    bot.reply_to(message, f"✅ تم الإرسال إلى {success}/{len(users)} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_user")
def admin_broadcast_user_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_user_id")
def admin_broadcast_user_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(message, "أرسل الرسالة:")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, "").startswith("broadcast_msg_"))
def admin_broadcast_user_step3(message):
    uid = int(user_states[message.from_user.id].split("_")[2])
    try:
        bot.send_message(uid, message.text)
        bot.reply_to(message, f"✅ تم الإرسال للمستخدم {uid}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة كومبو برايفت", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح كومبو برايفت", callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_panel"))
    bot.edit_message_text("👤 كومبو برايفت:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_private_combo")
def add_private_combo_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_private_user_id")
def add_private_combo_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"add_private_country_{uid}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        all_combos = get_all_combos()
        country_combos = {}
        for country_code, combo_index in all_combos:
            if country_code not in country_combos:
                country_combos[country_code] = []
            country_combos[country_code].append(combo_index)
        for country_code, indices in country_combos.items():
            if country_code in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[country_code]
                for idx in indices:
                    if len(indices) == 1:
                        btn_text = f"{flag} {name}"
                    else:
                        btn_text = f"{flag} {name} ({idx})"
                    buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"select_private_{uid}_{country_code}"))
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
        markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_private_combo"))
        bot.reply_to(message, "اختر الدولة:", reply_markup=markup)
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_private_"))
def select_private_combo(call):
    parts = call.data.split("_")
    uid = int(parts[2])
    country_code = parts[3]
    save_user(uid, private_combo_country=country_code)
    name, flag, _ = COUNTRY_CODES[country_code]
    bot.answer_callback_query(call.id, f"✅ تم تعيين كومبو برايفت لـ {uid} - {flag} {name}", show_alert=True)
    admin_private_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "del_private_combo")
def del_private_combo_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "del_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 𝐁𝐀𝐂𝐊", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "del_private_user_id")
def del_private_combo_step2(message):
    try:
        uid = int(message.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(message, f"✅ تم مسح الكومبو البرايفت للمستخدم {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    del user_states[message.from_user.id]

# ======================
# ▶️ تشغيل البوت
# ======================
def run_bot():
    print("[*] Starting bot...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # تشغيل البوت في thread منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل الحلقة الرئيسية
    main_loop()