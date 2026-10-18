"""Regression tests: daveviewer must not report success for work it never did.

Defects in the original daveviewer.py:

  * use_turn() printed "[TURN] Connecting to TURN server turn_server_ip_here:3478"
    and returned True without opening a socket. use_hole_punching() ran
    `udp_socket.sendto(b"Hello", ("peer_ip_here", 12345))` -- a UDP datagram to a
    host name that does not exist -- and returned True. The caller then printed
    "Hole punching successfully." and "Proceeding with connection.", so the
    script claimed a remote desktop connection that was never established.
    The repository description also claims "Remote Desktop connection the David
    way", but no RDP code exists.
  * stun.l.google.com:19302 was hardcoded inside use_stun() with no way to
    override it.

Fails on the original module, passes on the patched one.
"""

import ast
import importlib.util
import os
import pathlib
import sys
import types

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1] / "daveviewer.py"


def _install_stun_stub():
    """The original module imports `stun` at top level, so provide a stub
    before loading it; otherwise every test errors during collection instead of
    reporting the behavioural difference."""
    if "stun" not in sys.modules:
        module = types.ModuleType("stun")
        module.get_ip_info = lambda stun_host, stun_port: (
            "Full Cone", "203.0.113.7", 51234,
        )
        sys.modules["stun"] = module


_install_stun_stub()

_spec = importlib.util.spec_from_file_location("daveviewer", SRC)
dv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dv)


def _code_without_docstrings(src):
    """Docstrings quote the old placeholders on purpose; only code counts."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                src = src.replace(doc, "")
    return src


def _stub_stun(nat_type="Full Cone", ip="203.0.113.7", port=51234):
    """Install a fake `stun` module and record how get_ip_info was called."""
    calls = []

    def get_ip_info(stun_host, stun_port):
        calls.append((stun_host, stun_port))
        return nat_type, ip, port

    module = types.ModuleType("stun")
    module.get_ip_info = get_ip_info
    sys.modules["stun"] = module
    return calls


def _drop_stub():
    sys.modules.pop("stun", None)


# ---------------------------------------------------------------- honesty

def test_use_turn_does_not_claim_success():
    try:
        result = dv.use_turn()
    except NotImplementedError as exc:
        assert "NOT IMPLEMENTED" in str(exc)
        return
    raise AssertionError(f"use_turn() returned {result!r} instead of raising")


def test_use_hole_punching_does_not_claim_success():
    try:
        result = dv.use_hole_punching()
    except NotImplementedError as exc:
        assert "NOT IMPLEMENTED" in str(exc)
        return
    raise AssertionError(
        f"use_hole_punching() returned {result!r} instead of raising"
    )


def test_no_placeholder_hosts_or_dummy_datagrams_remain():
    code = _code_without_docstrings(SRC.read_text(encoding="utf-8"))
    for placeholder in ("turn_server_ip_here", "peer_ip_here", 'sendto(b"Hello")'):
        assert placeholder not in code, f"placeholder still present: {placeholder}"


def test_module_no_longer_imports_socket():
    """The only reason socket was imported was the fake hole-punch datagram."""
    src = SRC.read_text(encoding="utf-8")
    assert "import socket" not in src


# ------------------------------------------------------------ configurability

def test_stun_server_is_configurable_by_argument():
    _drop_stub()
    calls = _stub_stun()
    try:
        assert dv.use_stun("stun.example.org", 3478) is True
    finally:
        _drop_stub()
    assert calls == [("stun.example.org", 3478)]


def test_stun_server_is_configurable_by_environment():
    _drop_stub()
    import os

    calls = _stub_stun()
    os.environ["DAVIEWER_STUN_HOST"] = "stun.internal.test"
    os.environ["DAVIEWER_STUN_PORT"] = "3479"
    try:
        dv.use_stun()
    finally:
        os.environ.pop("DAVIEWER_STUN_HOST", None)
        os.environ.pop("DAVIEWER_STUN_PORT", None)
        _drop_stub()
    assert calls == [("stun.internal.test", 3479)]


def test_stun_host_is_not_hardcoded_in_the_function():
    src = SRC.read_text(encoding="utf-8")
    body = src[src.index("def use_stun"):src.index("def use_turn")]
    assert "stun.l.google.com" not in body, (
        "the STUN host must come from resolve_stun_server(), not a literal"
    )
    assert dv.DEFAULT_STUN_HOST == "stun.l.google.com"
    assert dv.DEFAULT_STUN_PORT == 19302


def test_stun_failure_is_reported_not_swallowed():
    _drop_stub()
    module = types.ModuleType("stun")

    def boom(stun_host, stun_port):
        raise OSError("network unreachable")

    module.get_ip_info = boom
    sys.modules["stun"] = module
    try:
        with pytest.raises(OSError):
            dv.use_stun()
    finally:
        _drop_stub()


# ------------------------------------------------------------------- CLI

def test_main_reports_no_connection_and_fails(capsys):
    _drop_stub()
    _stub_stun()
    try:
        code = dv.main([])
    finally:
        _drop_stub()
    out = capsys.readouterr().out
    assert code != 0, "must not exit 0 when no connection was established"
    assert "No connection was established" in out
    assert "does NOT implement Remote Desktop" in out


def test_probe_only_exits_zero_on_success(capsys):
    _drop_stub()
    _stub_stun()
    try:
        code = dv.main(["--probe-only"])
    finally:
        _drop_stub()
    out = capsys.readouterr().out
    assert code == 0
    assert "External IP: 203.0.113.7" in out
    assert "NOT IMPLEMENTED" in out


def test_probe_only_fails_when_stun_fails(capsys):
    _drop_stub()
    module = types.ModuleType("stun")
    module.get_ip_info = lambda stun_host, stun_port: (None, None, None)
    sys.modules["stun"] = module
    try:
        code = dv.main(["--probe-only"])
    finally:
        _drop_stub()
    assert code != 0
