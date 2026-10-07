#!/usr/bin/env python3
"""Pull whole task blocks out of an ansible-playbook log by partial task name.

Usage:
    ansible_log_filter.py PATTERN [PATTERN...] [-f LOGFILE...]
    ansible-playbook site.yml | ansible_log_filter.py cuda install

A block is the TASK banner plus every line that follows it, up to the next
banner (PLAY / TASK / SECTION / summary rules) or end of log: the per-host
output, `fatal: [host]:` failures, `[WARNING]:` lines and blank lines in
between. Patterns are case-insensitive substrings of the task name; any
pattern matching selects the block. `--regex` treats them as regexes.

Both log shapes are read: the default human-readable run output (colour
stripped) and `--json` / `--output-format json` event logs.

Exit status: 0 when something matched, 1 when nothing did (like grep).
"""

import argparse
import json
import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# A banner starts a new section. Ansible pads banners with a run of '*', so
# requiring that run keeps command output that happens to start with TASK/PLAY
# from being read as a header.
BANNER = re.compile(
    r"^\s*(?P<kind>PLAY|TASK|SECTION|META|BOOTSTRAP SECTION|ANSIBLE SECTION)"
    r"(?:\s+\[(?P<label>[^\]]*)\])?.*?\*{4,}\s*$"
)
SUMMARY = re.compile(r"^\s*={4,}\s*$")


# Ansible pads every block with a blank line before the next banner; drop those
# so block counts and printed gaps stay honest.
def trim(blocks):
    for block in blocks:
        body = block[2]
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        block[2] = body
    return blocks


def blocks_from_text(text):
    """Return [(task_name, play_name, [lines])] for human-readable output."""
    blocks = []
    task = None
    play = None
    for raw in text.splitlines():
        line = ANSI.sub("", raw)
        m = BANNER.match(line)
        if m and (m.group("label") is not None or "*" in line):
            kind = m.group("kind")
            if kind == "PLAY":
                play = m.group("label") or ""
                task = None
                continue
            if kind == "TASK":
                task = m.group("label") or ""
                blocks.append([task, play, []])
                continue
            # SECTION / META / summary banners close the current task.
            task = None
            continue
        if SUMMARY.match(line):
            task = None
            continue
        if task is not None:
            blocks[-1][2].append(line)
    return blocks


def blocks_from_events(events):
    """Return [(task_name, play_name, [lines])] for JSON event logs.

    Handles both `-j` events (`task` + `hostname` + `msg` on every event) and
    `--output-format json` events (`task_name` on TASK log events, `stdout`/
    `stderr`/`result` events carrying `host` + `line`). A new block starts when
    the task name changes, so two back-to-back tasks sharing a name merge.
    """
    blocks = []
    play = None
    for ev in events:
        action = ev.get("action") or ev.get("object_type")
        name = ev.get("task") or ev.get("task_name")
        if action in ("play", "PLAY") or ev.get("play") or ev.get("playbook_file"):
            play = ev.get("play") or ev.get("play_name") or ev.get("playbook_file") or play
            continue
        if action in ("summary", "recap", "success"):
            continue
        if name and (not blocks or blocks[-1][0] != name):
            blocks.append([name, play or "", []])
            continue
        line = ev.get("line") or ev.get("msg") or ""
        if isinstance(line, (dict, list)):
            line = json.dumps(line)
        host = ev.get("host") or ev.get("hostname")
        if blocks and line:
            blocks[-1][2].append(f"[{host}]: {line}" if host else line)
    return blocks


def main():
    ap = argparse.ArgumentParser(
        description="Filter ansible playbook logs by partial task name.",
        add_help=True,
    )
    ap.add_argument("pattern", nargs="+", help="partial task name (or regex with --regex)")
    ap.add_argument("-f", "--file", action="append", default=[], metavar="LOGFILE",
                    help="log file to read; repeatable, default stdin")
    ap.add_argument("--regex", action="store_true", help="match task names as regexes")
    ap.add_argument("--list", action="store_true", help="list task names and stop")
    ap.add_argument("--invert", action="store_true", help="print blocks that match no pattern")
    ap.add_argument(
        "--also-match-output",
        action="store_true",
        help="also select blocks whose output text contains a pattern",
    )
    ap.add_argument("--show-play", action="store_true", help="prefix blocks with their PLAY name")
    ap.add_argument("--json", action="store_true", help="print matches as JSON instead of text")
    args = ap.parse_args()
    def parse(source):
        head = source.lstrip()
        if head.startswith("{"):
            try:
                data = json.loads(head)
            except ValueError:
                sys.exit("input starts with '{' but is not valid JSON")
            return blocks_from_events(data.get("events", []))
        return blocks_from_text(source)

    sources = [open(f, encoding="utf-8", errors="replace").read() for f in args.file]
    if not sources:
        sources = [sys.stdin.read()]
    blocks = trim([b for source in sources for b in parse(source)])

    def matches(task, body):
        hay = "\n".join(body)
        for p in args.pattern:
            if args.regex:
                try:
                    hit = re.search(p, task, re.IGNORECASE) is not None
                    if not hit and args.also_match_output:
                        hit = re.search(p, hay, re.IGNORECASE) is not None
                except re.error as exc:
                    sys.exit(f"bad pattern {p!r}: {exc}")
            else:
                hit = p.lower() in task.lower()
                if not hit and args.also_match_output:
                    hit = p.lower() in hay.lower()
            if hit:
                return True
        return False

    if args.list:
        for task, play, body in blocks:
            print(f"{task}\t{len(body)}")
        sys.exit(0)

    selected = [b for b in blocks if matches(b[0], b[2]) != args.invert]
    if args.json:
        print(json.dumps(
            [{"play": p, "task": t, "lines": body} for t, p, body in selected], indent=2
        ))
    else:
        for task, play, body in selected:
            if args.show_play and play:
                print(f"PLAY [{play}] " + "*" * 40)
            head = f"TASK [{task}] "
            print(head + "*" * max(4, 79 - len(head)))
            if body:
                print("\n".join(body))
            print()
    sys.exit(0 if selected else 1)


if __name__ == "__main__":
    main()
