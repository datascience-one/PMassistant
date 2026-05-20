from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def save_prd_pdf(prd: dict, project_name: str):

    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / f"{project_name}_PRD.pdf"

    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    def heading(text):
        story.append(Paragraph(f"<b>{text}</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))

    def body(text):
        story.append(Paragraph(str(text), styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Product Requirement Document</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    for key, value in prd.items():
        heading(key.replace("_", " ").title())
        if isinstance(value, list):
            for item in value:
                body(f"• {item}")
        else:
            body(value)

    doc.build(story)

    print(f"✅ PRD PDF saved at: {file_path}")

    return str(file_path)
