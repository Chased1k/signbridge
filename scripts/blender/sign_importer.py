"""Reusable StudioGalt No Mesh Full FBX import and Galtis retargeting."""

import argparse
import re
import sys
import time
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SIGN_INDEX = PROJECT_ROOT / "data" / "sign_index.json"

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
            EXPORT_TO_BASE[f"{finger}{joint}_{side}"] = (
                f"{finger.lower()}inte_0{joint}_{side}"
            )
    for finger in ("Index", "Middle", "Ring", "Pinky"):
        EXPORT_TO_BASE[f"{finger}Palm_{side}"] = (
            f"{finger.lower()}inte_metacarpal_{side}"
        )


def normalized_bone_name(name):
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def action_bone_names(action):
    return {
        match.group(1)
        for curve in action.fcurves
        if (match := re.search(r'pose\.bones\["([^"]+)"\]', curve.data_path))
    }


def remap_action(action, base_bones):
    """Copy an action and rewrite source-bone F-curves for the Galtis base rig."""
    normalized_base = {normalized_bone_name(name): name for name in base_bones}
    mapping = {}
    for source_name in action_bone_names(action):
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
            source_name = match.group(1)
            curve.data_path = curve.data_path.replace(
                f'pose.bones["{source_name}"]',
                f'pose.bones["{mapping[source_name]}"]',
            )
    return remapped, mapping


def find_target_armature():
    armatures = [
        obj
        for obj in bpy.data.objects
        if obj.type == "ARMATURE" and not obj.name.startswith("Galtis_Rig")
    ]
    if not armatures:
        armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("No target Galtis armature is loaded")
    return max(armatures, key=lambda obj: len(obj.data.bones))


def import_sign_fbx(filepath):
    """Import a No Mesh Full FBX and return (source armature, retargeted action)."""
    filepath = Path(filepath).resolve()
    if not filepath.is_file():
        raise FileNotFoundError(f"Sign FBX not found: {filepath}")

    target = find_target_armature()
    base_bones = {bone.name for bone in target.data.bones}
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.fbx(
        filepath=str(filepath),
        use_anim=True,
        ignore_leaf_bones=True,
        automatic_bone_orientation=False,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"FBX importer failed for {filepath}: {result}")

    imported = [obj for obj in bpy.data.objects if obj not in before]
    imported_armatures = [obj for obj in imported if obj.type == "ARMATURE"]
    if not imported_armatures:
        raise RuntimeError(f"FBX import produced no armature: {filepath}")
    source_armature = max(imported_armatures, key=lambda obj: len(obj.data.bones))
    source_action = (
        source_armature.animation_data.action
        if source_armature.animation_data
        else None
    )
    if source_action is None:
        raise RuntimeError(f"Imported armature has no action: {filepath}")

    retargeted_action, mapping = remap_action(source_action, base_bones)
    retargeted_action["signbridge_source"] = str(filepath)
    retargeted_action["signbridge_mapped_bones"] = len(mapping)

    # No Mesh Full should not contain a character mesh, but delete any imported
    # meshes defensively so only Galtis can appear in the render.
    for obj in list(imported):
        if obj.type == "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    source_armature.hide_render = True
    source_armature.hide_viewport = True

    print(f"SIGNBRIDGE_FBX={filepath}")
    print(f"SIGNBRIDGE_IMPORTED_ARMATURE={source_armature.name}")
    print(f"SIGNBRIDGE_RETARGET_MAPPED_BONES={len(mapping)}")
    return source_armature, retargeted_action


def retime_action(action, source_fps=60, target_fps=30):
    """Scale FBX key times to preserve duration at the target frame rate."""
    if source_fps <= 0 or target_fps <= 0:
        raise ValueError("source_fps and target_fps must be positive")
    scale = target_fps / source_fps
    original_start, original_end = (float(value) for value in action.frame_range)
    if scale == 1:
        return original_start, original_end
    origin = original_start
    for curve in action.fcurves:
        for keyframe in curve.keyframe_points:
            keyframe.co.x = origin + (keyframe.co.x - origin) * scale
            keyframe.handle_left.x = origin + (keyframe.handle_left.x - origin) * scale
            keyframe.handle_right.x = origin + (keyframe.handle_right.x - origin) * scale
        curve.update()
    # action.frame_range is lazily cached, so compute the new bounds directly.
    return origin, origin + (original_end - origin) * scale


def transfer_animation(target_armature, retargeted_action, frame_range=None):
    """Assign a retargeted action and make action-driven Galtis bones authoritative."""
    if target_armature.type != "ARMATURE":
        raise TypeError("target_armature must be an armature")
    if retargeted_action is None:
        raise ValueError("retargeted_action is required")

    # The base rig's intermediate bones are constrained to FK/IK controls.
    # Baked FBX transforms target those intermediate bones directly, so their
    # constraints must be muted or they override the transferred motion.
    driven_bones = action_bone_names(retargeted_action)
    muted_constraints = 0
    for bone_name in driven_bones:
        pose_bone = target_armature.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        for constraint in pose_bone.constraints:
            if not constraint.mute:
                constraint.mute = True
                muted_constraints += 1
        pose_bone.matrix_basis.identity()

    target_armature.animation_data_create()
    target_armature.animation_data.action = retargeted_action
    # Blender 4.4+ actions use slots. A copied FBX action retains its source
    # slot, but assignment to another object does not select it automatically.
    if retargeted_action.slots:
        target_armature.animation_data.action_slot = retargeted_action.slots[0]
    target_armature.data.pose_position = "POSE"

    start, end = frame_range or retargeted_action.frame_range
    scene = bpy.context.scene
    scene.frame_start = int(round(start))
    scene.frame_end = int(round(end))
    scene.frame_set(scene.frame_start)
    bpy.context.view_layer.update()
    print(
        f"SIGNBRIDGE_TRANSFER frames={scene.frame_start}-{scene.frame_end} "
        f"driven_bones={len(driven_bones)} muted_constraints={muted_constraints}"
    )
    return scene.frame_start, scene.frame_end


def remove_imported_armature(armature):
    """Remove one temporary FBX armature after its retargeted action is copied."""
    if armature and armature.name in bpy.data.objects:
        bpy.data.objects.remove(armature, do_unlink=True)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("fbx", nargs="+", type=Path)
    return parser.parse_args(argv)


def main():
    from setup_scene import load_galtis_scene

    args = parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    target = load_galtis_scene()
    failures = 0
    for filepath in args.fbx:
        started = time.perf_counter()
        try:
            source, action = import_sign_fbx(filepath)
            frame_range = tuple(action.frame_range)
            transfer_animation(target, action, frame_range)
            remove_imported_armature(source)
            print(
                f"SIGNBRIDGE_IMPORT_TEST=PASS file={filepath} "
                f"seconds={time.perf_counter() - started:.3f}"
            )
        except Exception as exc:
            failures += 1
            print(f"SIGNBRIDGE_IMPORT_TEST=FAIL file={filepath} error={exc!r}")
    if failures:
        raise SystemExit(f"{failures} FBX import test(s) failed")


if __name__ == "__main__":
    main()
