#!/usr/bin/env python3
"""Generate a photorealistic Fabio character sheet with fal.ai."""

from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT / "fal_key.json"
REFERENCE_PATH = ROOT / "fabio_reference.png"
TEMP_ANCHOR_PATH = ROOT / ".fabio_photoreal_anchor.png"
PRIMARY_ENDPOINT = "fal-ai/ideogram/character"
FALLBACK_ENDPOINTS = (
    "fal-ai/flux-pro/ultra",
    "fal-ai/flux-pro/v1.1-ultra",
)
API_BASE = "https://fal.run"
REQUEST_TIMEOUT = 360
DOWNLOAD_TIMEOUT = 120

BASE_DESCRIPTION = (
    "Photorealistic handsome adult man with long wavy blonde hair, blue eyes, "
    "and a tanned complexion, wearing a red and green plaid button-down shirt "
    "with the sleeves rolled up and dark jeans. Clean seamless white background. "
    "Professional studio lighting. Natural skin pores, fine facial hair, individual "
    "hair strands, realistic fabric, photographic lens detail, and natural anatomy. "
    "NOT a cartoon, illustration, painting, airbrush art, or 3D render; this must "
    "look like an unambiguously real human in a high-end studio photograph. Use "
    "the supplied Fabio reference image only for consistent identity, facial "
    "features, hair, coloring, and wardrobe cues; ignore its pose and framing."
)

NEGATIVE_PROMPT = (
    "cartoon, illustration, painting, drawing, anime, CGI, 3D render, stylized, "
    "cropped feet, cropped head, hidden hands, extra fingers, missing fingers, "
    "extra limbs, distorted hands, malformed anatomy, text, logo, watermark, "
    "props, furniture, scenery, harsh shadows"
)

ASSETS: list[dict[str, str]] = [
    {
        "filename": "fabio_front.png",
        "label": "FRONT",
        "image_size": "portrait_16_9",
        "view": (
            "Full-body front view, photographed head to toe with generous white "
            "space above the hair and below both shoes. Standing upright in a "
            "neutral symmetrical pose, facing the camera directly. Both arms "
            "relaxed slightly away from the torso; both complete hands and all "
            "fingers clearly visible. Both feet fully visible."
        ),
    },
    {
        "filename": "fabio_side.png",
        "label": "SIDE PROFILE",
        "image_size": "portrait_16_9",
        "view": (
            "Full-body true side profile view, photographed head to toe with "
            "generous white space above the hair and below both shoes. Standing "
            "upright in a neutral pose, body and face turned exactly 90 degrees "
            "to camera and looking toward frame left. Arms relaxed naturally; "
            "hands, fingers, and both feet completely visible."
        ),
    },
    {
        "filename": "fabio_back.png",
        "label": "BACK",
        "image_size": "portrait_16_9",
        "view": (
            "Full-body back view, photographed head to toe with generous white "
            "space above the hair and below both shoes. Standing upright in a "
            "neutral symmetrical pose, body facing directly away from camera. "
            "Show the back of the long wavy blonde hair and plaid shirt. Arms "
            "relaxed slightly away from the torso; hands and both feet fully visible."
        ),
    },
    {
        "filename": "fabio_three_quarter.png",
        "label": "THREE-QUARTER",
        "image_size": "portrait_16_9",
        "view": (
            "Full-body three-quarter front view, photographed head to toe with "
            "generous white space above the hair and below both shoes. Standing "
            "upright in a neutral pose, torso turned about 35 degrees while the "
            "eyes look toward camera. Arms relaxed; both complete hands, all "
            "fingers, and both feet clearly visible."
        ),
    },
    {
        "filename": "fabio_head_neutral.png",
        "label": "NEUTRAL",
        "image_size": "square_hd",
        "view": (
            "Centered close-up head-and-shoulders studio portrait, straight-on "
            "camera angle. Neutral relaxed expression, mouth closed, eyes looking "
            "directly into camera. Entire hairstyle and shoulders remain in frame."
        ),
    },
    {
        "filename": "fabio_head_smiling.png",
        "label": "SMILING",
        "image_size": "square_hd",
        "view": (
            "Centered close-up head-and-shoulders studio portrait, straight-on "
            "camera angle. Warm natural smile with a friendly expression, eyes "
            "looking directly into camera. Entire hairstyle and shoulders in frame."
        ),
    },
    {
        "filename": "fabio_head_serious.png",
        "label": "SERIOUS",
        "image_size": "square_hd",
        "view": (
            "Centered close-up head-and-shoulders studio portrait, straight-on "
            "camera angle. Serious focused expression without anger, mouth closed, "
            "eyes looking directly into camera. Entire hairstyle and shoulders in frame."
        ),
    },
]


