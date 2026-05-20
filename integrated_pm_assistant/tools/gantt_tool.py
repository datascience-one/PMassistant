import pandas as pd
import plotly.express as px
import json
import re
from pathlib import Path
from google.adk.tools.function_tool import FunctionTool

def _safe_json_parse(raw_input):
    if isinstance(raw_input, dict): return raw_input
    raw_str = str(raw_input)
    match = re.search(r'\{.*\}', raw_str, re.DOTALL)
    if not match: raise ValueError("No JSON object found")
    cleaned = re.sub(r'\bNaN\b', 'null', match.group(0))
    return json.loads(cleaned)


def _apply_dependency_scheduling(df, project_start):
    """
    FIXED: True parallel scheduling for independent tasks
    """

    df = df.copy()
    end_dates = {}

    # Normalize dependencies column
    if "dependencies" not in df.columns:
        df["dependencies"] = [[] for _ in range(len(df))]

    # Convert string dependencies to list
    def parse_deps(dep):
        if isinstance(dep, str):
            try:
                return json.loads(dep)
            except:
                return []
        return dep if isinstance(dep, list) else []

    df["dependencies"] = df["dependencies"].apply(parse_deps)

    # 🔥 STEP 1: Handle tasks with NO dependencies (PARALLEL)
    no_dep_mask = df["dependencies"].apply(lambda x: len(x) == 0)

    df.loc[no_dep_mask, "start_date"] = project_start

    for idx in df[no_dep_mask].index:
        duration = (df.at[idx, "end_date"] - df.at[idx, "start_date"]).days
        df.at[idx, "end_date"] = df.at[idx, "start_date"] + pd.Timedelta(days=duration)
        end_dates[df.at[idx, "task_name"]] = df.at[idx, "end_date"]

    # 🔥 STEP 2: Handle dependent tasks (ITERATIVE, NOT SEQUENTIAL ORDER)
    unresolved = df[~no_dep_mask].copy()

    while not unresolved.empty:
        resolved_in_this_pass = False
        for idx, row in unresolved.iterrows():
            deps = row["dependencies"]

            # Check if all dependencies are already scheduled
            if all(dep in end_dates for dep in deps):
                start = max(end_dates[dep] for dep in deps)

                duration = (row["end_date"] - row["start_date"]).days
                end = start + pd.Timedelta(days=duration)

                df.at[idx, "start_date"] = start
                df.at[idx, "end_date"] = end

                end_dates[row["task_name"]] = end
                resolved_in_this_pass = True

        if not resolved_in_this_pass:
            print(f"⚠️ Warning: Circular dependency or missing task detected. Stopping scheduling for: {unresolved['task_name'].tolist()}")
            break

        # Remove resolved tasks
        unresolved = df[
            df["task_name"].apply(lambda x: x not in end_dates)
        ]

    return df

def generate_gantt_chart(input_json: str) -> str:
    try:
        data = _safe_json_parse(input_json)
        project_name = data["project_name"]
        tasks = data.get("tasks", [])

        df = pd.DataFrame(tasks)

        # Ensure dates are in datetime format
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["end_date"] = pd.to_datetime(df["end_date"])

        # NEW: Fix waterfall issue
        project_start = df["start_date"].min()
        df = _apply_dependency_scheduling(df, project_start)

        fig = px.timeline(
            df, 
            x_start="start_date",  
            x_end="end_date",    
            y="task_name",
            color="assigned_empl",
            title=f"Project Roadmap: {project_name}",
            hover_data={
                "assigned_email": True,
                "project_manager": True,
                "RACI": True,
                "start_date": "|%b %d, %Y",
                "end_date": "|%b %d, %Y"
            }
        )

        fig.update_yaxes(autorange="reversed") 
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        html_path = output_dir / f"{project_name}_Gantt.html"
        fig.write_html(str(html_path))
        
        png_path = output_dir / f"{project_name}_Gantt.png"
        fig.write_image(str(png_path))

        print(f"📊 Gantt HTML: {html_path}")
        print(f"🖼️ Gantt PNG: {png_path}")

        return json.dumps({
            "status": "Success", 
            "html_path": str(html_path),
            "png_path": str(png_path)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Gantt Tool failed: {str(e)}"})


gantt_chart_tool = FunctionTool(generate_gantt_chart)