from flask import Flask, render_template
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

REPORTS_DIR = "app"


def parse_pytest_results():
    file_path = os.path.join(REPORTS_DIR, "pytest-results.xml")

    if not os.path.exists(file_path):
        return None

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        total = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))
        passed = total - failures - errors - skipped

        return {
            "total": total,
            "passed": passed,
            "failures": failures,
            "errors": errors,
            "skipped": skipped
        }
    except Exception:
        return {
            "total": 0,
            "passed": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0
        }


def read_text_file(file_path, default_message):
    if not os.path.exists(file_path):
        return default_message

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception:
        return default_message


def get_dependency_check_report():
    file_path = os.path.join(REPORTS_DIR, "dependency-check-report.xml")

    if not os.path.exists(file_path):
        return "No Dependency Check report found."

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        vulnerabilities = root.findall(".//vulnerability")

        if not vulnerabilities:
            return "No vulnerabilities found."

        return f"Vulnerabilities found: {len(vulnerabilities)}"

    except Exception:
        return "Error reading Dependency Check report."


@app.route("/")
def dashboard():
    pytest_data = parse_pytest_results()
    pylint_data = read_text_file(
        os.path.join(REPORTS_DIR, "pylint-report.txt"),
        "No pylint report found."
    )
    trivy_data = read_text_file(
        os.path.join(REPORTS_DIR, "trivy-report.txt"),
        "No Trivy report found."
    )
    dependency_data = get_dependency_check_report()

    return render_template(
        "index.html",
        pytest=pytest_data,
        pylint=pylint_data,
        trivy=trivy_data,
        dependency=dependency_data
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)