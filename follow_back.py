#!/usr/bin/env python3
"""
GitHub follow-back: follows only the people who follow you.

Usage:
    export GITHUB_TOKEN=ghp_xxx        # classic token with scope: user:follow
    python follow_back.py --dry-run    # just show what would happen
    python follow_back.py              # run once
    python follow_back.py --watch 30   # check every 30 minutes
    python follow_back.py --unfollow --dry-run   # show who doesn't follow you back
    python follow_back.py --unfollow             # also unfollow non-followers

Put logins you never want to unfollow into whitelist.txt (one per line).
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import requests

API = "https://api.github.com"
STATE_FILE = Path("follow_back_state.json")  # logins already handled
WHITELIST_FILE = Path("whitelist.txt")       # never unfollow these (one login per line)

TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("Set GITHUB_TOKEN environment variable first.")

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})


def request(method, url, **kwargs):
    """Request with basic rate-limit handling."""
    while True:
        r = session.request(method, url, timeout=30, **kwargs)
        if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - int(time.time()), 1) + 5
            print(f"Rate limit hit, sleeping {wait}s...")
            time.sleep(wait)
            continue
        return r


def get_logins(path):
    """Return a set of logins from a paginated endpoint."""
    logins, page = set(), 1
    while True:
        r = request("GET", f"{API}{path}", params={"per_page": 100, "page": page})
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        logins.update(u["login"] for u in data)
        page += 1
    return logins


def load_state():
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_state(state):
    STATE_FILE.write_text(json.dumps(sorted(state), indent=2))


def load_whitelist():
    if not WHITELIST_FILE.exists():
        return set()
    lines = WHITELIST_FILE.read_text().splitlines()
    return {l.strip().lower() for l in lines if l.strip() and not l.startswith("#")}


def unfollow_non_followers(followers, following, dry_run):
    whitelist = load_whitelist()
    todo = sorted(
        u for u in following - followers if u.lower() not in whitelist
    )
    print(f"Not following you back: {len(todo)} (whitelisted skipped: {len(whitelist)})")

    for login in todo:
        if dry_run:
            print(f"[dry-run] would unfollow {login}")
            continue
        r = request("DELETE", f"{API}/user/following/{login}")
        if r.status_code == 204:
            print(f"Unfollowed {login}")
        else:
            print(f"Failed to unfollow {login}: {r.status_code} {r.text[:100]}")
        time.sleep(random.uniform(5, 15))


def run_once(dry_run, unfollow=False):
    me = request("GET", f"{API}/user")
    me.raise_for_status()
    print(f"Logged in as {me.json()['login']}")

    followers = get_logins("/user/followers")
    following = get_logins("/user/following")
    handled = load_state()

    # Followers I'm not following yet and haven't processed before.
    # (If you manually unfollow someone, they won't be re-followed.)
    todo = sorted(followers - following - handled)
    print(f"Followers: {len(followers)}, following: {len(following)}, to follow: {len(todo)}")

    for login in todo:
        if dry_run:
            print(f"[dry-run] would follow {login}")
            continue
        r = request("PUT", f"{API}/user/following/{login}")
        if r.status_code == 204:
            print(f"Followed {login}")
            handled.add(login)
            save_state(handled)
        else:
            print(f"Failed to follow {login}: {r.status_code} {r.text[:100]}")
        time.sleep(random.uniform(5, 15))  # be gentle, avoid looking like spam

    if unfollow:
        unfollow_non_followers(followers, following, dry_run)

    # Remember everyone who is already mutual so we never touch them later.
    if not dry_run:
        handled |= followers & following
        save_state(handled)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="don't follow anyone")
    p.add_argument("--watch", type=int, metavar="MIN", help="repeat every N minutes")
    p.add_argument("--unfollow", action="store_true",
                   help="also unfollow people who don't follow you back (respects whitelist.txt)")
    args = p.parse_args()

    while True:
        try:
            run_once(args.dry_run, args.unfollow)
        except requests.RequestException as e:
            print(f"Network/API error: {e}")
        if not args.watch:
            break
        print(f"Sleeping {args.watch} min...\n")
        time.sleep(args.watch * 60)


if __name__ == "__main__":
    main()
