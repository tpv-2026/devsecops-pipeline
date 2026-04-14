from flask import Flask, render_template
import os
import json
import xml.etree.ElementTree as ET

app = Flask(__name__)

REPORTS_DIR = "reports"


def file_exists(filename: str) -> bool:
    return os.path.exists(os.path.join(REPORTS_DIR, filename))


def load_pytest_results():
    filepath = os.path.join(REPORTS_DIR, "pytest-results.xml")
    if not os.path.exists(filepath):
        return {"status": "Not found", "tests": 0, "failures": 0, "errors": 0}

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        return {
            "status": "Loaded",
            "tests": int(root.attrib.get("tests", 0)),
            "failures": int(root.attrib.get("failures", 0)),
            "errors": int(root.attrib.get("errors", 0)),
        }
    except Exception as e:
        return {"status": f"Error: {e}", "tests": 0, "failures": 0, "errors": 0}


def load_pylint_results():
    filepath = os.path.join(REPORTS_DIR, "pylint-report.txt")
    if not os.path.exists(filepath):
        return {"status": "Not found", "score": "N/A", "issues": []}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        score = "N/A"
        for line in content.splitlines():
            if "Your code has been rated at" in line:
                score = line.strip()
                break

        issues = [
            line.strip()
            for line in content.splitlines()
            if ":" in line and ("C0" in line or "W0" in line or "E0" in line or "R0" in line)
        ]

        return {"status": "Loaded", "score": score, "issues": issues[:10]}
    except Exception as e:
        return {"status": f"Error: {e}", "score": "N/A", "issues": []}


def load_trivy_results():
    filepath = os.path.join(REPORTS_DIR, "trivy-report.json")
    if not os.path.exists(filepath):
        return {"status": "Not found", "total": 0, "high": 0, "critical": 0}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        high = 0
        critical = 0
        total = 0

        for result in data.get("Results", []):
            vulnerabilities = result.get("Vulnerabilities", [])
            total += len(vulnerabilities)
            for vuln in vulnerabilities:
                severity = vuln.get("Severity", "").upper()
                if severity == "HIGH":
                    high += 1
                elif severity == "CRITICAL":
                    critical += 1

        return {
            "status": "Loaded",
            "total": total,
            "high": high,
            "critical": critical,
        }
    except Exception as e:
        return {"status": f"Error: {e}", "total": 0, "high": 0, "critical": 0}


def load_dependency_check_results():
    filepath = os.path.join(REPORTS_DIR, "dependency-check-report.xml")
    if not os.path.exists(filepath):
        return {"status": "Not found", "dependencies": 0, "vulnerable_dependencies": 0}

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        dependencies = root.findall(".//dependency")
        vulnerable_dependencies = 0

        for dep in dependencies:
            vulnerabilities = dep.findall(".//vulnerability")
            if vulnerabilities:
                vulnerable_dependencies += 1

        return {
            "status": "Loaded",
            "dependencies": len(dependencies),
            "vulnerable_dependencies": vulnerable_dependencies,
        }
    except Exception as e:
        return {"status": f"Error: {e}", "dependencies": 0, "vulnerable_dependencies": 0}


@app.route("/")
def dashboard():
    pytest_results = load_pytest_results()
    pylint_results = load_pylint_results()
    trivy_results = load_trivy_results()
    dependency_results = load_dependency_check_results()

    return render_template(
        "index.html",
        pytest_results=pytest_results,
        pylint_results=pylint_results,
        trivy_results=trivy_results,
        dependency_results=dependency_results,
    )


if __name__ == "__main__":
    app.run(debug=True)