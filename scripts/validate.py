#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import sys

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title_depth = 0
        self.title = ""
        self.description = ""

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and "href" in values:
            self.links.append(values["href"])
        elif tag == "link" and "href" in values:
            self.links.append(values["href"])
        elif tag == "title":
            self.title_depth += 1
        elif tag == "meta" and values.get("name") == "description":
            self.description = values.get("content", "").strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self.title_depth -= 1

    def handle_data(self, data):
        if self.title_depth:
            self.title += data


def resolve(page, href):
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return None
    parsed = urlparse(clean)
    if parsed.scheme or clean.startswith("//"):
        return None
    target = ROOT / clean.lstrip("/") if clean.startswith("/") else page.parent / clean
    target = target.resolve()
    if target.is_dir():
        target /= "index.html"
    return target


def main():
    errors = []
    titles = {}
    pages = sorted(ROOT.rglob("*.html"))
    for page in pages:
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        title = parser.title.strip()
        if not title:
            errors.append(f"{page.relative_to(ROOT)}: title is missing")
        elif title in titles:
            errors.append(f"{page.relative_to(ROOT)}: duplicate title with {titles[title]}")
        else:
            titles[title] = page.relative_to(ROOT)
        if not parser.description:
            errors.append(f"{page.relative_to(ROOT)}: meta description is missing")
        for href in parser.links:
            if href.startswith(("http://", "//")):
                errors.append(f"{page.relative_to(ROOT)}: external URL must use https: {href}")
                continue
            target = resolve(page, href)
            if target and ROOT not in target.parents and target != ROOT:
                errors.append(f"{page.relative_to(ROOT)}: link escapes project: {href}")
            elif target and not target.exists():
                errors.append(f"{page.relative_to(ROOT)}: broken link: {href}")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: validated {len(pages)} HTML pages; titles, descriptions, and links are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
