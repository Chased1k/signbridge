"""Inspect the StudioGalt Galtis rig and render its rest pose."""
import argparse
import sys

import time
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RIG_FILE = PROJECT_ROOT / "data" / "studiogalt" / "Rigs" / "Galtis 8 20260401.blend"
OUTPUT_FILE = PROJECT_ROOT / "output" / "galtis_tpose_test.png"


def scene_bounds(objects):
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        if obj.type == "MESH" and not obj.hide_render
        for corner in obj.bound_box
    ]
    if not points:
        return Vector((0, 0, 1)), Vector((2, 2, 2))
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return (low + high) / 2, high - low


def setup_camera_and_light(scene, meshes):
    center, size = scene_bounds(meshes)
    span = max(size.x, size.y, size.z, 1.0)
    cam_data = bpy.data.cameras.new("SignBridge_Test_Camera")
    camera = bpy.data.objects.new("SignBridge_Test_Camera", cam_data)
    camera.location = center + Vector((0, -2.8 * span, 0.15 * span))
    bpy.context.collection.objects.link(camera)
    camera.name = "SignBridge_Test_Camera"
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 55
    scene.camera = camera

    key_data = bpy.data.lights.new("SignBridge_Test_Key", type="AREA")
    key = bpy.data.objects.new("SignBridge_Test_Key", key_data)
    key.location = center + Vector((1.5 * span, -1.5 * span, 2.0 * span))
    key_data.energy = 1400
    key_data.size = span
    bpy.context.collection.objects.link(key)
    key.name = "SignBridge_Test_Key"
    key.data.energy = 1400
    key.data.size = span

    fill_data = bpy.data.lights.new("SignBridge_Test_Fill", type="AREA")
    fill = bpy.data.objects.new("SignBridge_Test_Fill", fill_data)
    fill.location = center + Vector((-1.5 * span, -0.5 * span, 0.8 * span))
    fill_data.energy = 700
    fill_data.size = span
    bpy.context.collection.objects.link(fill)
    fill.name = "SignBridge_Test_Fill"
    fill.data.energy = 700
    fill.data.size = span


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-render", action="store_true", help="inspect the rig without GPU rendering")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    started = time.perf_counter()
    if not RIG_FILE.is_file():
        raise FileNotFoundError(f"Rig not found: {RIG_FILE}")

    bpy.ops.wm.open_mainfile(filepath=str(RIG_FILE))
    objects = list(bpy.data.objects)
    armatures = [obj for obj in objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in objects if obj.type == "MESH"]
    print(f"SIGNBRIDGE_OBJECT_COUNT={len(objects)}")
    for obj in objects:
        print(f"OBJECT type={obj.type} name={obj.name}")

    print(f"SIGNBRIDGE_ARMATURE_COUNT={len(armatures)}")
    for armature in armatures:
        print(f"ARMATURE name={armature.name} bones={len(armature.data.bones)}")
        print("BONES " + " | ".join(bone.name for bone in armature.data.bones))
        armature.data.pose_position = "REST"

    print(f"SIGNBRIDGE_MESH_COUNT={len(meshes)}")
    for mesh in meshes:
        keys = mesh.data.shape_keys
        names = [block.name for block in keys.key_blocks] if keys else []
        print(f"SHAPEKEYS mesh={mesh.name} count={len(names)} names={' | '.join(names)}")

    if args.skip_render:
        print(f"SIGNBRIDGE_TOTAL_SECONDS={time.perf_counter() - started:.3f}")
        return

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    avatar_meshes = [mesh for mesh in meshes if mesh.name in {"GaltisBody", "GaltisHead"}] or meshes
    setup_camera_and_light(scene, avatar_meshes)
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(OUTPUT_FILE)

    render_started = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    print(f"SIGNBRIDGE_OUTPUT={OUTPUT_FILE}")
    print(f"SIGNBRIDGE_RENDER_SECONDS={time.perf_counter() - render_started:.3f}")
    print(f"SIGNBRIDGE_TOTAL_SECONDS={time.perf_counter() - started:.3f}")


if __name__ == "__main__":
    main()
