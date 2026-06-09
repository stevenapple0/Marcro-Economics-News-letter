"""Fetch latest macro-economics headlines from a fixed set of RSS feeds.

Standard-library only (urllib + xml.etree) so it runs anywhere without pip installs.
Prints a JSON array of {feed, title, link, published, summary} to stdout,
limited to items published within HOURS_BACK hours (falls back to the
newest N items per feed if a feed has no parsable dates).
"""
import json
import re
import sys
import urllib.request

# Force UTF-8 on stdout/stderr regardless of the system locale (Windows
# console code pages mangle curly quotes etc. otherwise).
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

FEEDS = {
    # Real-time markets & macro data
    "WSJ Markets":            "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
    "WSJ World News":         "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "CNBC Economy":           "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "Investing.com Economy":  "https://www.investing.com/rss/news_14.rss",
    # Premium outlets — titles & summaries free via RSS
    "Bloomberg Economics":    "https://feeds.bloomberg.com/economics/news.rss",
    "FT Economics":           "https://www.ft.com/economics?format=rss",
    "The Economist Finance":  "https://www.economist.com/finance-and-economics/rss.xml",
    "Project Syndicate":      "https://www.project-syndicate.org/rss",
    # Official / central bank
    "Federal Reserve":        "https://www.federalreserve.gov/feeds/press_all.xml",
    # IMF Blog & World Bank Blogs: RSS currently blocked externally — omitted
}

HOURS_BACK = 36          # how far back to look for "today's" news
MAX_PER_FEED = 8         # fallback cap when dates can't be parsed
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TAG_RE = re.compile(r"<[^>]+>")

import http.cookiejar as _cj
_OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_cj.CookieJar())
)


def strip_html(text):
    if not text:
        return ""
    return TAG_RE.sub("", text).replace("&nbsp;", " ").strip()


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml,application/xml,text/xml,*/*",
    })
    with _OPENER.open(req, timeout=20) as resp:
        return resp.read()


def parse_feed(name, url, cutoff):
    items = []
    try:
        raw = fetch(url)
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"[warn] failed to fetch/parse {name}: {e}", file=sys.stderr)
        return items

    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_raw = item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date")
        summary = item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or ""
        summary = strip_html(summary)[:600]

        published = None
        if pub_raw:
            try:
                published = parsedate_to_datetime(pub_raw)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except Exception:
                published = None

        if not title or not link:
            continue

        items.append({
            "feed": name,
            "title": title,
            "link": link,
            "published": published.isoformat() if published else None,
            "summary": summary,
        })

    with_dates = [i for i in items if i["published"]]
    if with_dates:
        items = [i for i in items if i["published"] and
                 datetime.fromisoformat(i["published"]) >= cutoff]
        items.sort(key=lambda i: i["published"], reverse=True)
    else:
        items = items[:MAX_PER_FEED]

    return items[:MAX_PER_FEED]


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    all_items = []
    for name, url in FEEDS.items():
        all_items.extend(parse_feed(name, url, cutoff))

    print(json.dumps(all_items, ensure_ascii=False, indent=2))
    print(f"[info] collected {len(all_items)} articles from {len(FEEDS)} feeds", file=sys.stderr)


if __name__ == "__main__":
    main()
