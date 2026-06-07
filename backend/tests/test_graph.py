import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy API key
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "mock-key")

from agents.graph import build_workflow

class TestGraphFlow(unittest.TestCase):
    
    @patch("agents.graph.run_requirement_agent")
    @patch("agents.graph.run_component_agent")
    @patch("agents.graph.run_schematic_agent")
    @patch("agents.graph.run_validation_agent")
    @patch("agents.graph.run_firmware_agent")
    def test_workflow_execution_5_times(self, mock_firmware, mock_validation, mock_schematic, mock_components, mock_requirements):
        """Test compiling and executing the LangGraph workflow 5 times with mocked agents."""
        print("\n--- Running LangGraph Workflow Tests (5 iterations) ---")
        
        # Configure mocks
        mock_requirements.return_value = {"microcontroller": "ESP32", "sensors": ["DHT22"]}
        mock_components.return_value = {"components": [
            {"name": "ESP32", "reason": "Microcontroller with WiFi", "datasheet_keywords": ["esp32"]},
            {"name": "DHT22", "reason": "Temperature sensor", "datasheet_keywords": ["dht22"]}
        ]}
        mock_schematic.return_value = {"connections": [{"from_component": "ESP32", "from_pin": "GPIO4", "to_component": "DHT22", "to_pin": "DATA", "connection_type": "GPIO"}]}
        
        # Scenario 1: Validation has no high severity issues
        mock_validation.return_value = {"items": [{"issues": "Add a decoupling capacitor", "severity": "Low", "fixes": "Place 0.1uF cap near VCC"}]}
        mock_firmware.return_value = "void setup() {} void loop() {}"
        
        app = build_workflow()
        
        # Execute 5 times
        for i in range(1, 6):
            inputs = {
                "user_prompt": "Smart plant monitor using ESP32 and DHT22",
                "iteration_count": 0
            }
            config = {"recursion_limit": 50}
            result = app.invoke(inputs, config)
            
            print(f"Iteration {i}: Graph finished. Final Report length = {len(result['final_report'])}")
            
            self.assertIn("ESP32", result["final_report"])
            self.assertIn("DHT22", result["final_report"])
            self.assertIn("Low", result["final_report"])
            
        print("LangGraph Workflow compiled and executed 5 times successfully!")

if __name__ == "__main__":
    unittest.main()
