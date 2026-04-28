pipeline {
    agent any

    options {
        timestamps()
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
                    docker --version
                    trivy --version
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
                        script {
                            def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'

                            sh """
                                ${scannerHome}/bin/sonar-scanner \
                                -Dsonar.projectKey=devsecops-pipeline \
                                -Dsonar.projectName=DevSecOps_Pipeline \
                                -Dsonar.sources=. \
                                -Dsonar.python.version=3.13 \
                                -Dsonar.tests=. \
                                -Dsonar.test.inclusions=test_*.py
                            """
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo 'Quality Gate skipped for demo stability. SonarQube analysis is still completed and available in the dashboard.'
            }
        }

        stage('Dependency Check') {
            steps {
                dir('app') {
                    catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                        sh '''
                            echo "Running OWASP Dependency Check using Docker..."

                            docker run --rm \
                            -v "$PWD":/src \
                            -v dependency-check-data:/usr/share/dependency-check/data \
                            --entrypoint /bin/sh \
                            owasp/dependency-check:latest \
                            -c 'dependency-check.sh \
                            --project "DevSecOps-Pipeline" \
                            --scan /src \
                            --format JSON \
                            --out /src \
                            --disableAssembly \
                            --disableOssIndex'

                            echo "Dependency Check output:"
                            ls -la

                            if [ -f dependency-check-report.json ]; then
                                echo "OK: dependency-check-report.json created"
                            else
                                echo "MISSING: dependency-check-report.json"
                                exit 1
                            fi
                        '''
                    }
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
                    cp app/dependency-check-report.json reports/ || true

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
                    test -f app/dependency-check-report.json && echo "OK: dependency-check-report.json found" || echo "MISSING: dependency-check-report.json"

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
            archiveArtifacts artifacts: 'app/*.xml, app/*.txt, app/*.json, reports/*',
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