from typing import List

from app.ai.schemas import (
    StoryResponse,
    LayoutPanel,
)


def build_comic_layout(
    story: StoryResponse,
    image_urls: List[str]
) -> List[LayoutPanel]:

    if len(story.panels) != len(image_urls):

        raise ValueError(
            "Every story panel must have "
            "a matching image."
        )

    layout = []

    for index, panel in enumerate(
        story.panels
    ):

        layout.append(
            LayoutPanel(
                panel_number=panel.panel_number,
                title=panel.title,
                image_url=image_urls[index],
                scene_description=(
                    panel.scene_description
                ),
                caption=panel.caption,
                narration=panel.narration,
                dialogue=panel.dialogue,
                image_prompt=panel.image_prompt,
            )
        )

    return layout