pipeline {
    agent any

    environment {
        SONARQUBE_ENV = 'SonarQube'
        SONAR_SCANNER = tool 'SonarScanner'
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Python') {
            steps {
                sh '''
                    python3 --version
                    pwd
                    ls -la
                    echo "----- ROOT CONTENT -----"
                    ls -la .
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
                    withSonarQubeEnv("${SONARQUBE_ENV}") {
                        sh '''
                            ${SONAR_SCANNER}/bin/sonar-scanner \
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
                    waitForQualityGate abortPipeline: true
                }
            }
        }

       stage('Dependency Checks') {
    steps {
        dir('app') {
            catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                dependencyCheck(
                    odcInstallation: 'OWASP-Dependency-Check',
                    additionalArguments: '--scan . --format XML'
                )
                dependencyCheckPublisher pattern: 'dependency-check-report.xml'
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
                        trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 0 devsecops-pipeline-app:latest > trivy-report.txt
                        cat trivy-report.txt
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'app/*.xml, app/*.txt', fingerprint: true
            junit 'app/pytest-results.xml'
        }
    }
}