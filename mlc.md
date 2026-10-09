# Intel Memory Latency Checker (MLC) — cited brief

Local copy verified on this box: `~/Downloads/mlc_v3.13.tgz`, 1,355,592 B,
`sha256sum` = `a8537e8ff3fad626d75a383fabc224ccc4cc98a0111c9989f7fb26b639f12019`,
which matches the SHA256 Intel publishes on its download page. (The requested
`~/Download` does not exist; the existing `~/Downloads` was used.)

## 1. What it is and what it measures

Intel MLC is a **binary-only** memory-latency/bandwidth tool for Linux and Windows:
download ID 736633, current version **3.13**, page dated 8/18/2026, `mlc_v3.13.tgz`,
1.3 MB — <https://www.intel.com/content/www/us/en/download/736633/intel-memory-latency-checker-intel-mlc.html>.

Package contents (local `find`): `Linux/mlc` 363,096 B, `Windows/mlc.exe` 704,904 B,
`Windows/mlcdrv.sys` 22,728 B, `Documentation/readme_mlc_v3.13.rst` 111,190 B
(2,655 lines), plus a corrupt license PDF (see §7).

Purpose (`readme_mlc_v3.13.rst:10-24`): latency/bandwidth of the cache hierarchy and
memory subsystem, and how they change with increasing load; on NUMA systems local vs
cross-socket latencies differ significantly.

A no-argument run measures five things (`readme:122-192`):

1. socket→socket idle-latency matrix
2. peak injection bandwidth at varying read/write ratios (local accesses only)
3. socket→socket bandwidth matrix
4. latencies at different bandwidth points
5. latencies between caches

Methodology (`readme:192-358`), which determines how the numbers are read:

- **Idle latency** = dependent loads (pointer chase); the buffer is built so each
  64-byte line points at another line; a timer over millions of loads yields the
  **average** time per load. Per-load latency histograms exist only from v3.10
  (`readme:208-210`).
- Cache level is inferred **only from buffer size**: "if L2 is 1MB and L3 is 30MB,
  4MB buffer = L3 hit; 60MB = memory" (`readme:212-219`). MLC "does not know whether
  a load is hitting in any caches or going to memory."
- **Bandwidth** = loads whose results are never consumed, one software thread per
  logical CPU, no hardware performance counters read — MLC computes b/w from its own
  load/store count (`readme:237-258`).
- **Loaded latency** = (logical CPUs − 1) bandwidth-generation threads + 1 latency
  thread, normally on cpu#0; bandwidth threads inject delays every few seconds to
  sweep load levels (`readme:276-298`). Prefetchers stay **enabled** on bandwidth
  threads, disabled on the latency thread. **Reported bandwidth includes the
  latency thread's own traffic** (`readme:296-297`).

## 2. Modes and flags (v3.13, from local `./mlc --help`)

| Mode | What it measures |
|---|---|
| `--idle_latency` | dependent-load (pointer-chase) latency, one thread |
| `--loaded_latency` | latency at injected bandwidth levels |
| `--latency_matrix` | socket→socket idle-latency matrix |
| `--bandwidth_matrix` | socket→socket bandwidth matrix |
| `--peak_injection_bandwidth` | peak b/w at varying read/write ratios (local accesses only) |
| `--c2c_latency` | core→core latency |
| `--c2c_bandwidth` | core→core bandwidth |
| `--concurrent_bandwidth` | concurrent bandwidth |
| `--delay_pointer_chase` | pointer chase with delays |
| `--c2c_readerbw_matrix` | reader-bandwidth matrix |
| `--memory_bandwidth_scan` | bandwidth scan |
| `--max_bandwidth` | appears only in the per-mode flag lines, not the mode list |

Help text still says "there are six modes" — stale. `--peak_max_bandwidth` appears once
in readme examples (`readme:1075`) but nowhere in `--help`; treat as a doc typo, unverified.

Flags that change results (verbatim glossary, `readme_mlc_v3.13.rst`):

