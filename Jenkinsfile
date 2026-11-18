pipeline {
    agent any

    // 10분마다 GHCR 이미지 확인
    triggers {
        cron('H/10 * * * *') 
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        IMAGE_NAME = 'ghcr.io/OWNER/python-api' 
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
                    env.DIGEST_FILE = '/var/jenkins_home/deployed-python-api-digest'
                    
                    env.REMOTE_DIGEST = sh(
                        script: '''
                            set -e
                            docker buildx imagetools inspect \
                              "${IMAGE_NAME}:${IMAGE_TAG}" \
                              --format '{{.Digest}}' \
                              | sha256sum | awk '{print $1}'
                        ''',
                        returnStdout: true
                    ).trim()

                    if (fileExists(env.DIGEST_FILE)) {
                        env.LOCAL_DIGEST = readFile(
                            env.DIGEST_FILE
                        ).trim()
                    } else {
                        env.LOCAL_DIGEST = ''
                    }

                    if (env.REMOTE_DIGEST == env.LOCAL_DIGEST) {
                        env.SHOULD_DEPLOY = 'false'
                        echo 'No new image. Deployment skipped.'
                    } else {
                        env.SHOULD_DEPLOY = 'true'
                        echo 'New image detected!'
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
                    docker pull "${IMAGE_NAME}:${IMAGE_TAG}"
                '''
            }
        }

        // 4. 로컬 이미지 이름 변경
        stage('Tag Local Image') {
            when {
                expression { env.SHOULD_DEPLOY == 'true' }
            }
            steps {
                sh '''
                    docker tag \
                        "${IMAGE_NAME}:${IMAGE_TAG}" \
                        "${LOCAL_IMAGE}:${IMAGE_TAG}"
                    docker images "${LOCAL_IMAGE}"
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
                    docker rm -f "${CONTAINER_NAME}" || true

                    docker run -d \
                      --name "${CONTAINER_NAME}" \
                      --restart unless-stopped \
                      -p 8501:8501 \
                      "${LOCAL_IMAGE}:${IMAGE_TAG}"
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
                    docker ps --filter name="${CONTAINER_NAME}"
                    docker logs --tail 30 "${CONTAINER_NAME}"
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
                        file: env.DIGEST_FILE,
                        text: env.REMOTE_DIGEST
                    )
                }
            }
        }

        // 이전 컨테이너 이미지 버전 정리
        stage('Cleanup Old Images') {
            steps {
                sh '''
                    set -e

                    # 현재 실행 컨테이너의 실제 이미지 ID
                    CURRENT_IMAGE=$(docker inspect \
                    --format='{{.Image}}' "${CONTAINER_NAME}")

                    echo "Current image: $CURRENT_IMAGE"

                    # python-api 이미지 목록 확인
                    docker image ls "${LOCAL_IMAGE}" \
                    --format '{{.Repository}}:{{.Tag}} {{.ID}}' |
                    while read IMAGE_TAG IMAGE_ID; do

                        # 현재 실행 이미지 보호
                        if [ "$IMAGE_ID" = "$CURRENT_IMAGE" ]; then
                            echo "KEEP CURRENT: $IMAGE_TAG"
                            continue
                        fi

                        # 다른 컨테이너가 사용 중인지 확인
                        USED=false

                        for CID in $(docker ps -aq); do
                            USED_IMAGE=$(docker inspect \
                            --format='{{.Image}}' "$CID")

                            if [ "$USED_IMAGE" = "$IMAGE_ID" ]; then
                                USED=true
                                break
                            fi
                        done

                        if [ "$USED" = "true" ]; then
                            echo "KEEP IN USE: $IMAGE_TAG"
                            continue
                        fi

                        echo "DELETE OLD IMAGE: $IMAGE_TAG"

                        docker rmi "$IMAGE_TAG" || true

                    done

                    echo "Old image cleanup completed."
                    docker images "${LOCAL_IMAGE}"
                '''
            }
        }

        stage('Docker Disk Cleanup') {
            steps {
                sh '''
                    echo "Docker disk usage before cleanup"
                    docker system df

                    # 중지된 컨테이너 정리
                    docker container prune -f

                    # 사용하지 않는 빌드 캐시 정리
                    docker builder prune -af

                    echo "Docker disk usage after cleanup"
                    docker system df
                '''
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