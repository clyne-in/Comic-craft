import json 
import logging
from typing import List 
 
from google import genai 
from google.genai import types 
from pydantic import BaseModel 
 
from app.ai.config import get_settings 
from app.ai.schemas import ( 
    OutlineResponse, 
    StoryPanel, 
    StoryResponse, 
) 


logger = logging.getLogger(__name__)
 
 
class GeminiStorySchema(BaseModel): 
    panels: List[StoryPanel] 
 
 
def _mock_story( 
    outline: OutlineResponse, 
    character_name: str, 
    tone: str 
) -> StoryResponse: 
 
    panels = [] 
 
    for panel in outline.panels: 
 
        panels.append( 
            StoryPanel( 
                panel_number=panel.panel_number, 
                title=panel.title, 
                scene_description=panel.scene_description, 
                caption=( 
                    "Meanwhile, the story takes " 
                    "an unexpected turn." 
                ), 
                narration=( 
                    f"{character_name} takes a deep breath " 
                    "and moves forward, determined to solve " 
                    "the mystery." 
                ), 
                dialogue=( 
                    f'"We can do this," says ' 
                    f'{character_name}.' 
                ), 
                image_prompt=panel.image_prompt, 
            ) 
        ) 
 
    return StoryResponse(panels=panels) 
 
 
def generate_story( 
    outline: OutlineResponse, 
    character_name: str, 
    tone: str 
) -> StoryResponse: 
 
    settings = get_settings() 
 
    if ( 
        settings.app_mode.lower() != "live" 
        or not settings.gemini_api_key 
    ): 
        return _mock_story( 
            outline, 
            character_name, 
            tone 
        ) 
 
    client = genai.Client( 
        api_key=settings.gemini_api_key 
    ) 
 
    outline_json = outline.model_dump_json( 
        indent=2 
    ) 
 
    prompt = f""" 
Expand this 5-panel comic outline into 
polished comic narration and dialogue. 
 
Main character: 
{character_name} 
 
Tone: 
{tone} 
 
Outline: 
 
{outline_json} 
 
For every panel preserve: 
 
- panel_number 
- title 
- scene_description 
- image_prompt 
 
Add: 
 
- caption 
- narration 
- dialogue 
 
Caption should be a short ambient/action caption. 
 
Narration should contain 1-3 engaging sentences. 
 
Dialogue should be natural character dialogue. 
Use an empty string if dialogue is unnecessary. 
 
Make the story coherent from panel 1 through 
panel 5. 
 
Return only valid JSON matching the requested schema. 
""" 
 
    try:
        response = client.models.generate_content( 
            model=settings.gemini_story_model, 
            contents=prompt, 
            config=types.GenerateContentConfig( 
                response_mime_type="application/json", 
                response_schema=GeminiStorySchema, 
                temperature=0.9, 
            ), 
        ) 

        data = json.loads(response.text) 

        result = StoryResponse.model_validate(data) 

        if len(result.panels) != 5: 
            raise ValueError( 
                "Gemini did not return exactly 5 story panels." 
            )

        return result

    except Exception as exc:
        logger.warning("Falling back to mock story: %s", exc)
        return _mock_story(
            outline,
            character_name,
            tone
        )