| Flag | Meaning (line) |
|---|---|
| `-b` | buffer size in KiB, default 100000 (≈97.7 MB) (`:600`) |
| `-l` | stride in bytes, default 64 (`:650`) |
| `-D` | random-access range for latency thread, default 4096 (`:642`) |
| `-d` | delay cycles between requests, default 0; higher lowers b/w (`:634`) |
| `-f` | latency-histogram bucket = 2^n cycles (`:646`) |
| `-e` | do not modify h/w prefetcher state (`:638`) |
| `-r` | random access, needed when prefetchers can't be disabled (`:632`) |
| `-X` | one thread per core (`:656`) |
| `-a` | idle latencies on all CPUs (`:602`) |
| `-c` / `-i` | affinitize latency thread to core #n / initialize memory from core #n (`:606`,`:668`) |
| `-J` | directory for mmap files on a pmem-mounted fs; **idle_latency only** (`:619`) |
| `-k` / `-m` | CPU list / hex CPU mask for bandwidth threads; mutually exclusive; CPU 0 must be excluded unless `-T` (`:623`,`:658`) |
| `-T` | b/w only, no latency; then the mask may include CPU 0 (`:867`) |
| `-u` | L3 b/w: all threads share one buffer, no clean-line write-back (`:873`) |
| `-U` / `-n` | random access for b/w threads / max random number per block (`:880`,`:676`) |
| `-M` / `-o` | pattern-init file (256 cache lines max) / per-thread control file (`:662`,`:695`) |
| `-g` | input file of delays to inject for loaded latency (`:630`) |
| `-Y` / `-Z` | AVX2 / AVX-512 loads-stores; **default is SSE2 128-bit only** (`:949`,`:954`) |
| `-W` | 2 = 2R:1W, 3 = 3R:1W, 5 = 1R:1W, 6 = 100% non-temporal write (`:1341-1345`) |
| `-L` / `-h` | allocate via hugetlbfs / 1GB pages (Windows DAX only) (`:654`,`:612`) |

## 3. Command lines people actually run

| Source | Command(s) |
|---|---|
| Intel readme pmem example (`readme:1271-1276`) | `mount -o dax /dev/pmem0 /mnt/pmem0` then `mlc --idle_latency -c0 -J/mnt/pmem0` |
| Intel readme b/w ratios (`readme:1329-1345`) | `mlc --bandwidth_matrix -W3` |
| Intel support article 000055898, "How to Test the Performance of Intel® Optane™ Persistent Memory", last reviewed 03/04/2025 — <https://www.intel.com/content/www/us/en/support/articles/000055898/management-and-tools.html> | `mlc -latency_matrix`, `-bandwidth_matrix`, `-peak_injection_bandwidth`, `-loaded_latency` run individually; App Direct mode requires **devdax** (`/dev/daxN.M`), and "to test fsdax, sector, or raw, a higher-level benchmark utility such as Flexible I/O Tester (FIO) should be used" |
| Phoronix Test Suite profile `pts/intel-mlc-1.2.0` (10 Sep 2025, "Update against MLC 3.11b") — <https://mail.openbenchmarking.org/test/pts/intel-mlc> and innhold <https://mail.openbenchmarking.org/innhold/840904cbf104079f8c4477b57482847d54d2acac> | `-X --peak_injection_bandwidth`, `-X --max_bandwidth`, `--idle_latency`; `install.sh` appends `-Z` when `grep avx512 /proc/cpuinfo`; `pre.sh` does `echo 4000 > /proc/sys/vm/nr_hugepages`, `post.sh` restores the old value |
| MemVerge `pmts-mlc` (fsdax pmem) — <https://github.com/MemVerge/pmts/blob/master/README-mlc.md>, script <https://raw.githubusercontent.com/MemVerge/pmts/master/pmts-mlc.sh> | `--idle_latency -c<FIRST_CPU_ON_SOCKET> -J<PMEM_PATH>`; `--idle_latency -c… -l256 -J<PMEM_PATH>` (random); `--loaded_latency -d0 -o<per-thread file> -t<SAMPLE_TIME> -T <Z>`; `--loaded_latency -g<DELAYS_FILE> -o… -t…` and the same with `-r`; driver form `sudo pmts-mlc -s 1 -p /pmemfs0` |
| <https://github.com/Purestreams/linux-mlc-bench> (MIT, MLC v3.12) | AIDA64-style sweep: `--idle_latency` with fixed buffers L1=16K, L2=512K, L3=6M, DRAM=256M; sample output on AMD EPYC 7532 (32C/64T, DDR4-2667): DRAM 132.3 GB/s read / 124.9 write / 128.1 copy; L1 2795.4, L2 1819.6, L3 131.6 GB/s; latencies L1 1.2 ns, L2 6.6, L3 13.4, DRAM 130.9 ns; 3m14s |
| Community "How to run the Intel MLC" — <https://community.intel.com/t5/Software-Tuning-Performance/How-to-run-the-Intel-MLC/td-p/1151750> | Intel employee Krishnaswa_V_Intel: "You can run MLC as ./mlc without any arguments…"; McCalpinJohn: binaries live in the `Linux`/`Windows` subdirs after un-tar, and "it needs to be run by the root user to get reliable latency measurements" |
| Community "Memory bandwidth on a NUMA system" — <https://community.intel.com/t5/Software-Tuning-Performance/Memory-bandwidth-on-a-NUMA-system/td-p/1095836> | Intel employee explains MLC's remote-socket measurement method; McCalpin critiques it and posts STREAM commands alongside MLC output (v3.0) |
| Community "Intel Memory Latency Checker v3.5 test" — <https://community.intel.com/t5/Software-Tuning-Performance/Intel-Memory-Latency-Checker-v3-5-test/m-p/1164437> | OEM test criteria + an `-X`/`-Y`/`-Z` sweep and a `perf stat` `uncore_imc` cross-check |
| Community "Measurement Results are Different in Different NUMA Nodes" — <https://community.intel.com/t5/Software-Tuning-Performance/Intel-Memory-Latency-Checker-Measurement-Results-are-Different-in-Different-NUMA-Nodes/m-p/1579149> (2,573 views, **0 replies**) | bash sweeps using `numactl`/CPU masks; asymmetry question unanswered |
| <https://github.com/wenhuizhang/MLC> ("mirror of MLC") | SMT comparison: `cat /sys/devices/system/cpu/smt/active`, `echo off > /sys/devices/system/cpu/smt/control`, full v3.9a output pasted for SMT on/off |
| Medium deep dive (Zhiwei Chen, 14 Jan 2024) — <https://medium.com/@wrightchen/intel-memory-latency-checker-mlc-for-cache-testing-deep-dive-b8b2c30bacab> | per-cache-level bandwidth/latency commands and a `-K0` experiment |