def load_api_key() -> str:
    try:
        data = json.loads(KEY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing API key file: {KEY_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {KEY_PATH.name}: {exc}") from exc

    key = data.get("FAL_KEY")
    if not isinstance(key, str) or not key.strip():
        raise RuntimeError(f"{KEY_PATH.name} must contain a non-empty FAL_KEY field")
    return key.strip()


def image_data_uri(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing image: {path}")
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def prompt_for(asset: dict[str, str]) -> str:
    framing = (
        " Camera pulled far back. Subject occupies about 65 percent of image height. "
        "The top of his hair, both complete shoes, and visible white floor below the "
        "shoes must all be inside the frame."
        if asset["image_size"] == "portrait_16_9"
        else ""
    )
    return (
        "Create one professional character-reference photograph for the SignBridge "
        "ASL signer video project. "
        + BASE_DESCRIPTION
        + " Composition: "
        + asset["view"]
        + framing
        + " Keep Fabio's identity, apparent age, facial structure, hair length and "
        "color, complexion, body build, and clothing consistent with every view. "
        "Absolutely no writing, name labels, text, borders, contact sheet, props, "
        "or additional people."
    )


def post_generation(
    session: requests.Session,
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = session.post(
        f"{API_BASE}/{endpoint}",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        detail = response.text.replace("\n", " ")[:500]
        raise RuntimeError(f"HTTP {response.status_code}: {detail}")
    result = response.json()
    if not isinstance(result, dict):
        raise RuntimeError("API response was not a JSON object")
    return result


def extract_image(result: dict[str, Any]) -> tuple[str, str | None]:
    images = result.get("images")
    if not isinstance(images, list) or not images:
        raise RuntimeError(f"API response contained no images: {str(result)[:500]}")
    first = images[0]
    if isinstance(first, str):
        return first, None
    if not isinstance(first, dict) or not isinstance(first.get("url"), str):
        raise RuntimeError(f"Unexpected image response: {str(first)[:500]}")
    return first["url"], first.get("content_type")


def download_image(
    session: requests.Session,
    source: str,
    destination: Path,
    content_type: str | None,
) -> None:
    if source.startswith("data:"):
        header, encoded = source.split(",", 1)
        raw = base64.b64decode(encoded) if ";base64" in header else encoded.encode()
    else:
        response = session.get(source, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        raw = response.content
        content_type = response.headers.get("Content-Type", content_type)

    temp = destination.with_suffix(".download")
    temp.write_bytes(raw)
    try:
        with Image.open(temp) as image:
            image.load()
            converted = ImageOps.exif_transpose(image).convert("RGB")
            converted.save(destination, "PNG", optimize=True)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    temp.unlink(missing_ok=True)


def generate_photoreal_anchor(
    session: requests.Session,
    illustrated_reference_uri: str,
) -> str:
    prompt = (
        "Convert this illustrated Fabio identity reference into a genuinely "
        "photorealistic studio portrait of a real adult human. Handsome man with "
        "long wavy blonde hair, blue eyes, tanned complexion, red and green plaid "
        "button-down shirt with rolled sleeves, and dark jeans. Neutral expression, "
        "clean seamless white background, soft professional studio lighting, "
        "natural skin pores, fine facial hair, individual hair strands, realistic "
        "fabric and photographic lens detail. Preserve the recognizable face, hair, "
        "coloring, and wardrobe cues, but do not preserve the illustration style. "
        "No cartoon, drawing, painting, CGI, text, name label, logo, or watermark."
    )
    payload = {
        "prompt": prompt,
        "image_url": illustrated_reference_uri,
        "image_prompt_strength": 0.15,
        "aspect_ratio": "9:16",
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "2",
        "enhance_prompt": False,
        "raw": True,
        "sync_mode": False,
    }
    errors: list[str] = []
    for endpoint in FALLBACK_ENDPOINTS:
        print(f"    Calling {endpoint} ...", flush=True)
        try:
            result = post_generation(session, endpoint, payload)
            source, content_type = extract_image(result)
            download_image(session, source, TEMP_ANCHOR_PATH, content_type)
            print(f"    Photographic identity anchor created via {endpoint}", flush=True)
            return image_data_uri(TEMP_ANCHOR_PATH)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            errors.append(f"{endpoint}: {exc}")
            print(f"    Attempt failed: {exc}", flush=True)
            print("    Trying compatible fallback endpoint ...", flush=True)
            time.sleep(1)
    raise RuntimeError("Could not create photographic identity anchor:\n" + "\n".join(errors))


def generate_one(
    session: requests.Session,
    asset: dict[str, str],
    reference_uri: str,
) -> tuple[str, int | None]:
    prompt = prompt_for(asset)
    primary_payload = {
        "prompt": prompt,
        "reference_image_urls": [reference_uri],
        "negative_prompt": NEGATIVE_PROMPT,
        "image_size": asset["image_size"],
        "num_images": 1,
        "rendering_speed": "QUALITY",
        "style": "REALISTIC",
        "expand_prompt": False,
        "sync_mode": False,
    }

    attempts: list[tuple[str, dict[str, Any]]] = [(PRIMARY_ENDPOINT, primary_payload)]
    aspect_ratio = "9:16" if asset["image_size"] == "portrait_16_9" else "1:1"
    flux_payload = {
        "prompt": prompt + " Avoid: " + NEGATIVE_PROMPT + ".",
        "image_url": reference_uri,
        "image_prompt_strength": 0.35,
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "2",
        "enhance_prompt": True,
        "raw": False,
        "sync_mode": False,
    }
    attempts.extend((endpoint, flux_payload) for endpoint in FALLBACK_ENDPOINTS)

    errors: list[str] = []
    for endpoint, payload in attempts:
        print(f"    Calling {endpoint} ...", flush=True)
        try:
            result = post_generation(session, endpoint, payload)
            source, content_type = extract_image(result)
            download_image(session, source, ROOT / asset["filename"], content_type)
            seed = result.get("seed")
            return endpoint, seed if isinstance(seed, int) else None
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            errors.append(f"{endpoint}: {exc}")
            print(f"    Attempt failed: {exc}", flush=True)
            if endpoint != attempts[-1][0]:
                print("    Trying fallback endpoint ...", flush=True)
                time.sleep(1)

    raise RuntimeError("All generation endpoints failed:\n" + "\n".join(errors))


def photorealize_asset(
    session: requests.Session,
    asset: dict[str, str],
) -> tuple[str, int | None]:
    current_path = ROOT / asset["filename"]
    temp_path = ROOT / f".{current_path.stem}_photoreal.png"
    aspect_ratio = "9:16" if asset["image_size"] == "portrait_16_9" else "1:1"
    source_path = current_path
    strength = 0.15
    pose_emphasis = ""
    if asset["filename"] == "fabio_side.png":
        source_path = ROOT / "fabio_front.png"
        strength = 0.05
        pose_emphasis = (
            " STRICT TRUE LATERAL SIDE PROFILE: body, shoulders, hips, feet, nose, "
            "and face point exactly 90 degrees toward frame left. Only one eye is "
            "visible. Do not show the front of his chest."
        )
    elif asset["filename"] == "fabio_three_quarter.png":
        source_path = ROOT / "fabio_side.png"
        strength = 0.08
        pose_emphasis = (
            " STRICT THREE-QUARTER FRONT VIEW: rotate the body about 35 degrees "
            "toward frame left, clearly showing both the front and one side, while "
            "the head and eyes turn toward camera."
        )
    payload = {
        "prompt": (
            prompt_for(asset)
            + pose_emphasis
            + " Transform the supplied composition into a genuine camera photograph "
            "of a real human while preserving the requested pose, view, expression, "
            "and framing. Avoid: "
            + NEGATIVE_PROMPT
            + "."
        ),
        "image_url": image_data_uri(source_path),
        "image_prompt_strength": strength,
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "2",
        "enhance_prompt": False,
        "raw": True,
        "sync_mode": False,
    }
    endpoint = FALLBACK_ENDPOINTS[-1]
    print(f"    Applying final photoreal pass via {endpoint} ...", flush=True)
    try:
        result = post_generation(session, endpoint, payload)
        source, content_type = extract_image(result)
        download_image(session, source, temp_path, content_type)
        temp_path.replace(current_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    seed = result.get("seed")
    return endpoint, seed if isinstance(seed, int) else None


def tighten_headshot(path: Path) -> None:
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        original_size = source.size
        crop_size = int(min(source.size) * 0.58)
        left = (source.width - crop_size) // 2
        top = max(0, int(source.height * 0.015))
        cropped = source.crop((left, top, left + crop_size, top + crop_size))
        cropped.resize(original_size, Image.Resampling.LANCZOS).save(
            path, "PNG", optimize=True
        )


def fitted_tile(path: Path, size: tuple[int, int], padding: int = 20) -> Image.Image:
    tile = Image.new("RGB", size, "white")
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        contained = ImageOps.contain(
            source,
            (size[0] - padding * 2, size[1] - padding * 2),
            Image.Resampling.LANCZOS,
        )
    x = (size[0] - contained.width) // 2
    y = (size[1] - contained.height) // 2
    tile.paste(contained, (x, y))
    return tile


def make_character_sheet() -> None:
    width = 2400
    title_height = 100
    label_height = 52
    body_height = 1020
    head_height = 650
    column_width = 600
    canvas = Image.new(
        "RGB",
        (width, title_height + body_height + label_height + head_height + label_height),
        (245, 245, 245),
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=28)
    title_font = ImageFont.load_default(size=44)
    title = "FABIO - SIGNBRIDGE CHARACTER REFERENCE"
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((width - (title_box[2] - title_box[0])) // 2, 25), title, fill=(30, 30, 30), font=title_font)

    body_assets = ASSETS[:4]
    for index, asset in enumerate(body_assets):
        x = index * column_width
        canvas.paste(fitted_tile(ROOT / asset["filename"], (column_width, body_height)), (x, title_height))
        label = asset["label"]
        box = draw.textbbox((0, 0), label, font=font)
        draw.text(
            (x + (column_width - (box[2] - box[0])) // 2, title_height + body_height + 10),
            label,
            fill=(35, 35, 35),
            font=font,
        )

    head_assets = ASSETS[4:]
    head_start_y = title_height + body_height + label_height
    total_head_width = len(head_assets) * column_width
    head_start_x = (width - total_head_width) // 2
    for index, asset in enumerate(head_assets):
        x = head_start_x + index * column_width
        canvas.paste(fitted_tile(ROOT / asset["filename"], (column_width, head_height)), (x, head_start_y))
        label = asset["label"]
        box = draw.textbbox((0, 0), label, font=font)
        draw.text(
            (x + (column_width - (box[2] - box[0])) // 2, head_start_y + head_height + 10),
            label,
            fill=(35, 35, 35),
            font=font,
        )

    canvas.save(ROOT / "fabio_character_sheet.png", "PNG", optimize=True)


def make_preview_html() -> None:
    body_cards = "\n".join(
        f'''<figure><img src="{a["filename"]}" alt="Fabio {a["label"].lower()} view"><figcaption>{a["label"]}</figcaption></figure>'''
        for a in ASSETS[:4]
    )
    head_cards = "\n".join(
        f'''<figure><img src="{a["filename"]}" alt="Fabio {a["label"].lower()} headshot"><figcaption>{a["label"]}</figcaption></figure>'''
        for a in ASSETS[4:]
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fabio — SignBridge Character Sheet</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    body {{ margin: 0; padding: 32px; background: #ececec; color: #202020; }}
    main {{ max-width: 1600px; margin: auto; }}
    h1, p {{ text-align: center; }}
    .sheet {{ display: block; width: 100%; height: auto; margin: 28px 0 42px; background: white;
              box-shadow: 0 8px 28px #0002; }}
    .grid {{ display: grid; gap: 20px; margin-bottom: 20px; }}
    .body-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .head-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); max-width: 1200px; margin-inline: auto; }}
    figure {{ margin: 0; background: white; box-shadow: 0 4px 18px #0002; }}
    figure img {{ display: block; width: 100%; aspect-ratio: 3 / 4; object-fit: contain; background: white; }}
    .head-grid figure img {{ aspect-ratio: 1 / 1; }}
    figcaption {{ padding: 12px; text-align: center; font-weight: 700; letter-spacing: .08em; }}
    @media (max-width: 800px) {{
      .body-grid, .head-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      body {{ padding: 16px; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Fabio — SignBridge Character Reference</h1>
    <p>Photorealistic reference views for Dreamactor video generation</p>
    <img class="sheet" src="fabio_character_sheet.png" alt="Complete Fabio character sheet">
    <section class="grid body-grid">{body_cards}</section>
    <section class="grid head-grid">{head_cards}</section>
  </main>
</body>
</html>
"""
    (ROOT / "preview.html").write_text(html, encoding="utf-8")


def main() -> int:
    print("Fabio character sheet generator", flush=True)
    print(f"Reference: {REFERENCE_PATH.name}", flush=True)
    try:
        api_key = load_api_key()
        illustrated_reference_uri = image_data_uri(REFERENCE_PATH)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    with requests.Session() as session:
        session.headers.update(
            {
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "SignBridge-character-sheet/1.0",
            }
        )
        print("[setup] Creating a photorealistic identity anchor", flush=True)
        try:
            reference_uri = generate_photoreal_anchor(session, illustrated_reference_uri)
        except Exception as exc:
            print(f"ERROR preparing photographic identity: {exc}", file=sys.stderr)
            return 1

        for index, asset in enumerate(ASSETS, start=1):
            destination = ROOT / asset["filename"]
            print(f"[{index}/{len(ASSETS)}] Generating {asset['filename']}", flush=True)
            try:
                composition_endpoint, _ = generate_one(session, asset, reference_uri)
                endpoint, seed = photorealize_asset(session, asset)
                if asset["image_size"] == "square_hd":
                    tighten_headshot(destination)
            except Exception as exc:
                print(f"ERROR generating {asset['filename']}: {exc}", file=sys.stderr)
                return 1
            suffix = f", final seed {seed}" if seed is not None else ""
            print(
                f"    Saved {destination.name} via {composition_endpoint} + {endpoint}{suffix}",
                flush=True,
            )

    TEMP_ANCHOR_PATH.unlink(missing_ok=True)
    print("[8/9] Compositing fabio_character_sheet.png", flush=True)
    make_character_sheet()
    print("[9/9] Writing preview.html", flush=True)
    make_preview_html()

    created = [a["filename"] for a in ASSETS] + [
        "fabio_character_sheet.png",
        "preview.html",
    ]
    print("\nCreated files:", flush=True)
    for name in created:
        path = ROOT / name
        print(f"  - {name} ({path.stat().st_size:,} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
