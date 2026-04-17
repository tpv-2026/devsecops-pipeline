from flask import Flask, render_template
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)

JENKINS_USER = "admin"
JENKINS_TOKEN = "11d15cde2442c073cb6ed0cf79a939eab9"

PYTEST_REPORT_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/54/artifact/app/pytest-results.xml"
PYLINT_REPORT_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/54/artifact/app/pylint-report.txt"
TRIVY_REPORT_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/54/artifact/app/trivy-report.txt"
DEPENDENCY_REPORT_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/54/artifact/app/dependency-check-report.xml"


def fetch_from_jenkins(url):
    try:
        response = requests.get(
            url,
            auth=(JENKINS_USER, JENKINS_TOKEN),
            timeout=10
        )
        print(f"Jenkins response status for {url}: {response.status_code}")
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching from Jenkins: {e}")
        return None


def parse_pytest_results():
    xml_data = fetch_from_jenkins(PYTEST_REPORT_URL)

    if not xml_data:
        return None

    try:
        root = ET.fromstring(xml_data)

        testsuite = root.find("testsuite")
        if testsuite is None:
            testsuite = root

        total = int(testsuite.attrib.get("tests", 0))
        failures = int(testsuite.attrib.get("failures", 0))
        errors = int(testsuite.attrib.get("errors", 0))
        skipped = int(testsuite.attrib.get("skipped", 0))
        passed = total - failures - errors - skipped

        pytest_data = {
            "total": total,
            "passed": passed,
            "failures": failures,
            "errors": errors,
            "skipped": skipped
        }

        print("Pytest data:", pytest_data)
        return pytest_data

    except Exception as e:
        print(f"Error parsing pytest XML: {e}")
        return None


def fetch_text_report(url, default_message):
    data = fetch_from_jenkins(url)
    if not data:
        return default_message
    return data


def parse_dependency_check_report():
    xml_data = fetch_from_jenkins(DEPENDENCY_REPORT_URL)

    if not xml_data:
        return "No Dependency Check report found."

    try:
        root = ET.fromstring(xml_data)

        dependencies = root.findall(".//dependency")
        vulnerabilities = root.findall(".//vulnerability")

        return (
            f"Dependencies scanned: {len(dependencies)}\n"
            f"Vulnerabilities found: {len(vulnerabilities)}"
        )

    except Exception as e:
        print(f"Error parsing dependency-check XML: {e}")
        return "Error reading Dependency Check report."


@app.route("/")
def dashboard():
    pytest_data = parse_pytest_results()
    pylint_data = fetch_text_report(PYLINT_REPORT_URL, "No pylint report found.")
    trivy_data = fetch_text_report(TRIVY_REPORT_URL, "No Trivy report found.")
    dependency_data = parse_dependency_check_report()

    return render_template(
        "index.html",
        pytest=pytest_data,
        pylint=pylint_data,
        trivy=trivy_data,
        dependency=dependency_data
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)