## 4. Who uses it and why

- **Server/OEM validation**: Intel's own community guidance and OEM criteria (thread
  1164437) use MLC to certify platform memory performance; Intel's Optane/pmem
  support article (000055898) prescribes MLC for App Direct/devdax bandwidth and
  latency.
- **Persistent-memory tooling**: MemVerge `pmts-mlc` wraps MLC for fsdax profiles
  (`README-mlc.md`).
- **Academic memory-system characterization**: "Systematic CXL Memory
  Characterization and Performance Analysis at Scale" (ASPLOS '25,
  <https://par.nsf.gov/servlets/purl/10614558> — local `/tmp/cxl.txt`, MLC evidence at
  lines 189-192, 259-262, 276-283; ref [6] is the Intel download URL) uses MLC to
  characterize CXL memory; "A Mess of Memory System Benchmarking, Simulation and
  Application Profiling" (MICRO 2024 runner-up, <https://arxiv.org/html/2405.10170v1>)
  compares MLC against its own `Mess` tooling across platforms.
- **Consumer/enthusiast benchmarking**: PTS `intel-mlc` (40k+ downloads, avg run 2m59s,
  in the "AVX-512 Capable Tests" and "Synthetic Benchmarks" suites),
  `linux-mlc-bench` reproducing AIDA64-style cache numbers on AMD EPYC.
- **Kernel/hardware review**: NUMA asymmetry and BIOS interleave/snooping validation
  questions on Intel community.

## 5. Interpretation pitfalls

1. **Huge-pages gate (v3.13)**: on this box (`AMD Ryzen 7 5700G`, 16 CPUs, 1 NUMA node,
   `HugePages_Total: 0`, `Hugepagesize: 2048 kB`) every mode run —
   `./mlc --idle_latency -e -r -c0 -b262144 -t2`, `./mlc --bandwidth_matrix -e -X`,
   `./mlc --bandwidth_matrix -e -X -b16384` — printed **only the huge-pages refusal,
   no numbers**. No measurement was produced here; do not read this machine as a source
   of MLC data. PTS works around it by setting `nr_hugepages` to 4000 in `pre.sh` and
   restoring in `post.sh` (innhold above). Fixing it needs a privileged write to
   `/proc/sys/vm/nr_hugepages`; `sudo` on this box requires a password, so it needs
   explicit authorization.
2. **SSE2 default**: `-Y`/`-Z` are required for AVX2/AVX-512 traffic; "By default, only
   SSE2 (128-bit loads/stores) instructions are used" (`readme:949-962`). Un-flagged
   bandwidth numbers are routinely low; PTS auto-adds `-Z` on AVX512 CPUs.
3. **Root + MSR side effects**: MLC "modifies the H/W prefetch control MSR" and needs
   root on Linux; MSR driver via `modprobe msr` (`readme:69-77`, `:102-120`). `-e` skips
   prefetcher mutation (and thus changes latency semantics); on Windows from v3.10 the
   driver is not used by default and latency tests fall back to random accesses; `-e0`
   forces the driver.
