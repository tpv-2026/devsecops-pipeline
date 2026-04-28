pipeline {
    agent any

    options {
        timestamps()
    }

    tools {
        sonarScanner 'SonarScanner'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Environment') {
            steps {
                sh '''
                    python3 --version
                    pwd
                    ls -la
                    echo "----- APP CONTENT -----"
                    ls -la app
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install -r app/requirements.txt
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                dir('app') {
                    withSonarQubeEnv('SonarQube') {
                        sh '''
                            sonar-scanner \
                            -Dsonar.projectKey=devsecops-pipeline \
                            -Dsonar.projectName=DevSecOps_Pipeline \
                            -Dsonar.sources=. \
                            -Dsonar.python.version=3.13 \
                            -Dsonar.tests=. \
                            -Dsonar.test.inclusions=test_*.py
                        '''
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        stage('Dependency Check') {
            steps {
                dir('app') {
                    catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                        dependencyCheck odcInstallation: 'OWASP-Dependency-Check',
                        additionalArguments: '--noupdate --format XML --out .'
                    }
                    dependencyCheckPublisher pattern: 'dependency-check-report.xml'
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('app') {
                    sh '''
                        . ../venv/bin/activate
                        pytest test_main.py --junitxml=pytest-results.xml
                    '''
                }
            }
        }

        stage('Run Lint') {
            steps {
                dir('app') {
                    sh '''
                        . ../venv/bin/activate
                        pylint main.py > pylint-report.txt || true
                        cat pylint-report.txt
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                dir('app') {
                    sh '''
                        docker build -t devsecops-pipeline-app:latest .
                    '''
                }
            }
        }

        stage('Trivy Scan') {
            steps {
                dir('app') {
                    sh '''
                        trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 0 devsecops-pipeline-app:latest > trivy-report.txt || true
                        cat trivy-report.txt
                    '''
                }
            }
        }

        stage('Copy Reports to Dashboard Folder') {
            steps {
                sh '''
                    echo "Copying reports to dashboard folder..."

                    mkdir -p reports

                    cp app/pytest-results.xml reports/ || true
                    cp app/pylint-report.txt reports/ || true
                    cp app/trivy-report.txt reports/ || true
                    cp app/dependency-check-report.xml reports/ || true

                    echo "Reports folder contents:"
                    ls -la reports
                '''
            }
        }

        stage('Verify Reports Exist') {
            steps {
                sh '''
                    echo "Checking generated report files..."

                    test -f app/pytest-results.xml && echo "OK: pytest-results.xml found" || echo "MISSING: pytest-results.xml"
                    test -f app/pylint-report.txt && echo "OK: pylint-report.txt found" || echo "MISSING: pylint-report.txt"
                    test -f app/trivy-report.txt && echo "OK: trivy-report.txt found" || echo "MISSING: trivy-report.txt"
                    test -f app/dependency-check-report.xml && echo "OK: dependency-check-report.xml found" || echo "MISSING: dependency-check-report.xml"

                    echo "APP FOLDER:"
                    ls -la app

                    echo "REPORTS FOLDER:"
                    ls -la reports || true
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'app/*.xml, app/*.txt, reports/*',
            fingerprint: true,
            allowEmptyArchive: true

            junit testResults: 'app/pytest-results.xml',
            allowEmptyResults: true
        }

        success {
            echo 'Pipeline completed successfully.'
        }

        unstable {
            echo 'Pipeline completed but one or more security/quality checks were unstable.'
        }

        failure {
            echo 'Pipeline failed. Check the failed stage above.'
        }
    }
}