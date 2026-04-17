from flask import Flask, render_template
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)

PYTEST_REPORT_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/49/artifact/app/dependency-check-report.xml/*view*/"


def fetch_xml_from_jenkins(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching XML from Jenkins: {e}")
        return None


def parse_pytest_results():
    xml_data = fetch_xml_from_jenkins(PYTEST_REPORT_URL)

    if not xml_data:
        return None

    try:
        root = ET.fromstring(xml_data)

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
        print(f"Error parsing pytest XML: {e}")
        return None


@app.route("/")
def dashboard():
    pytest_data = parse_pytest_results()

    return render_template(
        "index.html",
        pytest=pytest_data,
        pylint="Phase 1: not connected yet.",
        trivy="Phase 1: not connected yet.",
        dependency="Phase 1: not connected yet."
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)