4. **Average-only latency** unless `-f` histogram (v3.10+): no p99/tail visibility
   (`readme:208-210`).
5. **RFO accounting is an estimate**: a store = 1 read + 1 write at the memory
   controller; "this is an estimation… MLC does not have any visibility into the
   functioning of the memory controller" (`readme:259-274`); `-K` controls partial-line
   /full-line access accounting (`readme:628-650`).
6. **Reported b/w includes the latency thread** (`readme:296-297`).
7. **Buffer sizing rules**: ≥100 MB per thread for DRAM b/w, and per-socket total must
   exceed that socket's LLC (`readme:252-257`); default `-b` is 100000 KiB.
8. **`-u` changes traffic type** (shared buffer, no clean-line write-back) for L3 b/w
   (`readme:873-878`).
9. **CPU 0 exclusion rule** for `-m`/`-k` unless `-T`; the HT sibling of core 0 must
   also be omitted (`readme:658-672`).
10. **NUMA asymmetry** is expected and explained by Intel employees (threads
    1095836, 1579149).
11. **pmem mode mismatch**: MLC's default tests DRAM/Memory-Mode only; App Direct needs
    devdax; fsdax numbers are nonsense — Intel's own article documents a ~1.9 TB/s
    "max read bandwidth" against a ~240 GB/s theoretical max for 12 channels, and tells
    you to use FIO for fsdax/sector/raw.
12. **Non-Intel hardware**: MLC runs on AMD (this box executed it; `linux-mlc-bench`
    reports full cache numbers on EPYC 7532), but the prefetcher-disabling MSR path is
    Intel-specific — `[INFERENCE]` on AMD, latency numbers depend on `-r` random access
    rather than prefetcher suppression.
13. **Doc/help inconsistencies**: help says "six modes" but lists 12;
    `--peak_max_bandwidth` in readme examples is absent from `--help`.
14. **SMT changes latency** (wenhuizhang/MLC v3.9a output with `smt/control` toggled).

## 6. Wrappers and alternatives

Wrappers: MemVerge `pmts-mlc` (fsdax pmem profiles),
`Purestreams/linux-mlc-bench` (MIT, AIDA64-style, auto-downloads MLC to
`/tmp/mlc_bench_<PID>`), PTS `pts/intel-mlc` (maintainer Michael Larabel),
`wenhuizhang/MLC` mirror.

Alternatives: **multichase** (<https://github.com/google/multichase>, Apache-2.0, 163
stars, created 2015-12-11; PTS test `multichase` "Multichase Pointer Chaser") for pure
pointer-chase latency; **STREAM** (McCalpin) for triad bandwidth — McCalpin's critique of
MLC's b/w methodology is in thread 1095836; `perf stat -e uncore_imc*` for counter-based
cross-checks (thread 1164437); FIO for fsdax/sector/raw (Intel article 000055898).
`mbw` fetch from <https://hydra.nj.org/mbw/> returned empty — unverified.

## 7. License caveats

- **Binary-only, no source release.** PTS marks the profile
  `<License>Non-Free</License>` (innhold above). GitHub "mirrors" (wenhuizhang/MLC,
  language "Other") are not official source.
- `redist.txt` (local, verbatim): Linux lists `mlc_internal`, Windows lists
  `mlc_internal.exe` + `mlcdrv.sys`, "subject to the terms and conditions of the End
  User License Agreement".
- readme appendix (`readme:2244-2320`): MLC "uses code from Intel® Power Governor" and
  "from Intel® Performance Counter Monitor", both BSD (Copyright 2009-2013 Intel), plus
  "sample code from MSDN website".
- **The shipped EULA file is corrupt**: `~/Downloads/mlc/"Intel Memory Latency Tools
  Outbound License Agreement.pdf"` is `file`-identified as gzip data; `gzip -dc` yields a
  POSIX tar of the **v3.11** package (`Linux/mlc` 199,728 B, `readme_mlc_v3.11.pdf`
  656,863 B dated 2023-11-07). So v3.13's actual EULA text is not readable from the
  tarball.
- The **older standalone EULA**
  (<https://github.com/PersistentMemory/mlc-v3.9a/blob/main/mlc_tool_license.txt>,
  "SOFTWARE TOOLS LICENSE AGREEMENT" §3 restriction (v)) forbids "publish or provide any
  Materials benchmark or comparison test results". Greps for
  `comparison test|publish or provide|benchmark` hit **nothing** in
  `readme_mlc_v3.13.rst` or in the pdftotext of the salvaged v3.11 readme — `[INFERENCE]`
  the clause may still be in the unreadable v3.13 EULA; treat publishing MLC results as
  restricted until Intel's current EULA is confirmed.

