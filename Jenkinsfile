pipeline {
    agent any

    parameters {
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'latest',
            description: 'GitHub Actions에서 생성한 Commit SHA'
        )
    }

    environment {
        IMAGE_NAME = 'python-api' 
        CONTAINER_NAME = 'python-app'
    }

    stages {

        stage('GHCR Login') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'ghcr-readonly',
                        usernameVariable: 'GHCR_USER',
                        passwordVariable: 'GHCR_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x
                        echo "$GHCR_TOKEN" | docker login ghcr.io \
                          -u "$GHCR_USER" --password-stdin
                    '''
                }
            }
        }

        stage('Pull Docker Image') {
            steps {
                sh '''
                    docker pull ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    docker rm -f ${CONTAINER_NAME} || true

                    docker run -d \
                      --name ${CONTAINER_NAME} \
                      --restart unless-stopped \
                      -p 8501:8501 \
                      ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    docker ps --filter name=${CONTAINER_NAME}
                    docker logs --tail 30 ${CONTAINER_NAME}
                '''
            }
        }
    }
}