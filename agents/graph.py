from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from agents.requirement_agent import run_requirement_agent
from agents.component_agent import run_component_agent
from agents.schematic_agent import run_schematic_agent
from agents.validation_agent import run_validation_agent
from agents.firmware_agent import run_firmware_agent
from rag.vector_db import query_datasheets

class AgentState(TypedDict):
    user_prompt: str
    requirements: Dict[str, Any]
    components: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    validation: Dict[str, Any]
    firmware: str
    final_report: str
    iteration_count: int
    feedback_notes: str

def requirements_node(state: AgentState) -> Dict[str, Any]:
    print("[Graph] Running Requirements Extraction Agent...")
    reqs = run_requirement_agent(state["user_prompt"])
    return {"requirements": reqs}

def components_node(state: AgentState) -> Dict[str, Any]:
    print("[Graph] Running Component Selection Agent...")
    reqs = state["requirements"]
    if state.get("feedback_notes"):
        reqs = {**reqs, "feedback_notes": state["feedback_notes"]}

    result = run_component_agent(reqs)
    return {
        "components": result.get("components", []),
        "iteration_count": state.get("iteration_count", 0) + 1
    }

def schematic_node(state: AgentState) -> Dict[str, Any]:
    print("[Graph] Running Schematic Design Agent...")
    result = run_schematic_agent(state["requirements"], state["components"])
    return {"connections": result.get("connections", [])}

def validation_node(state: AgentState) -> Dict[str, Any]:
    print("[Graph] Running Validation Agent (including RAG checks)...")

    rag_context = ""
    try:
        keywords = []
        for c in state["components"]:
            keywords.extend(c.get("datasheet_keywords", []))

        if keywords:
            query = " ".join(keywords[:5])
            docs = query_datasheets(query, limit=3)
            rag_context = "\n".join([f"Source: {d.metadata.get('source', 'Datasheet')}\nContent: {d.page_content}" for d in docs])
    except Exception as e:
        print(f"[RAG] Skipping vector search due to lack of connection or index: {e}")
        rag_context = "No specific datasheet matches found in vector DB."

    report = run_validation_agent(state["requirements"], state["components"], state["connections"], RAG_context=rag_context)

    issues_list = report.get("items", [])
    high_severity_issues = [iss for iss in issues_list if iss.get("severity") == "High"]

    feedback_notes = ""
    if high_severity_issues:
        feedback_notes = "Please resolve the following critical validation issues:\n" + "\n".join(
            [f"- {iss['issues']}. Proposed fix: {iss['fixes']}" for iss in high_severity_issues]
        )

    return {
        "validation": report,
        "feedback_notes": feedback_notes
    }

def firmware_node(state: AgentState) -> Dict[str, Any]:
    print("[Graph] Running Firmware Generation Agent...")
    code = run_firmware_agent(state["requirements"], state["components"], state["connections"])
    return {"firmware": code}

def report_node(state: AgentState) -> Dict[str, Any]:
    print("[Graph] Compiling final project report...")

    reqs = state["requirements"]
    comps = state["components"]
    conns = state["connections"]
    val = state["validation"]
    firm = state["firmware"]

    report_md = f"""# CircuitMind Design Report: {reqs.get('microcontroller', 'Embedded System')}

## 1. System Requirements Summary
- **Controller**: {reqs.get('microcontroller')}
- **Sensors**: {', '.join(reqs.get('sensors', [])) or 'None'}
- **Actuators**: {', '.join(reqs.get('actuators', [])) or 'None'}
- **Communication**: {', '.join(reqs.get('communication', [])) or 'None'}
- **Power specs**: {reqs.get('power')}
- **Cloud integration**: {', '.join(reqs.get('cloud_services', [])) or 'None'}

## 2. Component Recommendations & BOM
| Component | Purpose & Selection Reason | Datasheet Keywords |
|---|---|---|
"""
    for c in comps:
        report_md += f"| **{c['name']}** | {c['reason']} | `{', '.join(c['datasheet_keywords'])}` |\n"

    report_md += "\n## 3. Physical Pin Connections & Wiring Diagram\n"
    report_md += "| From Device | From Pin | To Device | To Pin | Signal Type |\n|---|---|---|---|---|\n"
    for cn in conns:
        report_md += f"| {cn['from_component']} | {cn['from_pin']} | {cn['to_component']} | {cn['to_pin']} | {cn['connection_type']} |\n"

    report_md += "\n## 4. Electrical Validation Checks\n"
    issues = val.get("items", [])
    if not issues:
        report_md += "✅ No electrical, voltage, or logic-level conflicts detected.\n"
    else:
        report_md += "| Issue Identified | Severity | Proposed Fix |\n|---|---|---|\n"
        for iss in issues:
            report_md += f"| {iss['issues']} | **{iss['severity']}** | {iss['fixes']} |\n"

    report_md += f"\n## 5. ESP32/Arduino Firmware\n```cpp\n{firm}\n```\n"

    return {"final_report": report_md}

def should_continue(state: AgentState) -> Literal["components", "firmware"]:
    val = state.get("validation", {})
    issues = val.get("items", [])
    high_issues = [iss for iss in issues if iss.get("severity") == "High"]

    if high_issues and state.get("iteration_count", 0) < 3:
        print(f"[Graph Routing] Critical issues found! Routing to Component node for self-healing (Iteration {state.get('iteration_count')})")
        return "components"

    print("[Graph Routing] Design valid or retry limit reached. Routing to Firmware node...")
    return "firmware"

def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("requirements", requirements_node)
    workflow.add_node("components", components_node)
    workflow.add_node("schematic", schematic_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("firmware", firmware_node)
    workflow.add_node("report", report_node)

    workflow.add_edge(START, "requirements")
    workflow.add_edge("requirements", "components")
    workflow.add_edge("components", "schematic")
    workflow.add_edge("schematic", "validation")

    workflow.add_conditional_edges(
        "validation",
        should_continue,
        {
            "components": "components",
            "firmware": "firmware"
        }
    )

    workflow.add_edge("firmware", "report")
    workflow.add_edge("report", END)

    return workflow.compile()
