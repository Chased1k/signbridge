"""Load Galtis and configure SignBridge's reusable Cycles studio scene.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/blender/setup_scene.py -- [--greenscreen]
"""

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RIG_FILE = PROJECT_ROOT / "data" / "studiogalt" / "Rigs" / "Galtis 8 20260401.blend"
DEFAULT_SCENE_FILE = PROJECT_ROOT / "output" / "galtis_signbridge_scene.blend"
SCENE_OBJECT_PREFIX = "SignBridge_"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--greenscreen", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_SCENE_FILE)
    parser.add_argument("--samples", type=int, default=64)
    return parser.parse_args(argv)


def find_galtis_armature():
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("No armature found in the Galtis scene")
    return max(armatures, key=lambda obj: len(obj.data.bones))


def galtis_meshes():
    named = [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and obj.name in {"GaltisBody", "GaltisHead"}
    ]
    return named or [
        obj for obj in bpy.data.objects if obj.type == "MESH" and not obj.hide_render
    ]


def scene_bounds(objects):
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        for corner in obj.bound_box
    ]
    if not points:
        return Vector((-0.5, -0.5, 0.0)), Vector((0.5, 0.5, 2.0))
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high


def _remove_previous_studio_objects():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(SCENE_OBJECT_PREFIX) or obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.name == "Background":
            obj.hide_render = True
            obj.hide_viewport = True


def _new_area_light(name, location, target, energy, size):
    light_data = bpy.data.lights.new(name, type="AREA")
    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    light.location = location
    light.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(light)
    return light


def configure_world(scene, greenscreen=False):
    world = scene.world or bpy.data.worlds.new("SignBridge_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (
        (0.0, 0.55, 0.08, 1.0) if greenscreen else (0.12, 0.12, 0.12, 1.0)
    )
    background.inputs["Strength"].default_value = 0.25


def setup_scene(greenscreen=False, samples=64, resolution_percentage=100):
    """Configure camera, three lights, background, and Cycles CPU output."""
    scene = bpy.context.scene
    meshes = galtis_meshes()
    low, high = scene_bounds(meshes)
    size = high - low
    height = max(size.z, 1.0)

    _remove_previous_studio_objects()

    # Frame from the waist (roughly 42% of body height) through the head.
    waist_z = low.z + 0.42 * height
    target = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, (waist_z + high.z) / 2))
    shot_height = max((high.z - waist_z) * 1.18, 0.8)

    camera_data = bpy.data.cameras.new(f"{SCENE_OBJECT_PREFIX}Camera")
    camera_data.lens = 50
    camera_data.sensor_width = 36
    camera = bpy.data.objects.new(f"{SCENE_OBJECT_PREFIX}Camera", camera_data)
    vertical_sensor = camera_data.sensor_width * (720 / 1280)
    vertical_fov = 2 * math.atan(vertical_sensor / (2 * camera_data.lens))
    distance = (shot_height / 2) / math.tan(vertical_fov / 2)
    camera.location = Vector((target.x, low.y - distance, target.z))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(camera)
    scene.camera = camera

    light_size = max(height * 0.55, 1.0)
    _new_area_light(
        f"{SCENE_OBJECT_PREFIX}Key",
        target + Vector((0.75 * height, -0.95 * height, 0.65 * height)),
        target,
        900_000,
        light_size,
    )
    _new_area_light(
        f"{SCENE_OBJECT_PREFIX}Fill",
        target + Vector((-0.8 * height, -0.55 * height, 0.25 * height)),
        target,
        350_000,
        light_size * 1.2,
    )
    _new_area_light(
        f"{SCENE_OBJECT_PREFIX}Back",
        target + Vector((0.25 * height, 0.7 * height, 0.85 * height)),
        target,
        700_000,
        light_size * 0.7,
    )

    configure_world(scene, greenscreen)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = resolution_percentage
    scene.render.fps = 30
    scene.render.fps_base = 1.0
    # The source .blend ships with a longer preview range; animation renders
    # must honor frame_start/frame_end set by the transferred sign action.
    scene.use_preview_range = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_persistent_data = True
    return scene


def load_galtis_scene():
    if not RIG_FILE.is_file():
        raise FileNotFoundError(f"Galtis rig not found: {RIG_FILE}")
    bpy.ops.wm.open_mainfile(filepath=str(RIG_FILE))
    return find_galtis_armature()


def main():
    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    armature = load_galtis_scene()
    setup_scene(greenscreen=args.greenscreen, samples=args.samples)
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    print(f"SIGNBRIDGE_ARMATURE={armature.name} bones={len(armature.data.bones)}")
    print(f"SIGNBRIDGE_GREENSCREEN={args.greenscreen}")
    print(f"SIGNBRIDGE_SCENE={args.output}")


if __name__ == "__main__":
    main()
