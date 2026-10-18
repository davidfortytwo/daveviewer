#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daveviewer -- NAT traversal probe.

WHAT THIS TOOL DOES NOT DO
--------------------------
It does not implement Remote Desktop. It does not speak RDP, it has no TURN
relay client, and it does not perform UDP hole punching.

The previous version of this script claimed otherwise. use_turn() returned True
after printing "Connecting to TURN server turn_server_ip_here:3478" without ever
opening a socket. use_hole_punching() returned True after

    udp_socket.sendto(b"Hello", ("peer_ip_here", 12345))

which is a UDP datagram aimed at a host name that does not exist. The caller
then printed "Hole punching succeeded." and "Proceeding with connection.", so
the script reported success for work it had never done.

What it actually does is a STUN probe: it asks a STUN server which public
IP:port the local host is seen as, the first step of any NAT traversal
workflow. That part is real, it is kept, and it is configurable. TURN and hole
punching now raise NotImplementedError instead of pretending to succeed.
"""

import argparse
import os
import sys

# The public Google STUN server. It is a default, not a hardcoded destination:
# override with --stun-host / --stun-port or the environment variables below.
DEFAULT_STUN_HOST = "stun.l.google.com"
DEFAULT_STUN_PORT = 19302

STUN_HOST_ENV = "DAVIEWER_STUN_HOST"
STUN_PORT_ENV = "DAVIEWER_STUN_PORT"

NOT_IMPLEMENTED = (
    "NOT IMPLEMENTED. This repository has no {what} client. The previous "
    "version of this script printed a success message here without doing any "
    "work. See README.md."
)


def resolve_stun_server(host=None, port=None):
    """Precedence: explicit argument, then environment, then default."""
    if host is None:
        host = os.environ.get(STUN_HOST_ENV) or DEFAULT_STUN_HOST
    if port is None:
        port = int(os.environ.get(STUN_PORT_ENV, DEFAULT_STUN_PORT))
    return host, port


def use_stun(host=None, port=None):
    """Ask a STUN server for our public IP:port. This part is real."""
    host, port = resolve_stun_server(host, port)

    try:
        import stun
    except ImportError as exc:
        raise SystemExit(
            "[!] The 'stun' package is required: pip install -r requirements.txt"
        ) from exc

    print(f"[STUN] querying {host}:{port}")
    nat_type, external_ip, external_port = stun.get_ip_info(
        stun_host=host, stun_port=port
    )
    if not external_ip:
        print("[STUN] No external address returned by the server.")
        return False

    print(f"[STUN] NAT Type: {nat_type}")
    print(f"[STUN] External IP: {external_ip}")
    print(f"[STUN] External Port: {external_port}")
    return True


def use_turn(host=None, port=3478):
    """Not implemented. Reported as such instead of returning a fake success."""
    raise NotImplementedError(NOT_IMPLEMENTED.format(what="TURN relay"))


def use_hole_punching(peer=None, peer_port=12345):
    """Not implemented. Reported as such instead of returning a fake success."""
    raise NotImplementedError(NOT_IMPLEMENTED.format(what="UDP hole punching"))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Probe NAT mapping with STUN. This tool does not implement "
                    "Remote Desktop; see README.md.")
    parser.add_argument("--stun-host", default=None,
                        help=f"STUN server (default: ${STUN_HOST_ENV} or "
                             f"{DEFAULT_STUN_HOST})")
    parser.add_argument("--stun-port", type=int, default=None,
                        help=f"STUN port (default: ${STUN_PORT_ENV} or "
                             f"{DEFAULT_STUN_PORT})")
    parser.add_argument("--probe-only", action="store_true",
                        help="Exit 0 when the STUN probe succeeds. Without this "
                             "flag the tool exits non-zero, because it cannot "
                             "establish the RDP session it is named after.")
    args = parser.parse_args(argv)

    print("daveviewer: NAT traversal probe.")
    print("This tool does NOT implement Remote Desktop (no RDP, no TURN, no "
          "hole punching).")

    try:
        probe_ok = use_stun(args.stun_host, args.stun_port)
    except SystemExit:
        raise
    except Exception as exc:  # network failures must not look like success
        probe_ok = False
        print(f"[STUN] Failed: {exc}")

    for label, call in (("TURN", use_turn), ("Hole Punching", use_hole_punching)):
        try:
            call()
        except NotImplementedError as exc:
            print(f"[{label}] {exc}")

    if probe_ok and args.probe_only:
        print("[=] STUN probe succeeded.")
        return 0

    print("[!] No connection was established. daveviewer implements a STUN "
          "probe only.")
    return 1


if __name__ == "__main__":
    sys.exit(main())