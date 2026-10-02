"""Create and render a minimal Blender scene.

Run with:
  blender --background --python scripts/blender/test_minimal_render.py
  blender --background --python scripts/blender/test_minimal_render.py -- --engine cycles
"""

import argparse
import sys
import time
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("eevee", "cycles"), default="eevee")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if args.engine == "eevee" else "CYCLES"
    if args.engine == "cycles":
        scene.cycles.device = "CPU"
        scene.cycles.samples = 32

    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
    cube = bpy.context.object
    cube.name = "SignBridge_Test_Cube"

    bpy.ops.object.camera_add(location=(4.0, -4.0, 3.0))
    camera = bpy.context.object
    camera.rotation_euler = ((cube.location - camera.location).to_track_quat("-Z", "Y").to_euler())
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(2.5, -2.5, 4.0))
    light = bpy.context.object
    light.data.energy = 1000
    light.data.shape = "DISK"
    light.data.size = 4.0

    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    default_name = "signbridge_test_render.png" if args.engine == "eevee" else "signbridge_test_render_cycles.png"
    output = Path(args.output or f"/tmp/{default_name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)

    render_started = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    render_seconds = time.perf_counter() - render_started
    print(f"SIGNBRIDGE_ENGINE={args.engine}")
    print(f"SIGNBRIDGE_OUTPUT={output}")
    print(f"SIGNBRIDGE_RENDER_SECONDS={render_seconds:.3f}")
    print(f"SIGNBRIDGE_TOTAL_SECONDS={time.perf_counter() - started:.3f}")


if __name__ == "__main__":
    main()
