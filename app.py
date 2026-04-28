from flask import Flask, render_template
import xml.etree.ElementTree as ET
import requests
import os

app = Flask(__name__)

JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

JENKINS_BASE_URL = "http://localhost:8080/job/devsecops-pipeline-v2.0/lastSuccessfulBuild/artifact/app"

PYTEST_REPORT_URL = f"{JENKINS_BASE_URL}/pytest-results.xml"
PYLINT_REPORT_URL = f"{JENKINS_BASE_URL}/pylint-report.txt"
TRIVY_REPORT_URL = f"{JENKINS_BASE_URL}/trivy-report.txt"
DEPENDENCY_REPORT_URL = f"{JENKINS_BASE_URL}/dependency-check-report.xml"


def fetch_from_jenkins(url):
    try:
        if not JENKINS_USER or not JENKINS_TOKEN:
            return None

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
        return {
            "total": 0,
            "passed": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0
        }

    try:
        root = ET.fromstring(xml_data)
        testsuite = root.find("testsuite") or root

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
        return {
            "total": 0,
            "passed": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0
        }


def fetch_text_report(url, default_message):
    data = fetch_from_jenkins(url)
    return data if data else default_message


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
        return "Dependency Check report exists, but could not be parsed."


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