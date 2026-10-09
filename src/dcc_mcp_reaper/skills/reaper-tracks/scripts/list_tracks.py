"""List every track in the active project with name, mute/solo state and FX count."""

import json
import sys


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
                "guid": module.RPR_GetTrackGUID(track),
                "muted": bool(module.RPR_GetMediaTrackInfo_Value(track, "B_MUTE")),
                "soloed": bool(module.RPR_GetMediaTrackInfo_Value(track, "I_SOLO")),
                "fx_count": module.RPR_TrackFX_GetCount(track),
            }
        )
    return tracks


def main():
    import argparse

    from dcc_mcp_reaper.runtime import environment_report
    from dcc_mcp_reaper.transport import IN_PROCESS, resolve_transport

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    report = environment_report()
    if not report["host_available"]:
        print(json.dumps({"host_available": False, "tracks": []}, indent=2))
        return 0

    transport = resolve_transport()
    if transport == IN_PROCESS:
        tracks = _read_in_process()
    else:
        import reapy

        tracks = [
            {
                "index": index,
                "name": track.name,
                "guid": track.GUID,
                "muted": track.is_muted,
                "soloed": bool(track.solo),
                "fx_count": track.n_fxs,
            }
            for index, track in enumerate(reapy.Project().tracks)
        ]

    if args.limit is not None:
        tracks = tracks[: args.limit]
    print(
        json.dumps(
            {"host_available": True, "transport": transport, "tracks": tracks},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
