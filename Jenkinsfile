pipeline {
    agent any

    // 1분마다 GHCR 이미지 확인
    triggers {
        cron('H/1 * * * *')
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    parameters {
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'latest',
            description: 'GitHub Actions에서 생성한 Commit SHA'
        )
    }

    environment {
        IMAGE_NAME = 'ghcr.io/kimchanbae/python-api' 
        LOCAL_IMAGE = 'python-api'
        CONTAINER_NAME = 'python-app'
        IMAGE_TAG = 'latest'
    }

    stages {
        // 1. GHCR 로그인
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

        // 2. GHCR 이미지 변경 확인
        stage('Check Image Update') {
            steps {
                script {
                    env.REMOTE_DIGEST = sh(
                        script: '''
                            docker buildx imagetools inspect \
                              ${IMAGE_NAME}:latest \
                              --format '{{json .Manifest}}' | sha256sum | awk '{print $1}'
                        ''',
                        returnStdout: true
                    ).trim()

                    if (fileExists('.deployed-digest')) {
                        env.LOCAL_DIGEST = readFile(
                            '.deployed-digest'
                        ).trim()
                    } else {
                        env.LOCAL_DIGEST = ''
                    }

                    if (env.REMOTE_DIGEST == env.LOCAL_DIGEST) {
                        echo 'No new image. Deployment skipped.'
                        env.SHOULD_DEPLOY = 'false'
                    } else {
                        echo 'New image detected!'
                        echo "Remote Digest: ${env.REMOTE_DIGEST}"
                        env.SHOULD_DEPLOY = 'true'
                    }
                }
            }
        }

        // 3. 새로운 이미지 Pull
        stage('Pull Docker Image') {
            when {
                expression { env.SHOULD_DEPLOY == 'true' }
            }
            steps {
                sh '''
                    docker pull ${IMAGE_NAME}:${IMAGE_TAG}
                    docker tag \
                      ${IMAGE_NAME}:latest \
                      ${LOCAL_IMAGE}:latest
                '''
            }
        }

        stage('Tag Local Image') {
            steps {
                sh '''
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${LOCAL_IMAGE}:${IMAGE_TAG}
                '''
            }
        }

        // 4. 컨테이너 배포
        stage('Deploy Application') {
            when {
                expression { env.SHOULD_DEPLOY == 'true' }
            }
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

        // 5. 배포 확인
        stage('Verify Deployment') {
            when {
                expression { env.SHOULD_DEPLOY == 'true' }
            }
            steps {
                sh '''
                    sleep 5
                    docker inspect \
                      --format='{{.State.Running}}' \
                      ${CONTAINER_NAME} | grep -q true
                    docker ps --filter name=${CONTAINER_NAME}
                    docker logs --tail 30 ${CONTAINER_NAME}
                    docker images ${LOCAL_IMAGE}
                '''
            }
        }

        // 6. 배포 성공 Digest 저장
        stage('Save Deployed Digest') {
            when {
                expression { env.SHOULD_DEPLOY == 'true' }
            }
            steps {
                script {
                    writeFile(
                        file: '.deployed-digest',
                        text: env.REMOTE_DIGEST
                    )
                    echo 'Deployed image digest saved.'
                }
            }
        }
    }

    post {
        success {
            echo 'CI/CD check completed successfully.'
        }

        failure {
            echo 'Deployment failed. Check Jenkins console output.'
        }
    }
}