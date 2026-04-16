pipeline {
    agent any

    tools {
        sonarQubeScanner 'SonarQube Scanner installations'
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
                    withSonarQubeEnv('SonarQube') {
                        sh '''
                            /var/jenkins_home/tools/hudson.plugins.sonar.SonarRunnerInstallation/SonarScanner/bin/sonar-scanner \
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

        stage('Dependency Checks') {
            steps {
                dir('app') {
                    catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                        dependencyCheck odcInstallation: 'OWASP-Dependency-Check', additionalArguments: '--noupdate --format XML'
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
                        trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 0 devsecops-pipeline-app:latest > trivy-report.txt
                        cat trivy-report.txt
                    '''
                }
            }
        }

        stage('Verify Reports Exist') {
            steps {
                sh '''
                    echo "Checking generated report files..."
                    test -f app/pytest-results.xml && echo "OK: pytest-results.xml found"
                    test -f app/pylint-report.txt && echo "OK: pylint-report.txt found"
                    test -f app/trivy-report.txt && echo "OK: trivy-report.txt found"
                    test -f app/dependency-check-report.xml && echo "OK: dependency-check-report.xml found"
                    ls -la app
                '''
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