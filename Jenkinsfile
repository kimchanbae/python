pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE_NAME = 'python-app'
        CONTAINER_NAME = 'python-app'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Test') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE:/app" \
                      -w /app \
                      python:3.14 \
                      sh -c "pip install -q -r requirements.txt && python -m pytest -v"
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t python-app:latest .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker rm -f python-app || true

                    docker run -d \
                      --name python-app \
                      --restart unless-stopped \
                      --memory=512m \
                      -p 8000:8000 \
                      python-app:latest
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                      if docker exec python-app \
                        python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/')"
                      then
                        echo "API HEALTH CHECK SUCCESS"
                        exit 0
                      fi
                      sleep 3
                    done

                    echo "API HEALTH CHECK FAILED"
                    docker logs python-app
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Docker API deployment completed!'
        }

        failure {
            echo 'Pipeline failed. Check stage logs.'
        }
    }
}