from flask import Flask, render_template
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)

JENKINS_USER = "admin"
JENKINS_TOKEN = "11d15cde2442c073cb6ed0cf79a939eab9"

PYTEST_REPORT_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/lastSuccessfulBuild/artifact/app/pytest-results.xml"


def fetch_xml_from_jenkins(url):
    try:
        response = requests.get(
            url,
            auth=(JENKINS_USER, JENKINS_TOKEN),
            timeout=10
        )
        print(f"Jenkins response status: {response.status_code}")
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

        if root.tag == "testsuites":
            testsuite = root.find("testsuite")
        else:
            testsuite = root

        if testsuite is None:
            return None

        total = int(testsuite.attrib.get("tests", 0))
        failures = int(testsuite.attrib.get("failures", 0))
        errors = int(testsuite.attrib.get("errors", 0))
        skipped = int(testsuite.attrib.get("skipped", 0))
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
    print("Pytest data: ", pytest_data)

    return render_template(
        "index.html",
        pytest=pytest_data,
        pylint="Phase 1: not connected yet.",
        trivy="Phase 1: not connected yet.",
        dependency="Phase 1: not connected yet."
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)