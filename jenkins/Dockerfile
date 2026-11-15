FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update && \
    apt-get install -y docker.io git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Docker 소켓 그룹 생성 (GID 1001)
RUN groupadd -g 1001 docker || true

# Jenkins 사용자에게 Docker 그룹 권한 부여
RUN usermod -aG docker jenkins

USER jenkins