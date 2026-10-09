# Installing dcc-mcp-reaper

Install the package first, then do the host-side setup for the transport you
intend to use.

```bash
pip install dcc-mcp-reaper
```

Check what the adapter can see at any time:

```bash
dcc-mcp-reaper doctor
```

The report's `host_available` field tells you whether REAPER is reachable. It is
`false` until the host-side setup below is complete — that is expected, not an
error.

## Transport 1: in-process ReaScript (default)

This is the default and the recommended path. The adapter runs inside REAPER as
a ReaScript.

### 1. Install a matching Python

ReaScript Python requires Python to be installed separately, and **the
interpreter bitness must match REAPER's**: a 64-bit REAPER needs a 64-bit
Python. Any version from 2.7 through the current 3.x release works; this
adapter targets 3.7 and above.

### 2. Enable Python in REAPER

1. Open `Options > Preferences > Plug-Ins > ReaScript`.
2. Confirm REAPER detected your Python. If it did not, enter the Python install
   directory manually in the same panel.

### 3. Add the adapter as a ReaScript

1. Open the Actions window (the `?` key by default).
2. Click `ReaScript: "Load..."` and select the adapter's bootstrap script.
3. Run it from the Actions window, or bind it to a shortcut or toolbar button.

### 4. Serve

```bash
dcc-mcp-reaper serve --pid <reaper-pid>
```

`--pid` is required on this transport: the service's lifetime is bound to the
REAPER process.

## Transport 2: external (Web Browser Interface)

Use this when you want the adapter to run in a separate process. The
`reapy_boost` bridge still needs Python enabled inside REAPER, with a shared
library whose bitness matches the host, to run its server ReaScript.

### 1. Enable REAPER's Web Browser Interface

1. Open `Options > Preferences > Control/OSC/web`.
2. Add a new `Web browser interface` entry and note its port.

### 2. Install the client and configure REAPER once

```bash
pip install "dcc-mcp-reaper[external]"
python -c "import reapy_boost; reapy_boost.configure_reaper()"
```

The `external` extra installs `reapy-boost`, whose importable top-level package
is **`reapy_boost`**. (`reapy` is a separate, unmaintained distribution on PyPI
that this adapter does not use.)

`configure_reaper()` enables ReaScript Python, configures its shared-library
path, adds the Web Browser Interface, and registers the package's
`activate_reapy_server.py` in REAPER's Actions list. It edits REAPER's
configuration files; it does not remove the embedded-Python requirement.
**Restart REAPER** afterwards so those changes take effect.

### 3. Serve

```bash
export DCC_MCP_REAPER_TRANSPORT=external
dcc-mcp-reaper serve
```

Do not pass `--pid` on this transport: the adapter process owns its own
lifetime, and REAPER may restart independently.

## Verifying

`dcc-mcp-reaper doctor` reports, for the active transport:

- `transport` — which channel is in use.
- `host_version` / `host_available` — whether REAPER answered.
- `host_version_supported` — whether that version sits on a supported line.
- `python_bitness_ok` — whether the interpreter can drive this REAPER.

## Uninstall

```bash
pip uninstall dcc-mcp-reaper
```

On the external transport, remove the registered `activate_reapy_server.py`
action and the Web Browser Interface added for reapy, then restart REAPER.
Keep any Python configuration that other ReaScripts still use.
