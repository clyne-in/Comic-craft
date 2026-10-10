from pathlib import Path
from datetime import datetime

from fpdf import FPDF
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent.parent.parent

EXPORT_DIR = (
    BASE_DIR
    / "static"
    / "exports"
)

PANEL_DIR = (
    BASE_DIR
    / "static"
    / "panels"
)


def _ascii(text: str) -> str:

    text = text or ""

    return (
        text
        .encode(
            "latin-1",
            "replace"
        )
        .decode("latin-1")
    )


def _image_path(
    image_url: str
) -> Path:

    filename = (
        image_url
        .rsplit("/", 1)[-1]
    )

    path = PANEL_DIR / filename

    if not path.exists():

        raise FileNotFoundError(
            f"Image not found: {path}"
        )

    return path


def save_pdf(
    layout,
    comic_id: str
) -> str:

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"comic_{comic_id}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ".pdf"
    )

    output = EXPORT_DIR / filename

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4"
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=14
    )

    for panel in layout:

        pdf.add_page()

        # Panel title
        pdf.set_font(
            "Helvetica",
            "B",
            18
        )

        pdf.multi_cell(
            0,
            10,
            _ascii(
                f"Panel {panel.panel_number}: "
                f"{panel.title}"
            )
        )

        image_path = _image_path(
            panel.image_url
        )

        with Image.open(
            image_path
        ) as image:

            width, height = image.size

        max_width = 180
        max_height = 100

        scale = min(
            max_width / width,
            max_height / height
        )

        image_width = width * scale
        image_height = height * scale

        x = (
            210 - image_width
        ) / 2

        pdf.image(
            str(image_path),
            x=x,
            y=35,
            w=image_width,
            h=image_height
        )

        pdf.set_y(
            35 + image_height + 8
        )

        pdf.set_x(14)

        text_width = pdf.w - pdf.l_margin - pdf.r_margin

        # Scene
        pdf.set_font(
            "Helvetica",
            "I",
            10
        )

        pdf.multi_cell(
            text_width,
            6,
            _ascii(
                panel.scene_description
            )
        )

        # Caption
        pdf.set_font(
            "Helvetica",
            "B",
            11
        )

        pdf.multi_cell(
            text_width,
            7,
            _ascii(
                "Caption: "
                + panel.caption
            )
        )

        # Narration
        pdf.set_font(
            "Helvetica",
            "",
            11
        )

        pdf.multi_cell(
            text_width,
            7,
            _ascii(
                panel.narration
            )
        )

        # Dialogue
        if panel.dialogue:

            pdf.set_font(
                "Helvetica",
                "I",
                11
            )

            pdf.multi_cell(
                text_width,
                7,
                _ascii(
                    "Dialogue: "
                    + panel.dialogue
                )
            )

    pdf.output(
        str(output)
    )

    return (
        f"/static/exports/{filename}"
    )