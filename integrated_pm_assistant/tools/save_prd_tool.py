from google.adk.tools.function_tool import FunctionTool
from pathlib import Path
from typing import List
from .prd_pdf_writer import save_prd_pdf
import json


def save_prd(
    product_name: str,
    problem_statement: str,
    goals: List[str],
    user_personas: List[str],
    functional_requirements: List[str],
    non_functional_requirements: List[str],
    constraints: List[str],
    assumptions: List[str],
    out_of_scope: List[str],
) -> dict:

    prd_data = {
        "product_name": product_name,
        "problem_statement": problem_statement,
        "goals": goals,
        "user_personas": user_personas,
        "functional_requirements": functional_requirements,
        "non_functional_requirements": non_functional_requirements,
        "constraints": constraints,
        "assumptions": assumptions,
        "out_of_scope": out_of_scope,
    }

    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / f"{product_name}_PRD.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(prd_data, f, indent=4)

    print(f"✅ PRD JSON saved at: {json_path}")

    pdf_path = save_prd_pdf(prd_data, product_name)
    print(f"✅ PRD PDF saved at: {pdf_path}")

    return {"project_name": product_name}


save_prd_tool = FunctionTool(save_prd)