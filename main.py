import os
import discord
import feedparser
import asyncio
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")

CHANNELS = {
    "geo": 1460156889106092136,
    "eco": 1460156891911950463,
    "market": 1460156894164291668,
    "breaking": 1460156896257507593,
    "energy": 1460156898694271010,
    "commodities": 1460156901387141205,
    "tech": 1460156903920238809,
    "daily": 1460156908810797229,
    "hourly": 1460156912032026716,
    "risk": 1460156914699604142,
    "snapshot": 1460156916662669322,
    "volatility": 1460170786756100177,
    "terminal": 1460156919737090198,
    "chart": 1460156922132168724,
    "indicator": 1460156923952500878,
    "ai": 1460156926406037505,
    "sentiment": 1460171055787409532,
    "archive": 1460156930667581492,
    "summaryarchive": 1460156932122873949
}

RSS_FEEDS = [
    "https://www.reuters.com/world/rss",
    "https://www.reuters.com/markets/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://www.ft.com/?format=rss",
    "https://www.investing.com/rss/news_285.rss",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.fxstreet.com/rss/news",
    "https://www.dailyfx.com/feeds/market-news",
    "https://www.oilprice.com/rss/main",
    "https://metalsdaily.com/rss/",
    "https://www.opec.org/opec_web/en/press/rss.html",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.technologyreview.com/feed/",
]

KEYWORDS = {
    "geo": ["war","attack","military","troop","nato","russia","china","iran","gaza","israel","missile","conflict","strike"],
    "eco": ["inflation","gdp","cpi","ppi","jobs","economy","recession","growth","federal","imf","world bank"],
    "market": ["stocks","forex","crypto","bitcoin","ethereum","nasdaq","dow","sp500","bond","yield"],
    "breaking": ["breaking","urgent","explosion","dead","killed","emergency"],
    "energy": ["oil","brent","wti","gas","energy","opec","production","pipeline"],
    "commodities": ["gold","silver","copper","iron","nickel","commodity"],
    "tech": ["ai","tech","robot","software","cyber","apple","google","microsoft","chip","semiconductor"],
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

last_sent = set()
message_timestamps = {}


def fetch_news():
    results = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for item in feed.entries[:8]:
            title = item.title
            link = item.link
            lower = title.lower()

            category = None
            for cat, words in KEYWORDS.items():
                if any(w in lower for w in words):
                    category = cat
            if category:
                results.append((category, title, link))
    return results


async def post_news():
    await client.wait_until_ready()

    while True:
        news_items = fetch_news()

        for cat, title, link in news_items:
            msg_hash = f"{cat}{title}"
            if msg_hash in last_sent:
                continue
            
            ch_id = CHANNELS.get(cat)
            ch = client.get_channel(ch_id)
            if ch:
                msg = await ch.send(f"🔹 **{title}**\n{link}")
                last_sent.add(msg_hash)
                message_timestamps[msg.id] = datetime.utcnow()

            await asyncio.sleep(2)
        
        await asyncio.sleep(60)


async def auto_delete():
    await client.wait_until_ready()

    while True:
        now = datetime.utcnow()
        for msg_id, timestamp in list(message_timestamps.items()):
            if now - timestamp > timedelta(hours=48):
                for channel_id in CHANNELS.values():
                    ch = client.get_channel(channel_id)
                    try:
                        msg = await ch.fetch_message(msg_id)
                        await msg.delete()
                        del message_timestamps[msg_id]
                    except:
                        pass
        await asyncio.sleep(300)


async def hourly_summary():
    await client.wait_until_ready()
    ch = client.get_channel(CHANNELS["hourly"])

    while True:
        content = []
        for cat, _, _ in fetch_news():
            content.append(f"• {cat.upper()} updated")

        summary = "\n".join(content[:50])
        await ch.send(f"🕒 **Hourly Summary**\n{summary}")
        await asyncio.sleep(3600)


@client.event
async def on_ready():
    print(f"🔥 BOT ONLINE as {client.user}")
    client.loop.create_task(post_news())
    client.loop.create_task(hourly_summary())
    client.loop.create_task(auto_delete())


client.run(TOKEN)
