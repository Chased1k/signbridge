"""Render one StudioGalt sign on Galtis as an H.264 MP4."""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from setup_scene import PROJECT_ROOT, load_galtis_scene, setup_scene
from sign_importer import (
    import_sign_fbx,
    remove_imported_armature,
    retime_action,
    transfer_animation,
)

SIGN_INDEX = PROJECT_ROOT / "data" / "sign_index.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "first_sign_render.mp4"


def resolve_sign_fbx(sign_name):
    data = json.loads(SIGN_INDEX.read_text())
    signs = data["signs"]
    key = next((name for name in signs if name.casefold() == sign_name.casefold()), None)
    if key is None:
        raise KeyError(f"Sign not found in index: {sign_name}")
    for variant in signs[key]["variants"]:
        path = variant["fbx"].get("no_mesh_full")
        if path:
            return PROJECT_ROOT / path, key, variant
    raise FileNotFoundError(f"No no_mesh_full FBX indexed for {key}")


def configure_mp4(scene, output):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def render_animation_mp4(scene, output, frame_start, frame_end):
    """Render an exact PNG frame range, then encode it as H.264."""
    output = configure_mp4(scene, output)
    frame_dir = output.parent / f".{output.stem}_frames"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)

    scene.render.image_settings.file_format = "PNG"
    try:
        for frame in range(frame_start, frame_end + 1):
            scene.frame_set(frame)
            scene.render.filepath = str(frame_dir / f"frame_{frame:06d}.png")
            bpy.ops.render.render(write_still=True)

        ffmpeg = shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"
        command = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(scene.render.fps),
            "-start_number",
            str(frame_start),
            "-i",
            str(frame_dir / "frame_%06d.png"),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
        subprocess.run(command, check=True)
    finally:
        shutil.rmtree(frame_dir, ignore_errors=True)
    return output


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--sign", default="Hello")
    parser.add_argument("--fbx", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--resolution-percentage", type=int, default=100)
    parser.add_argument("--greenscreen", action="store_true")
    parser.add_argument("--source-fps", type=int, default=60)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    total_started = time.perf_counter()

    target = load_galtis_scene()
    scene = setup_scene(
        greenscreen=args.greenscreen,
        samples=args.samples,
        resolution_percentage=args.resolution_percentage,
    )
    output_fps = scene.render.fps
    if args.fbx:
        fbx_path = args.fbx.resolve()
        sign_name = fbx_path.stem
    else:
        fbx_path, sign_name, _variant = resolve_sign_fbx(args.sign)

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
    frame_start, frame_end = transfer_animation(target, action, frame_range)
    remove_imported_armature(source)
    transfer_seconds = time.perf_counter() - transfer_started

    # The copied action is retimed from StudioGalt's 60 fps source to 30 fps.
    scene.frame_step = 1
    output = Path(args.output).resolve()
    rendered_frames = frame_end - frame_start + 1

    print(f"SIGNBRIDGE_SIGN={sign_name}")
    print(f"SIGNBRIDGE_SOURCE_FRAMES={frame_start}-{frame_end}")
    print(f"SIGNBRIDGE_FRAME_STEP={scene.frame_step}")
    print(f"SIGNBRIDGE_OUTPUT_FRAMES={rendered_frames}")
    print(f"SIGNBRIDGE_IMPORT_SECONDS={import_seconds:.3f}")
    print(f"SIGNBRIDGE_TRANSFER_SECONDS={transfer_seconds:.3f}")

    render_started = time.perf_counter()
    render_animation_mp4(scene, output, frame_start, frame_end)
    render_seconds = time.perf_counter() - render_started
    total_seconds = time.perf_counter() - total_started
    print(f"SIGNBRIDGE_OUTPUT={output}")
    print(f"SIGNBRIDGE_RENDER_SECONDS={render_seconds:.3f}")
    print(f"SIGNBRIDGE_RENDER_SECONDS_PER_FRAME={render_seconds / rendered_frames:.3f}")
    print(f"SIGNBRIDGE_TOTAL_SECONDS={total_seconds:.3f}")


if __name__ == "__main__":
    main()
