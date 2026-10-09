"""REAPER host compatibility matrix.

REAPER exposes its own version through the ReaScript API function
``GetAppVersion()``, which returns a display string such as ``7.82/x64``. The
matrix below records which release lines this adapter is written against.

The current CI suite is host-free, so a version row here is a *declared*
support statement, not CI-verified evidence. See ``docs/validation/README.md``.
"""

SUPPORTED_MAJOR_LINES = ("6", "7")

MINIMUM_VERSION = "6.0"

TARGET_VERSION = "7.82"

# GetAppVersion() returns "<version>/<arch>"; the arch suffix is informative
# only because ReaScript Python requires the interpreter to match the host
# bitness, and that is checked separately at runtime.
VERSION_SUFFIX_SEPARATOR = "/"


def parse_app_version(raw):
    """Split a ``GetAppVersion()`` string into ``(version, arch)``.

    Returns ``(version, None)`` when REAPER reports no architecture suffix.
    """
    text = (raw or "").strip()
    if VERSION_SUFFIX_SEPARATOR in text:
        version, _, arch = text.partition(VERSION_SUFFIX_SEPARATOR)
        return version.strip(), arch.strip() or None
    return text, None


def major_line(raw):
    """Return the major release line of a ``GetAppVersion()`` string."""
    version, _ = parse_app_version(raw)
    return version.split(".")[0] if version else ""


def is_supported(raw):
    """Whether a reported REAPER version falls on a supported major line."""
    return major_line(raw) in SUPPORTED_MAJOR_LINES
