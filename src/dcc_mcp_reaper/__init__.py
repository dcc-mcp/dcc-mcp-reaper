"""REAPER adapter; host discovery is lazy."""

__version__ = "0.1.2"  # x-release-please-version


def __getattr__(name):
    if name == "ReaperServer":
        from .server import ReaperServer

        return ReaperServer
    raise AttributeError(name)
