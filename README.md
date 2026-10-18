# daveviewer

A NAT traversal probe, and nothing more.

## Read this before using it

**This tool does not implement Remote Desktop.** Despite the repository
description, there is no RDP client here, and there never was. The previous
version of `daveviewer.py` reported success for work it never performed:

* `use_turn()` printed `Connecting to TURN server turn_server_ip_here:3478`
  and returned `True` without opening a socket.
* `use_hole_punching()` sent `b"Hello"` to the host name `peer_ip_here` on port
  12345, then printed `Hole punching successfully.` and returned `True`.

The caller then printed `Proceeding with connection.`, so an operator running
this script was told a remote desktop connection had been established when no
connection of any kind existed.

Those two functions now raise `NotImplementedError` and say so.

## What it actually does

A STUN probe: it asks a STUN server which public IP:port the local host is
seen as. That is the first step of any NAT traversal workflow, and it is
implemented for real.

The `stun.l.google.com:19302` public server is a **default, not a hardcoded
destination**. Override it per run or per environment:

| Setting | Flag | Environment variable |
| --- | --- | --- |
| STUN host | `--stun-host` | `DAVIEWER_STUN_HOST` |
| STUN port | `--stun-port` | `DAVIEWER_STUN_PORT` |

Precedence is: explicit flag, then environment variable, then default.

## Install

```
pip install -r requirements.txt
```

## Usage

```
python daveviewer.py --probe-only
python daveviewer.py --stun-host stun.example.org --stun-port 3478
DAVIEWER_STUN_HOST=stun.example.org python daveviewer.py --probe-only
```

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | STUN probe succeeded **and** `--probe-only` was given |
| `1` | No connection established (always the case without `--probe-only`) |

Without `--probe-only` the tool exits non-zero on purpose: it cannot establish
the RDP session it is named after, and it should not imply that it did.

## Tests

```
python -m pytest tests -q
```

The tests need no network and no STUN server; the STUN call is stubbed.

## If you want to finish this

The two missing pieces are a TURN relay client (RFC 5766: Allocate, CreatePermission,
CreateChannel over a relayed transport address) and a real rendezvous for UDP
hole punching. Neither is a stub, and neither is in this repository.