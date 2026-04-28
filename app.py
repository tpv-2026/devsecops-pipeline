from flask import Flask, render_template
import xml.etree.ElementTree as ET
import requests
import os
import json

app = Flask(__name__)

JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "")

JENKINS_BASE_URL = os.getenv(
    "JENKINS_BASE_URL",
    "http://localhost:8080/job/devsecops-pipeline-v2.0/lastSuccessfulBuild/artifact/app"
)

REPORTS = {
    "pytest": f"{JENKINS_BASE_URL}/pytest-results.xml",
    "pylint": f"{JENKINS_BASE_URL}/pylint-report.txt",
    "trivy": f"{JENKINS_BASE_URL}/trivy-report.txt",
    "dependency_json": f"{JENKINS_BASE_URL}/dependency-check-report.json",
}


def fetch_from_jenkins(url):
    if not JENKINS_USER or not JENKINS_TOKEN:
        print("Jenkins credentials are missing.")
        return None

    try:
        response = requests.get(
            url,
            auth=(JENKINS_USER, JENKINS_TOKEN),
            timeout=10
        )

        print(f"Fetching: {url}")
        print(f"Status code: {response.status_code}")

        if response.status_code == 404:
            print("Report does not exist yet.")
            return None

        response.raise_for_status()
        return response.text

    except requests.RequestException as error:
        print(f"Error fetching Jenkins artifact: {error}")
        return None


def parse_pytest_results():
    xml_data = fetch_from_jenkins(REPORTS["pytest"])

    default_result = {
        "total": 0,
        "passed": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "status": "No pytest report found."
    }

    if not xml_data:
        return default_result

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

        return {
            "total": total,
            "passed": passed,
            "failures": failures,
            "errors": errors,
            "skipped": skipped,
            "status": "Pytest report loaded successfully."
        }

    except Exception as error:
        print(f"Error parsing pytest XML: {error}")
        default_result["status"] = "Pytest report exists but could not be parsed."
        return default_result


def fetch_text_report(report_name, default_message):
    data = fetch_from_jenkins(REPORTS[report_name])
    return data if data else default_message


def parse_dependency_check_report():
    json_data = fetch_from_jenkins(REPORTS["dependency_json"])

    if not json_data:
        return {
            "summary": "No Dependency Check JSON report found.",
            "dependencies": 0,
            "vulnerabilities": 0
        }

    try:
        report = json.loads(json_data)
        dependencies = report.get("dependencies", [])

        vulnerability_count = 0

        for dependency in dependencies:
            vulnerability_count += len(dependency.get("vulnerabilities", []))

        return {
            "summary": "Dependency Check report loaded successfully.",
            "dependencies": len(dependencies),
            "vulnerabilities": vulnerability_count
        }

    except Exception as error:
        print(f"Error parsing Dependency Check JSON: {error}")

        return {
            "summary": "Dependency Check report exists but could not be parsed.",
            "dependencies": 0,
            "vulnerabilities": 0
        }


@app.route("/")
def dashboard():
    pytest_data = parse_pytest_results()

    pylint_data = fetch_text_report(
        "pylint",
        "No pylint report found."
    )

    trivy_data = fetch_text_report(
        "trivy",
        "No Trivy report found."
    )

    dependency_data = parse_dependency_check_report()

    return render_template(
        "index.html",
        pytest=pytest_data,
        pylint=pylint_data,
        trivy=trivy_data,
        dependency=dependency_data,
        jenkins_base_url=JENKINS_BASE_URL
    )


if __name__ == "__main__":
    print("Starting DevSecOps Dashboard Backend...")
    print(f"Jenkins base URL: {JENKINS_BASE_URL}")
    print(f"Jenkins user configured: {'YES' if JENKINS_USER else 'NO'}")
    print(f"Jenkins token configured: {'YES' if JENKINS_TOKEN else 'NO'}")

    app.run(host="0.0.0.0", port=5000, debug=True)