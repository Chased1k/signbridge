"""Import a StudioGalt No Mesh Full FBX, compare its rig, and render a frame."""

import argparse
import re
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = PROJECT_ROOT / "data" / "studiogalt"
RIG_FILE = ARCHIVE / "Rigs" / "Galtis 8 20260401.blend"
OUTPUT_FILE = PROJECT_ROOT / "output" / "fbx_import_test.png"

EXPORT_TO_BASE = {
    "Head": "headinte",
    "Neck": "neckinte_01",
    "Chest_1": "spineinte_01",
    "Chest_2": "spineinte_02",
    "Chest_3": "spineinte_03",
    "Chest_4": "spineinte_04",
    "Hip": "pelvisinte",
    "Hips": "pelvisinte",
}
for side in ("L", "R"):
    EXPORT_TO_BASE.update(
        {
            f"Collar_{side}": f"clavicleinte_{side}",
            f"Bicep_{side}": f"upperarminte_{side}",
            f"Forearm_{side}": f"lowerarminte_{side}",
            f"Hand_{side}": f"handinte_{side}",
            f"Wrist_{side}": f"wristinte_{side}",
            f"Elbow_{side}": f"elbowinte_{side}",
            f"Thigh_{side}": f"thighinte_{side}",
            f"CThigh_{side}": f"cthighinte_{side}",
            f"Shin_{side}": f"calfinte_{side}",
            f"CShin_{side}": f"cshininte_{side}",
            f"Foot_{side}": f"footinte_{side}",
            f"Toe_{side}": f"ballinte_{side}",
        }
    )
    for finger in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
        for joint in (1, 2, 3):
            EXPORT_TO_BASE[f"{finger}{joint}_{side}"] = f"{finger.lower()}inte_0{joint}_{side}"
    for finger in ("Index", "Middle", "Ring", "Pinky"):
        EXPORT_TO_BASE[f"{finger}Palm_{side}"] = f"{finger.lower()}inte_metacarpal_{side}"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--fbx", type=Path)
    parser.add_argument("--skip-render", action="store_true", help="inspect the FBX without GPU rendering")
    return parser.parse_args(argv)


def find_sample_fbx():
    candidates = sorted((ARCHIVE / "SG ASL Dictionary" / "ASL A").rglob("*No Mesh Full*.fbx"))
    if not candidates:
        candidates = sorted((ARCHIVE / "SG ASL Dictionary").rglob("*No Mesh Full*.fbx"))
    if not candidates:
        raise FileNotFoundError("No 'No Mesh Full' FBX found in the StudioGalt dictionary")
    return candidates[0]


def scene_bounds(meshes):
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    if not points:
        return Vector((0, 0, 1)), Vector((2, 2, 2))
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return (low + high) / 2, high - low


def setup_render(scene, meshes):
    center, size = scene_bounds(meshes)
    span = max(size.x, size.y, size.z, 1.0)
    bpy.ops.object.camera_add(location=center + Vector((0, -2.8 * span, 0.15 * span)))
    camera = bpy.context.object
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 55
    scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=center + Vector((1.5 * span, -1.5 * span, 2 * span)))
    bpy.context.object.data.energy = 1600
    bpy.context.object.data.size = span
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(OUTPUT_FILE)


def normalized_bone_name(name):
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def remap_action(action, base_bones):
    normalized_base = {normalized_bone_name(name): name for name in base_bones}
    mapping = {}
    for source_name in {match.group(1) for curve in action.fcurves if (match := re.search(r'pose\.bones\["([^"]+)"\]', curve.data_path))}:
        target = EXPORT_TO_BASE.get(source_name)
        if target not in base_bones:
            target = normalized_base.get(normalized_bone_name(source_name))
        if target:
            mapping[source_name] = target

    remapped = action.copy()
    remapped.name = f"{action.name} | SignBridge retarget"
    for curve in remapped.fcurves:
        match = re.search(r'pose\.bones\["([^"]+)"\]', curve.data_path)
        if match and match.group(1) in mapping:
            curve.data_path = curve.data_path.replace(
                f'pose.bones["{match.group(1)}"]', f'pose.bones["{mapping[match.group(1)]}"]'
            )
    return remapped, mapping


