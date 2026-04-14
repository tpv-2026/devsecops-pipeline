pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Python') {
            steps {
                dir('app') {
                    sh '''
                        python3 --version
                        pwd
                        ls -la
                    '''
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        python -m pip install -r requirements.txt
                    '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                dir('app') {
                    script {
                        def scannerHome = tool 'SonarScanner'
                        withSonarQubeEnv('SonarQube') {
                            sh """
                                ${scannerHome}/bin/sonar-scanner \
                                -Dsonar.projectKey=devsecops-pipeline \
                                -Dsonar.projectName=DevSecOps_Pipeline \
                                -Dsonar.sources=. \
                                -Dsonar.python.version=3.13
                            """
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true, webhookSecretId: 'sonar-webhook-secret'
                }
            }
        }

        stage('Dependency Checks') {
            steps {
                dir('app') {
                    dependencyCheck additionalArguments: '--scan . --format XML', odcInstallation: 'DependencyCheck'
                    dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('app') {
                    sh '''
                        . venv/bin/activate
                        pytest test_main.py --junitxml=pytest-results.xml
                    '''
                }
            }
        }

        stage('Run Lint') {
            steps {
                dir('app') {
                    sh '''
                        . venv/bin/activate
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
                sh '''
                    trivy image --format json -o trivy-report.json devsecops-pipeline-app:latest
                    trivy image --severity HIGH,CRITICAL devsecops-pipeline-app:latest > trivy-report.txt || true
                    cat trivy-report.txt
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'app/*.xml, app/*.json, app/*.txt, app/*.html', fingerprint: true, allowEmptyArchive: true
        }
    }
}