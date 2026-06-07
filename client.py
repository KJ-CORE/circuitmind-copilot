import os
import sys
import time
import threading
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: The 'requests' library is required to run this CLI client.")
    print("Please install it by running:")
    print("  pip install requests")
    sys.exit(1)

BACKEND_URL = os.environ.get("CIRCUITMIND_BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api"

def safe_print(*args, **kwargs):
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    flush = kwargs.get('flush', False)
    text = sep.join(str(arg) for arg in args) + end
    try:
        enc = sys.stdout.encoding or 'utf-8'
        sys.stdout.buffer.write(text.encode(enc, errors='replace'))
        if flush:
            sys.stdout.flush()
    except Exception:
        try:
            sys.stdout.write(text)
            if flush:
                sys.stdout.flush()
        except Exception:
            pass

print = safe_print

class Spinner:
    def __init__(self, message="Processing..."):
        self.message = message
        self.spinner_chars = ["|", "/", "-", "\\"]
        self.stop_running = threading.Event()
        self.thread = None

    def _spin(self):
        idx = 0
        while not self.stop_running.is_set():
            sys.stdout.write(f"\r{self.message} {self.spinner_chars[idx]} ")
            sys.stdout.flush()
            idx = (idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def start(self):
        self.stop_running.clear()
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.thread:
            self.stop_running.set()
            self.thread.join()

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title.center(58)}")
    print("=" * 60)

def check_backend_status():
    print(f"Connecting to backend at {BACKEND_URL}...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n[SUCCESS] Backend is Online & Healthy!")
            print(f"  App Name:    {data.get('app', 'CircuitMind API')}")
            print(f"  Environment: {data.get('environment', 'development')}")
            print(f"  Status:      {data.get('status', 'healthy')}")
            return True
        else:
            print(f"\n[ERROR] Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Failed to connect to backend: {e}")
        print("   Make sure the FastAPI backend is running and the port is correct.")
        return False

def generate_design():
    print_header("GENERATE NEW CIRCUIT DESIGN")
    prompt = input("\nEnter your natural language design requirements:\n> ").strip()
    if not prompt:
        print("[WARNING] Prompt cannot be empty.")
        return

    print("\nSending request to CircuitMind LangGraph pipeline...")
    print("This will execute the agentic workflow (Requirements -> Components -> Schematic -> Validation -> Firmware -> Report).")

    spinner = Spinner("Executing Agent Pipeline (this may take up to a minute)...")
    spinner.start()

    try:
        start_time = time.time()
        response = requests.post(f"{API_URL}/projects", json={"user_prompt": prompt}, timeout=180)
        spinner.stop()

        elapsed = time.time() - start_time
        if response.status_code == 201:
            project = response.json()
            print(f"\n[SUCCESS] Circuit Design Generated Successfully in {elapsed:.2f}s!")
            print(f"Project Title: {project.get('title')}")
            print(f"Project ID:    {project.get('id')}")

            view = input("\nWould you like to view the full details of this design now? (y/n): ").strip().lower()
            if view == 'y':
                display_project_details(project)
        else:
            print(f"\n[ERROR] Error generating design (HTTP {response.status_code}):")
            try:
                err_detail = response.json().get("detail", response.text)
                print(f"  Detail: {err_detail}")
            except Exception:
                print(f"  Raw: {response.text}")
    except Exception as e:
        spinner.stop()
        print(f"\n[ERROR] Pipeline request failed: {e}")

def list_projects():
    print_header("LIST ALL SAVED PROJECTS")
    spinner = Spinner("Fetching projects...")
    spinner.start()

    try:
        response = requests.get(f"{API_URL}/projects", timeout=10)
        spinner.stop()

        if response.status_code == 200:
            projects = response.json()
            if not projects:
                print("\nNo saved projects found in the database.")
                return None

            print(f"\nFound {len(projects)} projects:")
            print("-" * 85)
            print(f"{'#':<3} | {'Project ID':<36} | {'Title':<25} | {'Created At':<15}")
            print("-" * 85)
            for idx, p in enumerate(projects, 1):
                created_dt = p.get("created_at", "")
                try:
                    dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00"))
                    created_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    created_str = created_dt[:16]

                print(f"{idx:<3} | {p.get('id'):<36} | {p.get('title')[:25]:<25} | {created_str:<15}")
            print("-" * 85)
            return projects
        else:
            print(f"\n[ERROR] Error fetching projects: HTTP {response.status_code}")
            return None
    except Exception as e:
        spinner.stop()
        print(f"\n[ERROR] Failed to retrieve projects: {e}")
        return None

def view_project_by_menu():
    projects = list_projects()
    if not projects:
        return

    choice = input("\nEnter the '#' number or Project UUID to view details (Press Enter to cancel):\n> ").strip()
    if not choice:
        return

    project = None
    try:
        idx = int(choice)
        if 1 <= idx <= len(projects):
            project = projects[idx - 1]
    except ValueError:
        for p in projects:
            if p.get("id") == choice:
                project = p
                break

    if not project:
        print("[WARNING] Invalid project selection.")
        return

    spinner = Spinner("Fetching project details...")
    spinner.start()
    try:
        response = requests.get(f"{API_URL}/projects/{project['id']}", timeout=10)
        spinner.stop()
        if response.status_code == 200:
            display_project_details(response.json())
        else:
            print(f"[ERROR] Error: {response.status_code} - {response.text}")
    except Exception as e:
        spinner.stop()
        print(f"[ERROR] Failed to fetch project details: {e}")

def clean_for_pdf(text):
    if not text:
        return ""
    replacements = {
        "\u202f": " ",
        "\u2011": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u03a9": "Ohm",
        "\u03bc": "u",
        "\u2026": "...",
        "\u2192": "->",
        "•": "-",
        "\xb0": " degrees ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def export_project_to_pdf(p, filepath):
    from fpdf import FPDF

    class PDFReport(FPDF):
        def header(self):
            self.set_font("helvetica", "B", 14)
            self.set_text_color(40, 50, 120)
            self.cell(0, 10, "CircuitMind Design Co-pilot Report", align="C")
            self.ln(10)
            self.set_draw_color(40, 50, 120)
            self.line(10, 18, 200, 18)
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 10, clean_for_pdf(f"Project: {p.get('title', 'N/A')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, clean_for_pdf(f"Project ID: {p.get('id')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, clean_for_pdf(f"Created At: {p.get('created_at')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(40, 50, 120)
    pdf.multi_cell(0, 7, "User Prompt", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, clean_for_pdf(p.get("user_prompt", "")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(40, 50, 120)
    pdf.multi_cell(0, 7, "System Requirements", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    reqs = p.get("requirements", {})
    if reqs:
        for k, v in reqs.items():
            key_str = k.replace("_", " ").title()
            if isinstance(v, list):
                val_str = ", ".join(v) if v else "None"
            else:
                val_str = str(v)
            pdf.multi_cell(0, 5, clean_for_pdf(f"- {key_str}: {val_str}"), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.multi_cell(0, 5, "No structured requirements parsed.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(40, 50, 120)
    pdf.multi_cell(0, 7, "Recommended Bill of Materials (BOM)", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 95, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    bom = p.get("bom", [])
    if bom:
        for item in bom:
            item_no = item.get("item_no", 1)
            name = item.get("name", "N/A")
            qty = item.get("quantity", 1)
            reason = item.get("reason", "N/A")
            pdf.multi_cell(0, 5, clean_for_pdf(f"{item_no}. {name} (Qty: {qty})\n   Purpose: {reason}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
    else:
        components = p.get("components", [])
        if components:
            for idx, comp in enumerate(components, 1):
                pdf.multi_cell(0, 5, clean_for_pdf(f"{idx}. {comp.get('name', 'N/A')}\n   Purpose: {comp.get('reason', 'N/A')}"), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
        else:
            pdf.multi_cell(0, 5, "No BOM or component data found.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(40, 50, 120)
    pdf.multi_cell(0, 7, "Physical Pin Connections", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 65, pdf.get_y())
    pdf.ln(2)

    final_report = p.get("final_report", "")
    wiring_started = False
    wiring_lines = []
    for line in final_report.splitlines():
        if "## 3. Physical Pin Connections" in line or "Wiring Diagram" in line:
            wiring_started = True
            continue
        if wiring_started:
            if line.startswith("## ") or line.startswith("---") or "## 4." in line:
                break
            if line.strip():
                wiring_lines.append(line.strip())

    pdf.set_font("courier", "", 9)
    pdf.set_text_color(50, 50, 50)
    if wiring_lines:
        for line in wiring_lines:
            pdf.multi_cell(0, 4.5, clean_for_pdf(line), new_x="LMARGIN", new_y="NEXT")
    else:
        wiring_diag = p.get("wiring_diagram", "")
        if wiring_diag:
            pdf.multi_cell(0, 4.5, clean_for_pdf(wiring_diag), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 5, "No connection data available.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(40, 50, 120)
    pdf.multi_cell(0, 7, "Design Report Details", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 55, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, clean_for_pdf(final_report), new_x="LMARGIN", new_y="NEXT")

    pdf.output(filepath)

def display_project_details(p):
    print_header(f"PROJECT: {p.get('title')}")
    print(f"ID:         {p.get('id')}")
    print(f"Created At: {p.get('created_at')}")
    print(f"Prompt:     {p.get('user_prompt')}")

    print("\n--- [System Requirements] ---")
    reqs = p.get("requirements", {})
    if reqs:
        for k, v in reqs.items():
            if isinstance(v, list):
                print(f"  {k.replace('_', ' ').title()}: {', '.join(v) if v else 'None'}")
            else:
                print(f"  {k.replace('_', ' ').title()}: {v}")
    else:
        print("  No structured requirements parsed.")

    print("\n--- [Recommended Bill of Materials (BOM)] ---")
    bom = p.get("bom", [])
    if bom:
        print(f"{'Item':<4} | {'Component Name':<20} | {'Quantity':<8} | {'Reason / Purpose'}")
        print("-" * 80)
        for item in bom:
            print(f"{item.get('item_no', 1):<4} | {item.get('name', 'N/A'):<20} | {item.get('quantity', 1):<8} | {item.get('reason', 'N/A')}")
    else:
        components = p.get("components", [])
        if components:
            print(f"{'Name':<20} | {'Purpose / Reason'}")
            print("-" * 80)
            for comp in components:
                print(f"{comp.get('name', 'N/A'):<20} | {comp.get('reason', 'N/A')}")
        else:
            print("  No component data found.")

    print("\n--- [Physical Pin Connections] ---")
    final_report = p.get("final_report", "")
    wiring_started = False
    wiring_lines = []

    for line in final_report.splitlines():
        if "## 3. Physical Pin Connections" in line or "Wiring Diagram" in line:
            wiring_started = True
            continue
        if wiring_started:
            if line.startswith("## ") or line.startswith("---") or "## 4." in line:
                break
            if line.strip():
                wiring_lines.append(line.strip())

    if wiring_lines:
        for line in wiring_lines:
            print(f"  {line}")
    else:
        wiring_diag = p.get("wiring_diagram", "")
        if wiring_diag:
            print(wiring_diag)
        else:
            print("  No wiring connection info available.")

    print("\n--- [Generated Firmware] ---")
    firmware = p.get("firmware", "").strip()
    if firmware:
        lines = firmware.splitlines()
        preview_limit = 20
        for line in lines[:preview_limit]:
            print(f"  {line}")
        if len(lines) > preview_limit:
            print(f"  ... [Total {len(lines)} lines of code] ...")
    else:
        print("  No firmware code generated.")

    while True:
        print("\nProject Actions:")
        print(" [1] Export Design Package (PDF Report & Firmware Code to UUID folder)")
        print(" [2] Export Full Markdown Report (.md)")
        print(" [3] View Full Firmware Code in Console")
        print(" [4] View Full Markdown Report in Console")
        print(" [5] Return to Main Menu")

        act = input("Select action: ").strip()
        if act == '1':
            project_uuid = p.get('id')
            if not project_uuid:
                print("[WARNING] No project UUID available.")
                continue

            dir_name = os.path.join("project", project_uuid)
            try:
                os.makedirs(dir_name, exist_ok=True)
            except Exception as e:
                print(f"[ERROR] Failed to create directory '{dir_name}': {e}")
                continue

            pdf_filename = os.path.join(dir_name, f"{project_uuid}.pdf")
            ino_filename = os.path.join(dir_name, f"{project_uuid}.ino")

            print("\nGenerating PDF Report...")
            try:
                export_project_to_pdf(p, pdf_filename)
                print(f"[SUCCESS] PDF Report successfully saved to: {os.path.abspath(pdf_filename)}")
            except Exception as e:
                print(f"[ERROR] Failed to export PDF: {e}")

            if firmware:
                print("Saving Firmware Code...")
                try:
                    with open(ino_filename, "w", encoding="utf-8") as f_out:
                        f_out.write(firmware)
                    print(f"[SUCCESS] Firmware code successfully saved to: {os.path.abspath(ino_filename)}")
                except Exception as e:
                    print(f"[ERROR] Failed to export Firmware Code: {e}")
            else:
                print("[WARNING] No firmware code available to save.")
        elif act == '2':
            if not final_report:
                print("[WARNING] No report available to export.")
                continue
            filename = f"report_{p.get('id')[:8]}.md"
            project_dir = "project"
            try:
                os.makedirs(project_dir, exist_ok=True)
                filepath = os.path.join(project_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(final_report)
                print(f"[SUCCESS] Full report successfully saved to {os.path.abspath(filepath)}")
            except Exception as e:
                print(f"[ERROR] Failed to write file: {e}")
        elif act == '3':
            print("\n--- FULL FIRMWARE CODE ---")
            print(firmware)
            print("-" * 50)
        elif act == '4':
            print("\n--- FULL MD REPORT ---")
            print(final_report)
            print("-" * 50)
        elif act == '5' or not act:
            break
        else:
            print("[WARNING] Invalid choice.")

def ingest_datasheet():
    print_header("UPLOAD & INGEST DATASHEET PDF (RAG)")
    file_path = input("\nEnter the absolute or relative path to the datasheet PDF:\n> ").strip()
    if not file_path:
        print("[WARNING] File path cannot be empty.")
        return

    file_path = file_path.strip("\"'")

    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {file_path}")
        return

    if not file_path.lower().endswith(".pdf"):
        print("[WARNING] Only PDF datasheets are supported.")
        return

    print(f"\nUploading and parsing '{os.path.basename(file_path)}'...")
    spinner = Spinner("Ingesting datasheet contents into vector database...")
    spinner.start()

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}
            response = requests.post(f"{API_URL}/rag/ingest", files=files, timeout=60)

        spinner.stop()
        if response.status_code == 200:
            result = response.json()
            print("\n[SUCCESS] Ingestion Successful!")
            print(f"  Filename:        {result.get('filename')}")
            print(f"  Chunks Ingested: {result.get('chunks_ingested')}")
            print(f"  Status:          {result.get('status')}")
        else:
            print(f"\n[ERROR] Ingestion failed (HTTP {response.status_code}):")
            print(f"  Detail: {response.text}")
    except Exception as e:
        spinner.stop()
        print(f"\n[ERROR] Ingestion request failed: {e}")

def main():
    while True:
        print_header("CIRCUITMIND DESIGN CO-PILOT")
        print(" [1] Check Backend Connection Status")
        print(" [2] Generate New Circuit Design")
        print(" [3] List All Saved Designs")
        print(" [4] View Specific Design Details")
        print(" [5] Upload & Ingest Datasheet (PDF RAG)")
        print(" [6] Exit")
        print("=" * 60)

        choice = input("Select an option: ").strip()
        if choice == '1':
            check_backend_status()
        elif choice == '2':
            generate_design()
        elif choice == '3':
            list_projects()
        elif choice == '4':
            view_project_by_menu()
        elif choice == '5':
            ingest_datasheet()
        elif choice == '6':
            print("\nGoodbye!")
            break
        else:
            print("\n[WARNING] Invalid option. Please enter a number between 1 and 6.")

        input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
