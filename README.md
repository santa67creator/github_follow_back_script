# This script made for following and unsubscribe from people who don't mutually subscribe

step one you need create classic token github

`export GITHUB_TOKEN=ghp_your_token`

step two you need install this lib

`pip install argparse, json, os, random, sys, time, pathlib, requests`

step three launch it

`python follow_back.py --unfollow --dry-run`

# commands (flags)

Without `--unfollow`, the script only follows.

`--dry-run` shows who subscribe

`python follow_back.py` run file

`--watch 60` check every 30-60 minutes

------

# Usage:
    export GITHUB_TOKEN=ghp_xxx        # classic token with scope: user:follow
    python follow_back.py --dry-run    # just show what would happen
    python follow_back.py              # run once
    python follow_back.py --watch 30   # check every 30 minutes
    python follow_back.py --unfollow --dry-run   # show who doesn't follow you back
    python follow_back.py --unfollow             # also unfollow non-followers
 
Put logins you never want to unfollow into whitelist.txt (one per line).

-----

# OTHER

A pause of 5–15 seconds between actions

To protect such individuals, create a file named `whitelist.txt` in the same directory and list their usernames, one per line. 

Lines beginning with `#` are treated as comments. The script will not unsubscribe anyone included in this list.



<img width="627" height="258" alt="image" src="https://github.com/user-attachments/assets/c72d21d0-db22-44ab-96be-e0a9d5761bfd" />


