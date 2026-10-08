#!/usr/bin/env python3
"""True when a uname -r string is an Ubuntu 22.04, 24.04, or 26.04 kernel.

The kernel must be an x86 or x86-64 flavour, or kvm. The string
is <version>-<abi>-<flavour>, for example 5.15.0-91-kvm or
6.8.0-45-generic. Kernels from interim releases are left out:
5.19 (22.10), 6.2 (23.04), 6.5 (23.10), 6.11 (24.10),
6.14 (25.04), 6.17 (25.10), and 7.3 (26.10).
"""


def is_ubuntu_kernel(release):
    """Return True when release is an Ubuntu 22/24/26 x86 or kvm kernel.

    release is the uname -r string. Interim-release kernels
    are rejected.
    """
    import re

    if not isinstance(release, str):
        return False
    # LTS kernels only. Interim GA versions are omitted:
    # 5.19, 6.2, 6.5, 6.11, 6.14, 6.17, 7.3.
    versions = {
        "22.04": {
            (5, 15), (5, 17), (6, 0), (6, 1), (6, 8),
        },
        "24.04": {(6, 8), (6, 10), (7, 0)},
        "26.04": {(7, 0), (7, 2)},
    }
    # amd64 flavours. kvm is 22.04 only. 64k-page flavours
    # are arm64-only and are left out.
    flavours = {
        "22.04": {
            "aws", "aws-fips", "azure", "azure-fde", "azure-fips",
            "fips", "gcp", "gcp-fips", "gcp-tcpx", "generic",
            "gke", "gkeop", "ibm", "ibm-gt", "ibm-gt-fips",
            "ibm-gt-opt", "intel-iot-realtime", "intel-iotg",
            "iot", "kvm", "lowlatency", "nvidia", "oem", "oracle",
            "realtime", "vmware",
        },
        "24.04": {
            "aws", "aws-fips", "azure", "azure-fde", "azure-fips",
            "fips", "gcp", "gcp-fips", "generic", "gke", "gkeop",
            "ibm", "ibm-gt", "ibm-gt-tdx", "intel", "iot",
            "lowlatency", "nvidia", "nvidia-bos",
            "nvidia-lowlatency", "oem", "oracle", "realtime",
            "vmware",
        },
        "26.04": {
            "amd-embedded", "aws", "aws-fips", "azure",
            "azure-fde", "fips", "gcp", "gcp-fips", "generic",
            "gke", "ibm", "ibm-gt", "intel", "iot", "nvidia",
            "nvidia-bos", "oem", "oracle", "realtime", "vmware",
        },
    }
    match = re.compile(
        r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
        r"-(?P<abi>\d+)-"
        r"(?P<flavour>[a-z0-9]+(?:-[a-z0-9]+)*)$"
    ).match(release)
    if match is None:
        return False
    abi = match.group("abi")
    if abi.startswith("0") or not 1 <= len(abi) <= 5:
        return False
    base = (int(match.group("major")), int(match.group("minor")))
    flavour = match.group("flavour")
    for rel, allowed in versions.items():
        if base in allowed and flavour in flavours[rel]:
            return True
    return False


if __name__ == "__main__":
    import os
    import sys

    text = sys.argv[1] if len(sys.argv) > 1 else os.uname().release
    print("yes" if is_ubuntu_kernel(text) else "no")
