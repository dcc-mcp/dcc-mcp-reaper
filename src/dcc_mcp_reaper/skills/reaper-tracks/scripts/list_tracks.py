"""List every track in the active project with name, mute/solo state and FX count."""

import sys
from typing import Optional

from dcc_mcp_core.skill import skill_entry

from dcc_mcp_reaper.skill_support import inspection_result, print_cli_result


def _read_in_process():
    from dcc_mcp_reaper.transport import in_process_module

    module = in_process_module()
    project = module.RPR_EnumProjects(-1, "", 0)[0]
    count = module.RPR_CountTracks(project)
    tracks = []
    for index in range(count):
        track = module.RPR_GetTrack(project, index)
        name = module.RPR_GetSetMediaTrackInfo_String(track, "P_NAME", "", False)[3]
        tracks.append(
            {
                "index": index,
                "name": name or None,
                "guid": module.RPR_GetSetMediaTrackInfo_String(track, "GUID", "", False)[3],
                "muted": bool(module.RPR_GetMediaTrackInfo_Value(track, "B_MUTE")),
                "soloed": bool(module.RPR_GetMediaTrackInfo_Value(track, "I_SOLO")),
                "fx_count": module.RPR_TrackFX_GetCount(track),
            }
        )
    return tracks


@skill_entry
def main(limit: Optional[int] = None) -> dict:
    from dcc_mcp_reaper.runtime import environment_report
    from dcc_mcp_reaper.transport import IN_PROCESS, external_client, resolve_transport

    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
        raise ValueError("limit must be a positive integer")

    report = environment_report()
    if not report["host_available"]:
        result = {"host_available": False, "tracks": []}
        if report["transport_error"]:
            result["transport_error"] = report["transport_error"]
        return inspection_result("REAPER is not reachable", result)

    transport = resolve_transport()
    if transport == IN_PROCESS:
        tracks = _read_in_process()
    else:
        reapy = external_client()

        tracks = [
            {
                "index": index,
                "name": track.name,
                "guid": reapy.reascript_api.GetSetMediaTrackInfo_String(track.id, "GUID", "", False)[3],
                "muted": track.is_muted,
                "soloed": bool(track.is_solo),
                "fx_count": track.n_fxs,
            }
            for index, track in enumerate(reapy.Project().tracks)
        ]

    if limit is not None:
        tracks = tracks[:limit]
    return inspection_result(
        "REAPER project tracks", {"host_available": True, "transport": transport, "tracks": tracks}
    )


def cli_main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    return print_cli_result(main(limit=args.limit))


if __name__ == "__main__":
    sys.exit(cli_main())
