#!/usr/bin/env python3
"""Check external links in content/*.md for breakages.

Extracts every http(s) URL referenced in the blog's markdown content
(markdown links/images, HTML src/href attributes, bare URLs), checks each
unique URL concurrently, and reports problems grouped by content file.

Usage:
    python3 check_broken_links.py              # full scan
    python3 check_broken_links.py --limit 200  # quick sample spread
    python3 check_broken_links.py --skip-domain amazon.com --skip-domain x.com

Categories reported:
    gone     - 404/410: the page no longer exists
    dead     - host does not resolve or refuses connections
    timeout  - server did not answer in time
    tls      - certificate/SSL problem
    blocked  - 401/403/429: usually bot detection, check manually
    server   - 5xx: remote server error, possibly transient

Exit code is 1 if any "gone" or "dead" links are found (0 otherwise), so
the script can be wired into CI. Use --strict to fail on any non-OK result.
"""
import argparse
import collections
import concurrent.futures
import glob
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
URL_RE = re.compile(r'https?://[^\s\)"\'\]<>}]+')
TRAILING = '.,;!\'">'
QUOTE_SAFE = ":/?#[]@!$&'()*+,;=%"
MARKDOWN_URL_RE = re.compile(r'!?\[[^\]]*\]\((https?://[^\s]+?)(?:\s+["\'][^"\']*["\'])?\)')
HTML_URL_RE = re.compile(r'(?:href|src)=["\'](https?://[^"\']+)["\']', re.I)
BARE_URL_RE = re.compile(r'https?://[^\s\)"\'\]<>}]+')

GONE = (404, 405, 410)
BLOCKED = (401, 402, 403, 407, 429)
BOT_BLOCKED = ('facebook.com', 'fb.com')


def extract_refs(root):
    """Map each unique URL to a list of (file, line) references."""
    refs = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(root, '**', '*.md'), recursive=True)):
        rel = os.path.relpath(path, root)
        try:
            text = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
        for lineno, line in enumerate(text.splitlines(), 1):
            spans = []
            for regex in (MARKDOWN_URL_RE, HTML_URL_RE):
                for m in regex.finditer(line):
                    url = m.group(1).rstrip(TRAILING)
                    refs[url].append((rel, lineno))
                    spans.append(m.span(1))
            for m in BARE_URL_RE.finditer(line):
                if any(start <= m.start() < end for start, end in spans):
                    continue
                refs[m.group(0).rstrip(TRAILING)].append((rel, lineno))
    return refs


def classify_reason(reason):
    if isinstance(reason, socket.gaierror):
        return 'dead'
    if isinstance(reason, ConnectionRefusedError):
        return 'dead'
    if isinstance(reason, ssl.SSLError):
        return 'tls'
    if isinstance(reason, TimeoutError) or 'timed out' in str(reason).lower():
        return 'timeout'
    return 'error'


def check(url, timeout):
    """Return (category, http_code, detail) for one URL."""
    quoted = urllib.parse.quote(url, safe=QUOTE_SAFE)
    req = urllib.request.Request(quoted, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(64)  # don't download whole files/images
            return 'ok', resp.status, ''
    except urllib.error.HTTPError as e:
        code = e.code
        host = urllib.parse.urlparse(url).netloc.lower()
        if code in GONE:
            return 'gone', code, e.reason or ''
        if code in BLOCKED or (code == 400 and any(host.endswith(d) for d in BOT_BLOCKED)):
            return 'blocked', code, e.reason or ''
        if 500 <= code < 600:
            return 'server', code, e.reason or ''
        return 'error', code, e.reason or ''
    except urllib.error.URLError as e:
        return classify_reason(e.reason), 0, str(e.reason)
    except (TimeoutError, socket.timeout):
        return 'timeout', 0, ''
    except Exception as e:  # malformed URL, etc.
        return 'error', 0, str(e)


def spread(urls, limit):
    """Pick an even spread of up to `limit` URLs from the sorted list."""
    if not limit or len(urls) <= limit:
        return urls
    step = len(urls) / limit
    return [urls[int(i * step)] for i in range(limit)]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--content-dir', default='content')
    ap.add_argument('--workers', type=int, default=40)
    ap.add_argument('--timeout', type=int, default=12)
    ap.add_argument('--limit', type=int, default=0,
                    help='check only an even sample of N URLs')
    ap.add_argument('--skip-domain', action='append', default=[],
                    help='skip URLs on this domain (repeatable)')
    ap.add_argument('--strict', action='store_true',
                    help='exit 1 on any non-OK result, incl. blocked/5xx')
    args = ap.parse_args()

    refs = extract_refs(args.content_dir)
    urls = sorted(refs)
    skipped = [u for u in urls
               if any(urllib.parse.urlparse(u).netloc.lower().endswith(d.lstrip('.').lower())
                      for d in args.skip_domain)]
    urls = spread([u for u in urls if u not in set(skipped)], args.limit)

    print(f"Checking {len(urls)} unique URLs "
          f"({len(refs)} found, {len(skipped)} skipped by domain)...\n")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_to_url = {pool.submit(check, u, args.timeout): u for u in urls}
        done = 0
        for fut in concurrent.futures.as_completed(future_to_url):
            results[future_to_url[fut]] = fut.result()
            done += 1
            if done % 500 == 0:
                print(f"  ...{done}/{len(urls)}")

    by_cat = collections.defaultdict(dict)
    for url, (cat, code, detail) in results.items():
        by_cat[cat][url] = (code, detail)

    fatal_cats = ('gone', 'dead')
    report_cats = ('gone', 'dead', 'timeout', 'tls', 'error')

    for cat in report_cats:
        if not by_cat.get(cat):
            continue
        print(f"\n{'=' * 60}\n{cat.upper()} ({len(by_cat[cat])} URLs)\n{'=' * 60}")
        for url, (code, detail) in sorted(by_cat[cat].items()):
            label = f"HTTP {code}" if code else detail
            print(f"\n  {url}\n    -> {label}")
            for rel, lineno in refs[url][:5]:
                print(f"    {rel}:{lineno}")
            extra = len(refs[url]) - 5
            if extra > 0:
                print(f"    ...and {extra} more")

    for cat in ('blocked', 'server'):
        if not by_cat.get(cat):
            continue
        print(f"\n{'=' * 60}\n{cat.upper()} ({len(by_cat[cat])} URLs, "
              f"manual check recommended)\n{'=' * 60}")
        for url, (code, detail) in sorted(by_cat[cat].items()):
            print(f"  HTTP {code}  {url}  ({len(refs[url])} ref(s))")

    print(f"\n{'=' * 60}\nSUMMARY\n{'=' * 60}")
    total = len(results)
    for cat in ('ok', 'gone', 'dead', 'timeout', 'tls', 'blocked', 'server', 'error'):
        n = len(by_cat.get(cat, {}))
        if n:
            print(f"  {cat:8s} {n:5d}  ({100.0 * n / total:.1f}%)")

    bad = sum(len(by_cat.get(c, {})) for c in fatal_cats)
    if args.strict:
        bad = total - len(by_cat.get('ok', {}))
    if bad:
        print(f"\n{bad} broken link(s) need attention.")
        sys.exit(1)
    print("\nNo dead links found.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit('\nInterrupted.')
