"""Benchmark the three Sprint 6 Cycles CPU still-frame configurations."""

import argparse
import json
import sys
import time
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from render_sign import PROJECT_ROOT, resolve_sign_fbx
from setup_scene import load_galtis_scene, setup_scene
from sign_importer import import_sign_fbx, remove_imported_armature, transfer_animation

DEFAULT_JSON = PROJECT_ROOT / "output" / "benchmarks" / "sprint6-benchmarks.json"
CONFIGS = (
    ("dev_360p_32", 32, 50),
    ("standard_720p_64", 64, 100),
    ("quality_720p_128", 128, 100),
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--sign", default="Hello")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    target = load_galtis_scene()
    scene = setup_scene()
    fbx_path, sign_name, _variant = resolve_sign_fbx(args.sign)
    source, action = import_sign_fbx(fbx_path)
    start, end = transfer_animation(target, action, tuple(action.frame_range))
    remove_imported_armature(source)
    benchmark_frame = round((start + end) / 2)
    scene.frame_set(benchmark_frame)

    output_dir = args.output_json.resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for label, samples, percentage in CONFIGS:
        scene.cycles.samples = samples
        scene.render.resolution_percentage = percentage
        scene.render.image_settings.file_format = "PNG"
        output = output_dir / f"{label}.png"
        scene.render.filepath = str(output)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        seconds = time.perf_counter() - started
        result = {
            "label": label,
            "engine": "Cycles CPU",
            "samples": samples,
            "resolution": (
                f"{scene.render.resolution_x * percentage // 100}x"
                f"{scene.render.resolution_y * percentage // 100}"
            ),
            "frame": benchmark_frame,
            "seconds": round(seconds, 3),
            "output": str(output.relative_to(PROJECT_ROOT)),
        }
        results.append(result)
        print(f"SIGNBRIDGE_BENCHMARK={json.dumps(result, sort_keys=True)}")

    payload = {"sign": sign_name, "fbx": str(fbx_path), "results": results}
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"SIGNBRIDGE_BENCHMARK_JSON={args.output_json.resolve()}")


if __name__ == "__main__":
    main()