## 8. Local commands (this box, 2026-10-09)

Binary `~/Downloads/mlc/Linux/mlc`, v3.13. `--help` prints with
`nr_hugepages` at 0. A measurement does not.

With `HugePages_Total` at 32, this command exited 22 and printed no
latency:

`sudo ~/Downloads/mlc/Linux/mlc --idle_latency -e -r -c0 -i0 -b2048 -t1 -L`

The refusal text was: at least 1000 2 MB pages per NUMA node, plus the
sample line `echo 4000 > /proc/sys/vm/nr_hugepages`. The count was
restored to 0 after the probe. One NUMA node, so the floor is 1000 pages
(2 GB). `MemAvailable` during the probe was 2,248,256 kB. 4000 pages is
8 GB. `sudo -n true` succeeded in that same check.

`lscpu`: AMD Ryzen 7 5700G, 8 cores / 16 threads, one socket. Caches:
L1d 32 KiB per core (256 KiB across 8), L2 512 KiB per core (4 MiB
across 8), L3 16 MiB in one instance. `/proc/cpuinfo` includes `avx2`
and has no `avx512f`.

A 2 MB hugepage is already larger than L1 and L2, so those levels are
not what a hugepage buffer measures. `-b8192` (8 MB) sits between L2 and
the 16 MB L3. `-b32768` (32 MB) is past the L3.

Peak and max bandwidth allocate a read buffer and a write buffer. At the
default `-b` of 100000 KiB, 16 threads × 2 buffers is about 3.1 GB, past
the 1000-page pool. `-X` keeps one thread per core (8). The default
bandwidth matrix is 100% reads, so that mode stays inside 2 GB with or
without `-X`. `-e` leaves prefetchers alone. `-r` is the random latency
walk. `-Y` is AVX2.

The block below is sized from that gate. It has not been run through to
a number. `HugePages_Total` has to read 1000 before the `mlc` lines. The
`trap` puts the old count back when the shell exits.

```bash
MLC=/home/jasonyeh/Downloads/mlc/Linux/mlc
old=$(cat /proc/sys/vm/nr_hugepages)
restore() {
  sudo sh -c "echo $old > /proc/sys/vm/nr_hugepages"
}
trap restore EXIT

sudo sh -c 'echo 1000 > /proc/sys/vm/nr_hugepages'
grep HugePages_ /proc/meminfo
# If Total is short of 1000, compact and write it again:
# sudo sh -c 'echo 1 > /proc/sys/vm/compact_memory'
# sudo sh -c 'echo 1000 > /proc/sys/vm/nr_hugepages'

# L3: 8 MB is above L2 and below the 16 MB L3
sudo "$MLC" --idle_latency -e -r -c0 -i0 -b8192 -t2 -L

# DRAM: 32 MB is above the L3
sudo "$MLC" --idle_latency -e -r -c0 -i0 -b32768 -t2 -L

# 1x1 socket matrix on this single-node box
sudo "$MLC" --latency_matrix -e -r -b32768 -t2 -L

# 100% reads, one thread per core. Default 100 MB buffer.
sudo "$MLC" --bandwidth_matrix -e -Y -X -t2 -L

# Read/write ratios. -X keeps the double buffer inside 2 GB.
sudo "$MLC" --peak_injection_bandwidth -e -Y -X -t2 -L

# Same footprint as peak. Sweeps injection delay.
sudo "$MLC" --max_bandwidth -e -Y -X -t2 -L

# Latency under load. Default delay list is ~40 s at -t2.
sudo "$MLC" --loaded_latency -e -r -Y -X -t2 -L
```

## 9. Extra knobs (same gate as §8, 2026-10-09)

Same preamble as §8: 1000 pages, `trap` restore, `sudo` per run. These
variants are not in §8. Sizing follows §8's gate only where the buffer
count is known; lines marked unverified have not been footprint-checked.

