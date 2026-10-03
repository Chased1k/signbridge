"""Load Galtis once and sequentially render three signs for Sprint 6."""

import argparse
import json
import sys
import time
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from render_sign import PROJECT_ROOT, render_animation_mp4, resolve_sign_fbx
from setup_scene import load_galtis_scene, setup_scene
from sign_importer import (
    import_sign_fbx,
    remove_imported_armature,
    retime_action,
    transfer_animation,
)

DEFAULT_SIGNS = ("Hello", "Biological Mother", "Please")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "batch_test"


def slugify(value):
    return "_".join(value.casefold().split())


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--signs", nargs=3, default=DEFAULT_SIGNS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--resolution-percentage", type=int, default=50)
    parser.add_argument("--source-fps", type=int, default=60)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    total_started = time.perf_counter()
    target = load_galtis_scene()
    scene = setup_scene(
        samples=args.samples,
        resolution_percentage=args.resolution_percentage,
    )
    output_fps = scene.render.fps
    scene.frame_step = 1
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for requested_sign in args.signs:
        sign_started = time.perf_counter()
        fbx_path, sign_name, _variant = resolve_sign_fbx(requested_sign)

        import_started = time.perf_counter()
        source, action = import_sign_fbx(fbx_path)
        import_seconds = time.perf_counter() - import_started

        transfer_started = time.perf_counter()
        frame_range = retime_action(
            action,
            source_fps=args.source_fps,
            target_fps=output_fps,
        )
        scene.render.fps = output_fps
        start, end = transfer_animation(target, action, frame_range)
        remove_imported_armature(source)
        transfer_seconds = time.perf_counter() - transfer_started

        frames = end - start + 1
        output = output_dir / f"{slugify(sign_name)}.mp4"
        render_started = time.perf_counter()
        render_animation_mp4(scene, output, start, end)
        render_seconds = time.perf_counter() - render_started

        result = {
            "sign": sign_name,
            "fbx": str(fbx_path.relative_to(PROJECT_ROOT)),
            "source_frames": [start, end],
            "output_frames": frames,
            "import_seconds": round(import_seconds, 3),
            "transfer_seconds": round(transfer_seconds, 3),
            "render_seconds": round(render_seconds, 3),
            "seconds_per_frame": round(render_seconds / frames, 3),
            "total_seconds": round(time.perf_counter() - sign_started, 3),
            "output": str(output.relative_to(PROJECT_ROOT)),
        }
        results.append(result)
        print(f"SIGNBRIDGE_BATCH_RESULT={json.dumps(result, sort_keys=True)}")

    summary = {
        "configuration": {
            "engine": "Cycles CPU",
            "samples": args.samples,
            "resolution": (
                f"{scene.render.resolution_x * args.resolution_percentage // 100}x"
                f"{scene.render.resolution_y * args.resolution_percentage // 100}"
            ),
            "fps": scene.render.fps,
            "frame_step": scene.frame_step,
            "base_scene_loads": 1,
        },
        "results": results,
        "total_seconds": round(time.perf_counter() - total_started, 3),
    }
    summary_file = output_dir / "batch-results.json"
    summary_file.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"SIGNBRIDGE_BATCH_JSON={summary_file}")
    print(f"SIGNBRIDGE_TOTAL_SECONDS={summary['total_seconds']:.3f}")


if __name__ == "__main__":
    main()
