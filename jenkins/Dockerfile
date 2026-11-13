FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update && \
    apt-get install -y docker.io git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER root