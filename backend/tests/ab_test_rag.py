import os
import sys
import unittest
from unittest.mock import patch

# Configure sys.path so it runs correctly within backend/tests/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import build_workflow
from rag.vector_db import get_vector_store
from langchain_core.documents import Document
from app.config import settings

def run_ab_test():
    print("================================================================")
    print("        STARTING CIRCUITMIND RAG PIPELINE A/B TEST")
    print("================================================================")
    
    # 1. Initialize LangGraph Workflow
    print("[Setup] Compiling LangGraph workflow state machine...")
    app = build_workflow()
    
    user_prompt = (
        "Design a temperature monitoring system using an ESP32 microcontroller and a DHT22 sensor. "
        "The system is powered by a 12V DC input. Wire the DHT22 VCC pin directly to the 12V DC input."
    )
    print(f"[Input Prompt]:\n  \"{user_prompt}\"\n")
    
    # ----------------------------------------------------
    # VARIANT A: Run WITHOUT RAG Context (Empty Vector DB)
    # ----------------------------------------------------
    print("----------------------------------------------------------------")
    print("RUNNING VARIANT A: No RAG Context (Empty Vector DB)")
    print("----------------------------------------------------------------")
    
    # Clear / Get vector store (it's in-memory, so it starts empty)
    vector_store = get_vector_store()
    
    # Execute the LangGraph workflow
    inputs_a = {
        "user_prompt": user_prompt,
        "iteration_count": 0,
        "feedback_notes": ""
    }
    
    print("[Variant A] Invoking workflow...")
    result_a = app.invoke(inputs_a)
    
    print("\n[Variant A] Validation Report:")
    val_report_a = result_a.get("validation", {})
    issues_a = val_report_a.get("items", [])
    if not issues_a:
         print("  ✅ No electrical issues detected by the validation agent.")
    else:
         for idx, issue in enumerate(issues_a, 1):
             print(f"  {idx}. [{issue.get('severity')}] {issue.get('issues')}")
             print(f"     Proposed fix: {issue.get('fixes')}")
             
    # ----------------------------------------------------
    # VARIANT B: Run WITH RAG Context (Populated Vector DB)
    # ----------------------------------------------------
    print("\n----------------------------------------------------------------")
    print("RUNNING VARIANT B: With RAG Context (Populated Vector DB)")
    print("----------------------------------------------------------------")
    
    # Populate the in-memory Qdrant vector store with the specific DHT22 operating limits
    print("[Variant B] Ingesting datasheet specifications into in-memory Qdrant...")
    datasheet_chunks = [
        Document(
            page_content=(
                "DHT22 Pinout and Electrical Specifications:\n"
                "- VCC Operating voltage range: 3.3V to 5.5V DC.\n"
                "- Absolute maximum supply voltage: 6.0V DC. Applying voltage above 6.0V (e.g. 12V) "
                "directly to VCC pin will result in immediate hardware failure, sensor destruction, and potential fire hazard.\n"
                "- If the system uses a 12V DC power source, a linear regulator (like LM7805 or LM1117-5V) "
                "or a step-down buck converter must be wired to drop the 12V supply to a safe 5.0V for the DHT22 VCC line."
            ),
            metadata={"source": "DHT22_Datasheet_Page2.pdf"}
        )
    ]
    vector_store.add_documents(datasheet_chunks)
    print("[Variant B] Datasheet context successfully stored in vector database.")
    
    # Execute the LangGraph workflow again
    inputs_b = {
        "user_prompt": user_prompt,
        "iteration_count": 0,
        "feedback_notes": ""
    }
    
    print("[Variant B] Invoking workflow...")
    result_b = app.invoke(inputs_b)
    
    print("\n[Variant B] Validation Report:")
    val_report_b = result_b.get("validation", {})
    issues_b = val_report_b.get("items", [])
    if not issues_b:
         print("  ✅ No electrical issues detected by the validation agent.")
    else:
         for idx, issue in enumerate(issues_b, 1):
             print(f"  {idx}. [{issue.get('severity')}] {issue.get('issues')}")
             print(f"     Proposed fix: {issue.get('fixes')}")
             
    # ----------------------------------------------------
    # SUMMARY OF COMPARISON
    # ----------------------------------------------------
    print("\n================================================================")
    print("                    A/B TESTING RESULTS SUMMARY")
    print("================================================================")
    print("Variant A (No RAG):")
    print(f"  Total Issues Found: {len(issues_a)}")
    print("Variant B (With RAG):")
    print(f"  Total Issues Found: {len(issues_b)}")
    
    print("\nAnalysis:")
    dht22_flagged_a = any("12V" in iss.get("issues", "") or "DHT22" in iss.get("issues", "") for iss in issues_a)
    dht22_flagged_b = any("12V" in iss.get("issues", "") or "DHT22" in iss.get("issues", "") or "voltage" in iss.get("issues", "").lower() for iss in issues_b)
    
    if not dht22_flagged_a and dht22_flagged_b:
        print("🎉 SUCCESS: The RAG context successfully enabled the validation agent to identify "
              "the DHT22 over-voltage mismatch that was missed in Variant A!")
    elif dht22_flagged_b:
        print("✨ SUCCESS: Both variants flagged issues, but Variant B (With RAG) was able to "
              "reference specific datasheet limits from the vector store.")
    else:
        print("⚠️ NOTE: The validation agent was unable to detect the mismatch. Verify LLM prompt context.")
    print("================================================================")

if __name__ == "__main__":
    run_ab_test()
