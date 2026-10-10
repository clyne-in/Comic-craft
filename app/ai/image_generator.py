from pathlib import Path
import re
import logging

from PIL import Image, ImageDraw
from huggingface_hub import InferenceClient

from app.ai.config import get_settings


logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

PANEL_DIR = (
    BASE_DIR
    / "static"
    / "panels"
)


def _safe_name(text: str) -> str:

    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text
    )

    text = text.strip("_")

    return text[:70] or "panel"


def _mock_image(
    prompt: str,
    output_path: Path,
    panel_number: int
) -> None:

    image = Image.new(
        "RGB",
        (768, 512),
        "white"
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (20, 20, 748, 492),
        outline="black",
        width=5
    )

    draw.text(
        (45, 55),
        f"COMIC PANEL {panel_number}",
        fill="black"
    )

    words = prompt.split()

    preview = " ".join(
        words[:35]
    )

    draw.text(
        (45, 115),
        preview,
        fill="black"
    )

    draw.text(
        (45, 420),
        "Mock image mode - add HF_TOKEN for AI images.",
        fill="black"
    )

    image.save(
        output_path,
        "PNG"
    )


def generate_image(
    prompt: str,
    panel_number: int,
    filename_hint: str = ""
) -> str:

    settings = get_settings()

    PANEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"panel_{panel_number}_"
        f"{_safe_name(filename_hint or prompt)}.png"
    )

    output_path = PANEL_DIR / filename

    # Development/testing mode
    if (
        settings.app_mode.lower() != "live"
        or not settings.hf_token
    ):

        _mock_image(
            prompt,
            output_path,
            panel_number
        )

        return (
            f"/static/panels/{filename}"
        )

    try:
        client = InferenceClient(
            provider=settings.hf_provider,
            api_key=settings.hf_token,
        )

        image = client.text_to_image(
            prompt=prompt,
            model=settings.hf_image_model,
            width=settings.image_width,
            height=settings.image_height,
            num_inference_steps=settings.image_steps,
            guidance_scale=settings.image_guidance,
            negative_prompt=(
                "blurry, distorted, extra fingers, "
                "duplicate characters, unreadable text, "
                "watermark"
            ),
        )

        image.save(
            output_path
        )

    except Exception as exc:
        logger.warning("Falling back to mock image: %s", exc)
        _mock_image(
            prompt,
            output_path,
            panel_number
        )

    return (
        f"/static/panels/{filename}"
    )