```bash
# Latency histogram, buckets = 2^10 cycles (v3.10+; §5 pitfall 4)
sudo "$MLC" --idle_latency -e -r -c0 -i0 -b32768 -t2 -L -f10

# Read/write ratios on the matrix (-W3 = 3R:1W, -W6 = 100%
# non-temporal writes; readme:1329-1345)
sudo "$MLC" --bandwidth_matrix -e -Y -X -t2 -L -W3
sudo "$MLC" --bandwidth_matrix -e -Y -X -t2 -L -W6

# L3 bandwidth: one shared buffer, no clean-line write-back
# (-u changes traffic type, readme:873-878)
sudo "$MLC" --bandwidth_matrix -e -Y -X -t2 -L -u -b8192

# Core-to-core on the 8 cores. Bandwidth form is 8 threads x 2
# buffers x 100 MB = 1.6 GB, inside the 2 GB pool; the latency
# form's footprint is unverified.
sudo "$MLC" --c2c_latency -e -r -t2 -L
sudo "$MLC" --c2c_bandwidth -e -Y -X -t2 -L
```

Corrections to the chat block this section replaces: `4000` pages
exceeds `MemAvailable` (2,248,256 kB) so it cannot allocate here —
§8's 1000-page floor is the working value. L3 is 16 MiB per §8's
`lscpu`, so a 24 MB buffer is past L3, not an L3 hit. With `-L`,
allocation is in 2 MB pages, so `-b16`/`-b512` L1/L2 sweeps are not
measurable this way; §5 pitfall 12's `-r` random walk is the AMD
path instead.

## sample 1
"""Initial Shaker draft for Intel Memory Latency Checker 3.13.

Linux only. The binary is the upstream tarball's Linux/mlc.
Cache-to-cache modes and --memory_bandwidth_scan are omitted:
the scan tries to allocate every byte on a NUMA node.
"""

import math
import os

import shaker_test


