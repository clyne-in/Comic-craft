import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)

from fastapi.templating import Jinja2Templates

from app.ai.config import get_settings

from app.ai.schemas import (
    PromptRequest,
    ComicResponse,
)

from app.ai.gemini_flash import (
    generate_outline
)

from app.ai.gemini_pro import (
    generate_story
)

from app.ai.image_generator import (
    generate_image
)

from app.ai.layout_builder import (
    build_comic_layout
)

from app.ai.exporters import (
    save_pdf
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent.parent
)


templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


router = APIRouter()


# Simple in-memory storage.
# Suitable for local development.
COMICS = {}


@router.get(
    "/",
    response_class=HTMLResponse
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "settings": get_settings()
        }
    )


def _generate_comic(
    data: PromptRequest
):

    comic_id = (
        uuid.uuid4()
        .hex[:12]
    )

    # Step 1:
    # Generate five-panel outline
    outline = generate_outline(
        data.story_prompt,
        data.character_name,
        data.setting,
        data.tone,
        data.art_style
    )

    # Step 2:
    # Generate narration and dialogue
    story = generate_story(
        outline,
        data.character_name,
        data.tone
    )

    # Step 3:
    # Generate image for every panel
    image_urls = []

    for panel in story.panels:

        image_url = generate_image(
            panel.image_prompt,
            panel.panel_number,
            filename_hint=(
                f"{comic_id}_{panel.title}"
            )
        )

        image_urls.append(
            image_url
        )

    # Step 4:
    # Build final layout
    layout = build_comic_layout(
        story,
        image_urls
    )

    # Step 5:
    # Create PDF
    pdf_url = save_pdf(
        layout,
        comic_id
    )

    # Save basic metadata
    COMICS[comic_id] = {
        "request": data.model_dump(),
        "layout": [
            panel.model_dump()
            for panel in layout
        ],
        "pdf_url": pdf_url
    }

    return (
        comic_id,
        layout,
        pdf_url
    )


@router.post(
    "/generate",
    response_class=HTMLResponse
)
def generate(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...)
):

    try:

        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        (
            comic_id,
            layout,
            pdf_url
        ) = _generate_comic(data)

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "comic_id": comic_id,
                "pdf_url": pdf_url,
                "error": None,
            }
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": [],
                "comic_id": None,
                "pdf_url": None,
                "error": str(exc),
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
    response_model=ComicResponse,
    tags=["API"]
)
def generate_comic_json(
    payload: PromptRequest
):

    try:

        (
            comic_id,
            layout,
            pdf_url
        ) = _generate_comic(
            payload
        )

        return ComicResponse(
            comic_id=comic_id,
            panels=layout,
            pdf_url=pdf_url
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Comic generation failed: "
                f"{exc}"
            )
        ) from exc


@router.get(
    "/export/{comic_id}",
    tags=["API"]
)
def export_comic(
    comic_id: str
):

    comic = COMICS.get(
        comic_id
    )

    if not comic:

        raise HTTPException(
            status_code=404,
            detail=(
                "Comic not found. "
                "Generate a new comic."
            )
        )

    relative = (
        comic["pdf_url"]
        .replace(
            "/static/",
            "",
            1
        )
    )

    pdf_path = (
        BASE_DIR
        / "static"
        / relative
    )

    if not pdf_path.exists():

        raise HTTPException(
            status_code=404,
            detail="PDF file no longer exists."
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name
    )


@router.get(
    "/export-success/{comic_id}",
    response_class=HTMLResponse
)
def export_success(
    request: Request,
    comic_id: str
):

    if comic_id not in COMICS:

        raise HTTPException(
            status_code=404,
            detail="Comic not found."
        )

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "comic_id": comic_id
        }
    )


@router.get(
    "/test-image",
    response_class=HTMLResponse,
    tags=["developer"]
)
def test_image(
    request: Request,
    prompt: str = (
        "A cheerful fox exploring "
        "an enchanted forest, "
        "comic book art"
    )
):

    try:

        image_url = generate_image(
            prompt,
            0,
            "test"
        )

        return templates.TemplateResponse(
            request=request,
            name="image_test.html",
            context={
                "image_url": image_url,
                "prompt": prompt,
                "error": None
            }
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="image_test.html",
            context={
                "image_url": None,
                "prompt": prompt,
                "error": str(exc)
            },
            status_code=500
        )