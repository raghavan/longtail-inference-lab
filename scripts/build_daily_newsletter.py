#!/usr/bin/env python3
"""Build a focused daily newsletter for Long Tail Inference Lab.

The generator is intentionally dependency free so it can run in GitHub Actions,
on a laptop, or in a small VPS without extra setup. It collects public signals
from arXiv, Hacker News, and GitHub repository search, then writes a dated
Markdown digest into docs/newsletter.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Iterable

NEWSLETTER_DIR = Path("docs/newsletter")
DEFAULT_LOOKBACK_DAYS = 2
USER_AGENT = "longtail-inference-lab-newsletter/1.0"

FOCUS_TOPICS = [
    "edge LLM inference",
    "open weight model serving",
    "local LLM runtime",
    "laptop plus VPS split inference",
    "network tax measurement",
    "job level inference routing",
    "quantized models",
    "llama.cpp",
    "GGUF",
    "vLLM",
    "Ollama",
    "distributed inference",
    "on device AI",
    "home lab compute",
]

HN_QUERIES = [
    "local llm",
    "edge inference",
    "llama.cpp",
    "open weight model",
    "vllm inference",
    "ollama",
    "on device ai",
    "distributed inference",
]

GITHUB_QUERIES = [
    "local llm inference",
    "edge llm inference",
    "llama.cpp",
    "gguf quantization",
    "vllm serving",
    "ollama local model",
    "distributed inference llm",
]

ARXIV_TERMS = [
    "edge inference",
    "local LLM",
    "large language model serving",
    "LLM quantization",
    "distributed inference",
    "on device AI",
    "speculative decoding",
    "efficient inference",
]


@dataclass(frozen=True)
class Item:
    source: str
    title: str
    url: str
    date_text: str
    summary: str = ""
    score: int = 0


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "digest"


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def request_text(url: str, *, timeout: int = 25) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def request_json(url: str) -> dict:
    return json.loads(request_text(url))


def score_item(title: str, summary: str = "") -> int:
    haystack = f"{title} {summary}".lower()
    score = 0
    for topic in FOCUS_TOPICS:
        topic_l = topic.lower()
        if topic_l in haystack:
            score += 4
        else:
            tokens = [part for part in re.split(r"[^a-z0-9]+", topic_l) if len(part) > 2]
            score += sum(1 for token in tokens if token in haystack)
    return score


def dedupe(items: Iterable[Item]) -> list[Item]:
    seen: set[str] = set()
    unique: list[Item] = []
    for item in items:
        key = item.url.lower() if item.url else slugify(item.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return sorted(unique, key=lambda item: (item.score, item.date_text), reverse=True)


def fetch_arxiv(max_results: int) -> list[Item]:
    query = " OR ".join(f'all:"{term}"' for term in ARXIV_TERMS)
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(max_results),
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    try:
        text = request_text(url)
    except Exception as exc:
        print(f"warning: arXiv fetch failed: {exc}", file=sys.stderr)
        return []

    root = ET.fromstring(text)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    items: list[Item] = []
    for entry in root.findall("atom:entry", namespace):
        title = normalize_space(entry.findtext("atom:title", default="", namespaces=namespace))
        summary = normalize_space(entry.findtext("atom:summary", default="", namespaces=namespace))
        published = entry.findtext("atom:published", default="", namespaces=namespace)[:10]
        link = ""
        for candidate in entry.findall("atom:link", namespace):
            if candidate.attrib.get("rel") == "alternate":
                link = candidate.attrib.get("href", "")
                break
        if not title or not link:
            continue
        items.append(
            Item(
                source="arXiv",
                title=title,
                url=link,
                date_text=published,
                summary=summary[:320],
                score=score_item(title, summary),
            )
        )
    return items


def fetch_hacker_news(since: datetime, max_results: int) -> list[Item]:
    since_epoch = int(since.timestamp())
    items: list[Item] = []
    for query in HN_QUERIES:
        params = urllib.parse.urlencode(
            {
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{since_epoch}",
                "hitsPerPage": str(max_results),
            }
        )
        url = f"https://hn.algolia.com/api/v1/search_by_date?{params}"
        try:
            payload = request_json(url)
        except Exception as exc:
            print(f"warning: Hacker News fetch failed for {query}: {exc}", file=sys.stderr)
            continue
        for hit in payload.get("hits", []):
            title = normalize_space(hit.get("title") or hit.get("story_title") or "")
            target_url = hit.get("url") or hit.get("story_url") or ""
            object_id = hit.get("objectID")
            if not target_url and object_id:
                target_url = f"https://news.ycombinator.com/item?id={object_id}"
            created = (hit.get("created_at") or "")[:10]
            if not title or not target_url:
                continue
            points = int(hit.get("points") or 0)
            item_score = score_item(title) + min(points // 10, 10)
            items.append(Item("Hacker News", title, target_url, created, score=item_score))
        time.sleep(0.2)
    return items


def fetch_github_repos(since_date: date, max_results: int) -> list[Item]:
    items: list[Item] = []
    for query in GITHUB_QUERIES:
        github_query = f'{query} pushed:>={since_date.isoformat()} archived:false'
        params = urllib.parse.urlencode(
            {
                "q": github_query,
                "sort": "updated",
                "order": "desc",
                "per_page": str(max_results),
            }
        )
        url = f"https://api.github.com/search/repositories?{params}"
        try:
            payload = request_json(url)
        except Exception as exc:
            print(f"warning: GitHub repo search failed for {query}: {exc}", file=sys.stderr)
            continue
        for repo in payload.get("items", []):
            full_name = repo.get("full_name", "")
            description = normalize_space(repo.get("description") or "")
            html_url = repo.get("html_url", "")
            pushed = (repo.get("pushed_at") or "")[:10]
            if not full_name or not html_url:
                continue
            title = f"{full_name}: {description}" if description else full_name
            stars = int(repo.get("stargazers_count") or 0)
            item_score = score_item(title, description) + min(stars // 1000, 10)
            items.append(Item("GitHub", title, html_url, pushed, description, item_score))
        time.sleep(0.2)
    return items


def render_items(items: list[Item], *, empty_text: str, limit: int) -> str:
    if not items:
        return f"- {empty_text}\n"
    lines: list[str] = []
    for item in items[:limit]:
        date_part = f" · {item.date_text}" if item.date_text else ""
        lines.append(f"- [{item.title}]({item.url})  ")
        lines.append(f"  Source: {item.source}{date_part}. Focus score: {item.score}.")
        if item.summary:
            lines.append(f"  {item.summary}")
    return "\n".join(lines) + "\n"


def build_markdown(today: date, arxiv: list[Item], hn: list[Item], repos: list[Item]) -> str:
    all_items = dedupe([*arxiv, *hn, *repos])
    top_signals = all_items[:8]

    return f"""# Long Tail Inference Daily Digest

