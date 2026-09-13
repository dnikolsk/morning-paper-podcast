#!/usr/bin/env python3
"""Publish a Morning Paper episode.

Copies an MP3 into episodes/YYYY-MM-DD.mp3 and inserts (or updates) the matching
<item> in feed.xml, keeping items ordered newest first.

Usage:
    python3 scripts/publish_episode.py --mp3 recording.mp3 \
        --title "Morning Paper - 13 Sep 2026" --date 2026-09-13 \
        [--summary "Short description"]

Only the Python standard library is used.
"""

import argparse
import datetime as dt
import email.utils
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FEED_PATH = REPO_ROOT / "feed.xml"
EPISODES_DIR = REPO_ROOT / "episodes"
BASE_URL = "https://dnikolsk.github.io/morning-paper-podcast/"

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"

ET.register_namespace("itunes", ITUNES_NS)
ET.register_namespace("atom", ATOM_NS)


def itunes(tag: str) -> str:
    return f"{{{ITUNES_NS}}}{tag}"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mp3", required=True, type=Path, help="Path to the episode MP3")
    parser.add_argument("--title", required=True, help="Episode title")
    parser.add_argument("--date", required=True, help="Episode date, YYYY-MM-DD")
    parser.add_argument("--summary", default=None, help="Optional episode description")
    args = parser.parse_args(argv)

    try:
        args.episode_date = dt.date.fromisoformat(args.date)
    except ValueError:
        parser.error(f"--date must be YYYY-MM-DD, got {args.date!r}")
    if not args.mp3.is_file():
        parser.error(f"--mp3 file not found: {args.mp3}")
    return args


def pub_date(day: dt.date) -> str:
    # Publish time is fixed at 06:00 UTC so re-running for the same date is idempotent.
    moment = dt.datetime(day.year, day.month, day.day, 6, 0, 0, tzinfo=dt.timezone.utc)
    return email.utils.format_datetime(moment)


def now_rfc2822() -> str:
    return email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))


def item_sort_key(item: ET.Element) -> str:
    # Items are keyed on the YYYY-MM-DD filename embedded in the enclosure URL.
    enclosure = item.find("enclosure")
    url = enclosure.get("url", "") if enclosure is not None else ""
    return Path(url).stem


def build_item(title: str, day: dt.date, summary: str | None, size: int) -> ET.Element:
    filename = f"{day.isoformat()}.mp3"
    url = f"{BASE_URL}episodes/{filename}"

    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = url
    guid = ET.SubElement(item, "guid", isPermaLink="false")
    guid.text = url
    ET.SubElement(item, "pubDate").text = pub_date(day)
    ET.SubElement(item, "enclosure", url=url, length=str(size), type="audio/mpeg")
    ET.SubElement(item, itunes("title")).text = title
    ET.SubElement(item, itunes("episodeType")).text = "full"
    ET.SubElement(item, itunes("explicit")).text = "false"
    if summary:
        ET.SubElement(item, "description").text = summary
        ET.SubElement(item, itunes("summary")).text = summary
    return item


def upsert_item(channel: ET.Element, new_item: ET.Element) -> bool:
    """Replace any existing item for the same date, then re-sort newest first.

    Returns True if an existing item was replaced.
    """
    key = item_sort_key(new_item)
    existing = channel.findall("item")
    for it in existing:
        channel.remove(it)

    kept = [it for it in existing if item_sort_key(it) != key]
    replaced = len(kept) != len(existing)
    kept.append(new_item)
    kept.sort(key=item_sort_key, reverse=True)
    for it in kept:
        channel.append(it)
    return replaced


def update_last_build_date(channel: ET.Element) -> None:
    node = channel.find("lastBuildDate")
    if node is None:
        node = ET.SubElement(channel, "lastBuildDate")
    node.text = now_rfc2822()


def main(argv=None) -> int:
    args = parse_args(argv)

    if not FEED_PATH.is_file():
        print(f"feed not found: {FEED_PATH}", file=sys.stderr)
        return 1

    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    dest = EPISODES_DIR / f"{args.episode_date.isoformat()}.mp3"
    if args.mp3.resolve() != dest.resolve():
        shutil.copyfile(args.mp3, dest)
    size = dest.stat().st_size

    tree = ET.parse(FEED_PATH)
    root = tree.getroot()
    channel = root.find("channel")
    if channel is None:
        print("feed.xml has no <channel> element", file=sys.stderr)
        return 1

    new_item = build_item(args.title, args.episode_date, args.summary, size)
    replaced = upsert_item(channel, new_item)
    update_last_build_date(channel)

    ET.indent(root, space="  ")
    tree.write(FEED_PATH, encoding="UTF-8", xml_declaration=True)
    with FEED_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n")

    action = "Updated" if replaced else "Added"
    print(f"{action} episode {args.episode_date.isoformat()} ({size} bytes)")
    print(f"  file: {dest.relative_to(REPO_ROOT)}")
    print(f"  url:  {BASE_URL}episodes/{dest.name}")
    print(f"  feed: {FEED_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
