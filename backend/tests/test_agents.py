import os
import sys
import json
import unittest
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.requirement_agent import run_requirement_agent
from agents.component_agent import run_component_agent
from agents.schematic_agent import run_schematic_agent
from agents.validation_agent import run_validation_agent
from agents.firmware_agent import run_firmware_agent

class TestAgentsNvidia(unittest.TestCase):

    @patch("agents.requirement_agent.call_nvidia_llm")
    def test_requirement_agent_5_times(self, mock_call):
        """Test the Requirement Agent 5 times."""
        print("\n--- Running NVIDIA Requirement Agent Tests (5 iterations) ---")
        
        mock_json = {
            "microcontroller": "ESP32 DevKit V1",
            "sensors": ["DHT22 Temperature & Humidity Sensor"],
            "actuators": ["5V Relay module"],
            "communication": ["WiFi", "I2C"],
            "power": "5V USB / 3.3V Regulator",
            "cloud_services": ["Firebase Realtime Database"],
            "features": ["Temperature-triggered automatic fan cooling"]
        }
        mock_call.return_value = json.dumps(mock_json)
        
        prompt = "Create a cooling system using ESP32, DHT22, and a relay that uploads stats to Firebase."
        for i in range(1, 6):
            res = run_requirement_agent(prompt)
            print(f"Iteration {i}: Microcontroller = {res['microcontroller']}")
            self.assertEqual(res["microcontroller"], "ESP32 DevKit V1")
            self.assertIn("WiFi", res["communication"])
            
        print("NVIDIA Requirement Agent verified 5 times successfully!")

    @patch("agents.component_agent.call_nvidia_llm")
    def test_component_agent_5_times(self, mock_call):
        """Test the Component Agent 5 times."""
        print("\n--- Running NVIDIA Component Agent Tests (5 iterations) ---")
        
        mock_json = {
            "components": [
                {"name": "ESP32-WROOM-32E", "reason": "Integrated WiFi and Bluetooth modules suitable for IoT", "datasheet_keywords": ["ESP32 WROOM datasheet", "pinout"]},
                {"name": "DHT22", "reason": "High accuracy temperature/humidity sensor", "datasheet_keywords": ["DHT22 datasheet", "DHT22 pin out"]}
            ]
        }
        mock_call.return_value = json.dumps(mock_json)
        
        req = {"microcontroller": "ESP32", "sensors": ["DHT22"]}
        for i in range(1, 6):
            res = run_component_agent(req)
            print(f"Iteration {i}: Recommended component {res['components'][0]['name']}")
            self.assertEqual(len(res["components"]), 2)
            self.assertEqual(res["components"][0]["name"], "ESP32-WROOM-32E")
            
        print("NVIDIA Component Agent verified 5 times successfully!")

    @patch("agents.schematic_agent.call_nvidia_llm")
    def test_schematic_agent_5_times(self, mock_call):
        """Test the Schematic Agent 5 times."""
        print("\n--- Running NVIDIA Schematic Agent Tests (5 iterations) ---")
        
        mock_json = {
            "connections": [
                {"from_component": "ESP32", "from_pin": "3V3", "to_component": "DHT22", "to_pin": "VCC", "connection_type": "Power"},
                {"from_component": "ESP32", "from_pin": "GND", "to_component": "DHT22", "to_pin": "GND", "connection_type": "Ground"},
                {"from_component": "ESP32", "from_pin": "GPIO4", "to_component": "DHT22", "to_pin": "DATA", "connection_type": "GPIO"}
            ],
            "explanation": "ESP32 connects DHT22 to GPIO4, utilizing 3.3V power supply."
        }
        mock_call.return_value = json.dumps(mock_json)
        
        req = {"microcontroller": "ESP32"}
        comps = [{"name": "DHT22"}]
        for i in range(1, 6):
            res = run_schematic_agent(req, comps)
            print(f"Iteration {i}: Connections count = {len(res['connections'])}")
            self.assertEqual(len(res["connections"]), 3)
            self.assertEqual(res["connections"][0]["from_pin"], "3V3")
            
        print("NVIDIA Schematic Agent verified 5 times successfully!")

    @patch("agents.validation_agent.call_nvidia_llm")
    def test_validation_agent_5_times(self, mock_call):
        """Test the Validation Agent 5 times."""
        print("\n--- Running NVIDIA Validation Agent Tests (5 iterations) ---")
        
        mock_json = {
            "items": [
                {"issues": "Missing pull-up resistor on DHT22 data line", "severity": "Medium", "fixes": "Add a 4.7k-10k Ohm pull-up resistor between VCC and DATA line."}
            ]
        }
        mock_call.return_value = json.dumps(mock_json)
        
        req = {}
        comps = []
        conns = []
        for i in range(1, 6):
            res = run_validation_agent(req, comps, conns)
            print(f"Iteration {i}: Issue identified = {res['items'][0]['issues']}")
            self.assertEqual(len(res["items"]), 1)
            self.assertEqual(res["items"][0]["severity"], "Medium")
            
        print("NVIDIA Validation Agent verified 5 times successfully!")

    @patch("agents.firmware_agent.call_nvidia_llm")
    def test_firmware_agent_5_times(self, mock_call):
        """Test the Firmware Agent 5 times."""
        print("\n--- Running NVIDIA Firmware Agent Tests (5 iterations) ---")
        
        mock_json = {
            "code": "#include <WiFi.h>\nvoid setup() { Serial.begin(115200); }\nvoid loop() {}"
        }
        mock_call.return_value = json.dumps(mock_json)
        
        req = {}
        comps = []
        conns = []
        for i in range(1, 6):
            code = run_firmware_agent(req, comps, conns)
            print(f"Iteration {i}: Code length = {len(code)}")
            self.assertTrue(code.startswith("#include"))
            
        print("NVIDIA Firmware Agent verified 5 times successfully!")

if __name__ == "__main__":
    unittest.main()
