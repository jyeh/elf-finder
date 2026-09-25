#!/usr/bin/env python3
"""Print the Ubuntu amd64 package that ships a shared object.

Reads the archive Contents index only. Does not install anything.
"""

import argparse
import gzip
import sys
import urllib.request
from pathlib import Path

MIRROR = "https://archive.ubuntu.com/ubuntu"
TRIPLET = "x86_64-linux-gnu"
SKIP_SUFFIX = ("-dev", "-dbg", "-dbgsym", "-cross")


def cache_path(suite: str) -> Path:
    base = Path.home() / ".cache" / "elf-finder"
    return base / f"{suite}-Contents-amd64.gz"


def contents_url(suite: str) -> str:
    return f"{MIRROR}/dists/{suite}/Contents-amd64.gz"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            with tmp.open("wb") as out:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
        tmp.replace(dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def ensure_contents(suite: str) -> Path:
    path = cache_path(suite)
    if path.is_file() and path.stat().st_size > 0:
        return path
    url = contents_url(suite)
    print(f"downloading {url}", file=sys.stderr)
    download(url, path)
    return path


def candidate_paths(soname: str) -> dict[str, int]:
    return {
        f"usr/lib/{TRIPLET}/{soname}": 0,
        f"lib/{TRIPLET}/{soname}": 1,
    }


def runtime_names(names: list[str]) -> list[str]:
    runtime = [
        name for name in names
        if not name.endswith(SKIP_SUFFIX)
    ]
    return runtime or names


def packages_for(contents: Path, soname: str) -> list[str]:
    ranks = candidate_paths(soname)
    best = 99
    found: list[str] = []
    seen: set[str] = set()
    with gzip.open(contents, "rt", errors="replace") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) != 2:
                continue
            rank = ranks.get(parts[0])
            if rank is None or rank > best:
                continue
            if rank < best:
                best = rank
                found = []
                seen = set()
            for item in parts[1].split(","):
                name = item.rsplit("/", 1)[-1]
                if not name or name in seen:
                    continue
                seen.add(name)
                found.append(name)
    return runtime_names(found)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print the Ubuntu amd64 package that ships "
            "a shared object. Does not install it."
        ),
    )
    parser.add_argument(
        "soname",
        help='Library file name, e.g. "libgomp.so.1"',
    )
    parser.add_argument(
        "--suite",
        default="noble",
        help="Ubuntu suite whose Contents index to read",
    )
    args = parser.parse_args()
    soname = args.soname.strip()
    if not soname or "/" in soname:
        print(
            "pass a library file name, not a path",
            file=sys.stderr,
        )
        return 2
    try:
        contents = ensure_contents(args.suite)
        pkgs = packages_for(contents, soname)
    except OSError as err:
        print(err, file=sys.stderr)
        return 1
    if not pkgs:
        where = f"usr/lib/{TRIPLET}/{soname}"
        print(
            f"no amd64 package in {args.suite} ships {where}",
            file=sys.stderr,
        )
        return 1
    for pkg in pkgs:
        print(pkg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
