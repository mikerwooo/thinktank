#!/usr/bin/env python3
"""
Wrapper to launch the Loki Mode MCP server.

The repo contains a local mcp/ package that shadows the pip-installed MCP SDK.
This script bootstraps the pip MCP SDK into sys.modules under the 'mcp' key
before any local imports occur, so all 'from mcp.xxx import ...' calls
inside the SDK resolve correctly.
"""
import sys
import os
import site
import importlib.util
import types

_repo_root = os.path.dirname(os.path.abspath(__file__))

# --- Step 1: find pip site-packages with the real mcp SDK ---
_site_dirs = []
try:
    _site_dirs.extend(site.getsitepackages())
except AttributeError:
    pass
try:
    _site_dirs.append(site.getusersitepackages())
except AttributeError:
    pass

_mcp_sdk_root = None
for _d in _site_dirs:
    _candidate = os.path.join(_d, "mcp")
    if os.path.isdir(_candidate) and os.path.isfile(os.path.join(_candidate, "__init__.py")):
        _mcp_sdk_root = _candidate
        _sdk_site = _d
        break

if not _mcp_sdk_root:
    sys.exit("ERROR: pip mcp SDK not found. Run: pip install mcp")

# --- Step 2: load the pip mcp package into sys.modules as 'mcp' ---
# We do this by temporarily removing the repo root from sys.path,
# inserting the SDK site-packages, and importing mcp cleanly.
_orig_path = sys.path[:]
sys.path = [_sdk_site] + [p for p in sys.path if p != _repo_root and p != '']
import mcp as _pip_mcp  # noqa: E402 — this now resolves to the pip SDK
sys.path = _orig_path

# sys.modules['mcp'] now points to the pip SDK.
# Re-add repo root for the loki server's other local imports (events, state, etc.)
if _repo_root not in sys.path:
    sys.path.append(_repo_root)

# --- Step 3: load loki mcp/server.py directly (not via 'import mcp.server') ---
_spec = importlib.util.spec_from_file_location(
    "loki_mcp_server",
    os.path.join(_repo_root, "mcp", "server.py")
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
