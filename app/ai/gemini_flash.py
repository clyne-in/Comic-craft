import json
import logging
from typing import List

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.config import get_settings
from app.ai.schemas import PanelOutline, OutlineResponse


logger = logging.getLogger(__name__)


class GeminiOutlineSchema(BaseModel):
    panels: List[PanelOutline]


def _mock_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
) -> OutlineResponse:

    stages = [
        (
            "The Beginning",
            f"{character_name} arrives in {setting}, "
            "where an unexpected mystery begins."
        ),
        (
            "The Discovery",
            f"{character_name} discovers a strange clue "
            "and decides to investigate."
        ),
        (
            "The Challenge",
            f"An unexpected obstacle tests "
            f"{character_name}'s courage and creativity."
        ),
        (
            "The Turning Point",
            f"{character_name} finds a clever way forward "
            "and learns something important."
        ),
        (
            "The Finale",
            f"The mystery is resolved, leaving "
            f"{character_name} with a memorable new story."
        ),
    ]

    panels = []

    for number, (title, description) in enumerate(
        stages,
        start=1
    ):

        image_prompt = (
            f"5-panel comic illustration, panel {number}, "
            f"{art_style}, {tone} mood, "
            f"main character {character_name}, "
            f"setting {setting}, "
            f"story idea: {story_prompt}, "
            "cinematic composition, expressive characters, "
            "clean line art, detailed background, "
            "visual storytelling"
        )

        panels.append(
            PanelOutline(
                panel_number=number,
                title=title,
                scene_description=description,
                image_prompt=image_prompt
            )
        )

    return OutlineResponse(panels=panels)


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
) -> OutlineResponse:

    settings = get_settings()

    # Mock mode allows testing without API keys.
    if (
        settings.app_mode.lower() != "live"
        or not settings.gemini_api_key
    ):
        return _mock_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style
        )

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    prompt = f"""
Create a coherent 5-panel comic outline.

Story prompt:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Return exactly 5 panels.

Each panel must contain:

- panel_number from 1 to 5
- short title
- scene_description
- detailed image_prompt suitable for a text-to-image model

Keep the same main character visually consistent
across all panels.

Do not include markdown or additional commentary.
"""

    try:
        response = client.models.generate_content(
            model=settings.gemini_outline_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiOutlineSchema,
                temperature=0.9,
            ),
        )

        data = json.loads(response.text)

        result = OutlineResponse.model_validate(data)

        if len(result.panels) != 5:
            raise ValueError(
                "Gemini did not return exactly 5 panels."
            )

        return result

    except Exception as exc:
        logger.warning("Falling back to mock outline: %s", exc)
        return _mock_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style
        )