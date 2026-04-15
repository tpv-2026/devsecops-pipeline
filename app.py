from flask import Flask, render_template
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "app")


def read_pytest_report():
    pytest_file = os.path.join(REPORTS_DIR, "pytest-results.xml")

    if not os.path.exists(pytest_file):
        return None

    try:
        tree = ET.parse(pytest_file)
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
    except Exception as e:
        return {
            "total": 0,
            "passed": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "message": f"Error reading pytest report: {e}"
        }


def read_text_report(filename, default_message="No report found."):
    file_path = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(file_path):
        return default_message

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()
    except Exception as e:
        return f"Error reading {filename}: {e}"


@app.route("/")
def dashboard():
    pytest_data = read_pytest_report()
    pylint_data = read_text_report("pylint-report.txt")
    trivy_data = read_text_report("trivy-report.txt")

    return render_template(
        "index.html",
        pytest=pytest_data,
        pylint=pylint_data,
        trivy=trivy_data
    )


if __name__ == "__main__":
    app.run(debug=True)