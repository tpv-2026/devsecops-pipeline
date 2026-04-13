pipeline {
    agent any

    stages{
        stage('Checkout') {
            steps{
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
                dir('app') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        python -m pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('app') {
                    sh '''
                        . venv/bin/activate
                        pytest test_main.py
                    '''
                }
            }
        }

        stage('Run Lint') {
            steps {
                dir('app') {
                    sh '''
                        . venv/bin/activate
                        pylint main.py || true
                    '''
                }
            }
        }
    }
}