def main():
    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    fbx_file = (args.fbx or find_sample_fbx()).resolve()
    if not RIG_FILE.is_file():
        raise FileNotFoundError(f"Rig not found: {RIG_FILE}")
    if not fbx_file.is_file():
        raise FileNotFoundError(f"FBX not found: {fbx_file}")

    total_started = time.perf_counter()
    bpy.ops.wm.open_mainfile(filepath=str(RIG_FILE))
    base_armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not base_armatures:
        raise RuntimeError("No armature found in Galtis base scene")
    base_armature = max(base_armatures, key=lambda obj: len(obj.data.bones))
    base_bones = {bone.name for bone in base_armature.data.bones}
    before_objects = set(bpy.data.objects)

    import_started = time.perf_counter()
    result = bpy.ops.import_scene.fbx(filepath=str(fbx_file))
    import_seconds = time.perf_counter() - import_started
    imported_objects = [obj for obj in bpy.data.objects if obj not in before_objects]
    imported_armatures = [obj for obj in imported_objects if obj.type == "ARMATURE"]
    if not imported_armatures:
        raise RuntimeError("FBX import produced no armature")
    source_armature = max(imported_armatures, key=lambda obj: len(obj.data.bones))
    source_bones = {bone.name for bone in source_armature.data.bones}

    common = sorted(base_bones & source_bones)
    only_base = sorted(base_bones - source_bones)
    only_source = sorted(source_bones - base_bones)
    print(f"SIGNBRIDGE_FBX={fbx_file}")
    print(f"SIGNBRIDGE_IMPORT_RESULT={result}")
    print(f"SIGNBRIDGE_IMPORT_SECONDS={import_seconds:.3f}")
    print(f"SIGNBRIDGE_BASE_ARMATURE={base_armature.name} bones={len(base_bones)}")
    print(f"SIGNBRIDGE_IMPORTED_ARMATURE={source_armature.name} bones={len(source_bones)}")
    print(f"SIGNBRIDGE_COMMON_BONES={len(common)}")
    print("COMMON_BONES " + " | ".join(common))
    print("ONLY_BASE " + " | ".join(only_base))
    print("ONLY_IMPORTED " + " | ".join(only_source))

    action = source_armature.animation_data.action if source_armature.animation_data else None
    if action is None:
        raise RuntimeError("Imported armature has no action")
    frame_start, frame_end = (float(value) for value in action.frame_range)
    print(f"ACTION name={action.name} fcurves={len(action.fcurves)} frame_start={frame_start:.3f} frame_end={frame_end:.3f}")
    for curve in action.fcurves:
        print(f"FCURVE path={curve.data_path} index={curve.array_index} keys={len(curve.keyframe_points)}")

    # The Full export skeleton uses presentation names rather than the base
    # rig's intermediate/control names. Reverse StudioGalt's documented export
    # mapping, then use normalized matching for FK/IK controls.
    retarget_action, mapping = remap_action(action, base_bones)
    print(f"SIGNBRIDGE_RETARGET_MAPPED_BONES={len(mapping)}")
    print("RETARGET_MAP " + " | ".join(f"{source}->{target}" for source, target in sorted(mapping.items())))

    if args.skip_render:
        print(f"SIGNBRIDGE_TOTAL_SECONDS={time.perf_counter() - total_started:.3f}")
        return

    base_armature.animation_data_create()
    base_armature.animation_data.action = retarget_action
    base_armature.data.pose_position = "POSE"
    source_armature.hide_render = True
    scene = bpy.context.scene
    scene.frame_start = int(frame_start)
    scene.frame_end = int(frame_end)
    scene.frame_set(round((frame_start + frame_end) / 2))
    base_meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj not in imported_objects]
    meshes = [mesh for mesh in base_meshes if mesh.name in {"GaltisBody", "GaltisHead"}] or base_meshes
    setup_render(scene, meshes)

    render_started = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    print(f"SIGNBRIDGE_OUTPUT={OUTPUT_FILE}")
    print(f"SIGNBRIDGE_RENDER_SECONDS={time.perf_counter() - render_started:.3f}")
    print(f"SIGNBRIDGE_TOTAL_SECONDS={time.perf_counter() - total_started:.3f}")


if __name__ == "__main__":
    main()