Date: {today.isoformat()}

This digest tracks signals relevant to Long Tail Inference Lab: edge LLM inference, open weight serving, laptop plus VPS split inference, network tax measurement, quantized models, inference routing, and verified everyday compute experiments.

## Highest signal items

{render_items(top_signals, empty_text="No high signal items found in the current lookback window.", limit=8)}

## Papers and technical notes

{render_items(dedupe(arxiv), empty_text="No matching arXiv items found today.", limit=8)}

## Builder and implementation signals

{render_items(dedupe(repos), empty_text="No matching GitHub repositories found today.", limit=8)}

## Community discussion

{render_items(dedupe(hn), empty_text="No matching Hacker News stories found today.", limit=8)}

## Suggested lab follow ups

- Turn one high signal item into a reproducible benchmark under `experiments/`.
- Add a network tax measurement if the item depends on remote execution.
- Compare local, VPS, and split execution paths before claiming a win.
- Capture model, quantization, hardware, latency, tokens per second, cost, and failure mode metadata.

Generated by `scripts/build_daily_newsletter.py`.
"""


def write_index(today: date, digest_path: Path) -> None:
    index_path = NEWSLETTER_DIR / "README.md"
    relative = digest_path.name
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Newsletter Archive\n\n"
    line = f"- [{today.isoformat()}]({relative})\n"
    if line not in existing:
        existing = existing.rstrip() + "\n" + line
    index_path.write_text(existing, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Long Tail Inference Lab daily newsletter.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Digest date in YYYY-MM-DD format.")
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    parser.add_argument("--max-results", type=int, default=10)
    args = parser.parse_args()

    today = date.fromisoformat(args.date)
    since = datetime.combine(today, datetime.min.time(), tzinfo=UTC) - timedelta(days=args.lookback_days)

    NEWSLETTER_DIR.mkdir(parents=True, exist_ok=True)

    arxiv = dedupe(fetch_arxiv(args.max_results))
    hn = dedupe(fetch_hacker_news(since, args.max_results))
    repos = dedupe(fetch_github_repos(since.date(), args.max_results))

    digest_path = NEWSLETTER_DIR / f"{today.isoformat()}.md"
    digest_path.write_text(build_markdown(today, arxiv, hn, repos), encoding="utf-8")
    write_index(today, digest_path)

    latest_path = NEWSLETTER_DIR / "latest.md"
    latest_path.write_text(digest_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"wrote {digest_path}")
    print(f"wrote {latest_path}")
    print(f"updated {NEWSLETTER_DIR / 'README.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