class mlcTest(shaker_test.shakerTest):
    def __init__(self, **kwargs):
        super().__init__(simple_tar_install="mlc", **kwargs)
        # Printed by every mode once a measurement starts. The
        # hugepage refusal does not contain it.
        self.pass_str = "Measuring "
        self.fail_str = (
            "Hugepages need to be allocated"
            "|Buffer allocation failed"
            "|insufficient large pages"
            "|Checksum mismatch"
            "|Exiting"
            "|exiting"
            "|Killed"
        )

        self.parameters["category"] = ["MLC"]
        self.parameters["variant"] = ["v3.13"]
        self.parameters["mode"] = [
            "idle_latency",
            "latency_matrix",
            "bandwidth_matrix",
            "peak_injection_bandwidth",
            "max_bandwidth",
            "loaded_latency",
        ]
        # v3.13 defaults to SSE2 128-bit loads. -Y/-Z are refused
        # by the picker when the CPU lacks the matching flag.
        flags = self._cpu_flags()
        self._avx2 = "avx2" in flags
        self._avx512 = "avx512f" in flags
        isas = ["sse2"]
        if self._avx2:
            isas.append("avx2")
        if self._avx512:
            isas.append("avx512")
        self.parameters["isa"] = isas
        # "one" adds -X (one thread per core). Partial widths
        # cannot combine -X with -k: v3.13 exits on that pair.
        self.parameters["smt"] = ["all", "one"]

        # Readme defaults, in KiB. Latency is one buffer.
        # Peak and max allocate a second buffer for writes.
        self._lat_kib = 200000
        self._bw_kib = 100000
        self._page_kib = 2048
        self._page_margin = 64
        # Seconds per sample point, not the whole run.
        # loaded_latency walks a built-in delay list.
        self._sample_s = 5
        self._nodes = self._numa_nodes()

        self._mlc = os.path.join(
            self.SHAKERROOT, "workloads", "mlc", "Linux", "mlc",
        )
        # Tarball is not published here yet. Member path is
        # Linux/mlc inside mlc_v3.13.tgz.
        self.install_media = [{
            "artifactory":
                "https://ausartifactory.amd.com/artifactory/"
                "HW-Shaker-DEV-LOCAL/...",
        }]

        n = self.num_threads_in_system
        widths = []
        for part in (n // 4, n // 2, n):
            width = max(part, 1)
            if width not in widths:
                widths.append(width)
        self.threads_to_test = widths

    def _cpu_flags(self):
        try:
            with open("/proc/cpuinfo") as fh:
                for line in fh:
                    if line.startswith("flags"):
                        return set(line.split(":", 1)[1].split())
        except OSError:
            return set()
        return set()

    def _numa_nodes(self):
        root = "/sys/devices/system/node"
        try:
            names = os.listdir(root)
        except OSError:
            return 1
        count = 0
        for name in names:
            if name.startswith("node") and name[4:].isdigit():
                count += 1
        return max(count, 1)

    def _accept(self, mode, isa, smt, n):
        if isa == "avx2" and not self._avx2:
            return False
        if isa == "avx512" and not self._avx512:
            return False
        full = n == self.num_threads_in_system
        if mode in ("idle_latency", "latency_matrix"):
            # One latency thread, or one chase per node.
            # ISA flags apply to bandwidth traffic only.
            return isa == "sse2" and smt == "all" and full
        if mode in ("bandwidth_matrix", "loaded_latency"):
            # No -k on the matrix. Loaded latency reserves
            # CPU 0 itself, so a partial -k list is omitted
            # until the sibling-of-core-0 rule is applied.
            return full
        if mode in (
            "peak_injection_bandwidth",
            "max_bandwidth",
        ):
            if smt == "one":
                return full
            return n >= 1
        return False

    def _reserve_bytes(self, mode, n):
        kib = 1024
        if mode == "idle_latency":
            return self._lat_kib * kib
        if mode == "latency_matrix":
            return self._lat_kib * kib * self._nodes
        if mode == "loaded_latency":
            bw = self._bw_kib * kib * n
            return bw + (self._lat_kib * kib)
        if mode == "bandwidth_matrix":
            # Default matrix traffic is 100% reads.
            return self._bw_kib * kib * n
        # Peak and max sweep read/write ratios.
        return self._bw_kib * kib * 2 * n

    def _command(self, mode, isa, smt, n, pages):
        buf = self._bw_kib
        if mode in ("idle_latency", "latency_matrix"):
            buf = self._lat_kib
        args = [
            f'"{self._mlc}"',
            f"--{mode}",
            "-e",
            "-L",
            f"-t{self._sample_s}",
            f"-b{buf}",
        ]
        # -e leaves prefetchers alone. -r keeps the latency
        # thread on random misses instead of a prefetched hit.
        # Bandwidth threads stay sequential either way.
        if mode in (
            "idle_latency",
            "latency_matrix",
            "loaded_latency",
        ):
            args.append("-r")
        if mode == "idle_latency":
            args.extend(["-c0", "-i0"])
        if isa == "avx2":
            args.append("-Y")
        elif isa == "avx512":
            args.append("-Z")
        if smt == "one":
            args.append("-X")
        elif n != self.num_threads_in_system:
            args.extend(["-k", "<THREAD_COMMA>"])

        mlc_cmd = " ".join(args)
        # v3.13 exits before measuring when nr_hugepages is 0.
        # Reserve 2MB pages for this run and put the old count back.
        return (
            "oldhp=$(cat /proc/sys/vm/nr_hugepages); "
            "restore_hp() { echo \"$oldhp\" > "
            "/proc/sys/vm/nr_hugepages; }; "
            "trap restore_hp EXIT; "
            f"echo {pages} > /proc/sys/vm/nr_hugepages || "
            "{ echo \"Hugepages need to be allocated\"; "
            "exit 1; }; "
            f"{mlc_cmd}"
        )

    def get_random_test(self, overrides={}, exclude_params={}):
        num_attempts = 0
        while num_attempts < 1000:
            num_attempts += 1
            job_info = super().get_random_test(
                overrides, exclude_params=exclude_params,
            )
            mode = job_info["mode"]
            isa = job_info["isa"]
            smt = job_info["smt"]
            num_threads = job_info["resources"]["threads"]["qty"]
            if not self._accept(mode, isa, smt, num_threads):
                continue

            total = self._reserve_bytes(mode, num_threads)
            page = self._page_kib * 1024
            pages = math.ceil(total / page) + self._page_margin
            job_info["resources"]["mem"]["qty"] = math.ceil(
                total / num_threads,
            )
            job_info["subtest"] = (
                f"{mode}_{isa}_{smt}_{num_threads}T"
            )
            job_info["name"] = (
                f"mlc_{mode}_{isa}_{smt}_{num_threads}T"
            )
            job_info["cmd"] = self._command(
                mode, isa, smt, num_threads, pages,
            )
            return job_info
        return {}

    def verify_ready_to_run(self):
        """The install is one binary, not one directory per variant."""
        print(f"checking {self._mlc}")
        if os.path.isfile(self._mlc):
            return True
        return False

# Sample 2
import math
import os.path
import shaker_test

# Initial draft: Intel Memory Latency Checker (MLC) v3.13.
# mlc_v3.13.tgz and readme_mlc_v3.13.rst line numbers. Items marked
# TODO-UNVERIFIED must be confirmed on a real run before trusting.

class mlcTest(shaker_test.shakerTest):
    def __init__(self, **kwargs):
        super().__init__(simple_tar_install="mlc_v3.13", **kwargs)
        # MLC prints result tables, no SUCCESSFUL/FAIL banner like NASA.
        # Pass = a results table appeared (units appear in every table).
        # TODO-UNVERIFIED: exact markers; confirm against a real run.
        self.pass_str = "Nanoseconds|MB/s"
        self.fail_str = "FAIL|Killed|Error"

        self.parameters['category'] = ['MLC']
        self.parameters['variant'] = ['v3.13']
        # --help lists 12 modes; this subset runs on a single-socket box.
        # latency_matrix needs >=2 sockets, memory_bandwidth_scan etc.
        self.parameters['mode_opt'] = [
            "idle_latency",
            "loaded_latency",
            "bandwidth_matrix",
            "peak_injection_bandwidth",
            "c2c_latency",
            "c2c_bandwidth",
        ]
        # -b unit is KiB, default 100000 (~97.7 MB). Cache-sweep sizes
        # from linux-mlc-bench: L1 16K, L2 512K, L3 6M, DRAM 256M.
        self.parameters['buffer_opt'] = ["16", "512", "6144", "262144",
                                         "100000"]
        # Default traffic is SSE2 128-bit only (readme:949-962); -Y/-Z
        # raise reported bandwidth. "sse2" means no flag.
        self.parameters['isa_opt'] = ["sse2", "-Y", "-Z"]

        # readme:252-257: DRAM bandwidth needs >=100 MB buffer per thread.
        self._min_bw_buffer_per_thread = 100 * 1024 * 1024

        # Huge-pages gate: MLC refuses to run when HugePages_Total is 0
        # (see ~/git/md/mlc.md §5 pitfall 1). PTS pre.sh works around it:
        #   echo 4000 > /proc/sys/vm/nr_hugepages   (privileged)
        # TODO: privileged pre-step + restore, needs explicit
        # authorization; without it every mode prints only the refusal.
        # TODO: install_media artifactory URL for mlc_v3.13.tgz, same
        # HW-Shaker-DEV-LOCAL tree as nasa.py; fill in real path.

        self.threads_to_test = [self.num_threads_in_system // 4,
                                self.num_threads_in_system // 2,
                                self.num_threads_in_system]

    def get_random_test(self, overrides={}, exclude_params={}):
        num_attempts = 0
        while num_attempts < 1000:
            num_attempts += 1
            job_info = super().get_random_test(
                overrides, exclude_params=exclude_params)
            mode = job_info['mode_opt']
            buffer_kib = int(job_info['buffer_opt'])
            isa = job_info['isa_opt']
            num_threads = job_info['resources']['threads']['qty']

            # -Z/-Y on a CPU without AVX-512/AVX2 is an illegal
            # instruction; PTS gates -Z on grep avx512 /proc/cpuinfo.
            cpuinfo = open("/proc/cpuinfo").read()
            if isa == "-Z" and "avx512" not in cpuinfo:
                continue
            if isa == "-Y" and "avx2" not in cpuinfo:
                continue

            # Latency modes are one-thread pointer chases; the
            # bandwidth modes run one thread per logical CPU by
            # themselves, sized by the taskset affinity mask.
            if mode in ("idle_latency", "c2c_latency"):
                num_threads = 1
                job_info['resources']['threads']['qty'] = 1

            if mode in ("bandwidth_matrix", "peak_injection_bandwidth",
                        "c2c_bandwidth"):
                per_thread = max(buffer_kib * 1024,
                                 self._min_bw_buffer_per_thread)
            else:
                per_thread = buffer_kib * 1024
            job_info['resources']['mem']['qty'] = math.ceil(
                per_thread * num_threads)

            job_info['subtest'] = f"{mode}_{buffer_kib}K"
            job_info['name'] = f"mlc_{mode}_{buffer_kib}K_{num_threads}T"

            exe = f"{self.SHAKERROOT}/workloads/mlc_v3.13/Linux/mlc"
            isa_flag = "" if isa == "sse2" else isa
            # taskset pins the CPUs MLC sees. The tool-native -k/-m CPU
            # masks (readme:623/658) carry a CPU-0 exclusion rule; taskset
            # avoids that trap, so use it for partial widths.
            job_info['cmd'] = (
                f"timeout 3600 taskset -c <THREAD_COMMA> {exe}"
                f" --{mode} {isa_flag} -b{buffer_kib}")
            return job_info
        return {}

    def verify_ready_to_run(self):
        '''Tar layout is Linux/mlc + Windows/mlc.exe; check the Linux
        binary exists before scheduling jobs.'''
        path = os.path.join(self.SHAKERROOT, "workloads", "mlc_v3.13",
                            "Linux", "mlc")
        if not os.path.exists(path):
            return False
        return True
