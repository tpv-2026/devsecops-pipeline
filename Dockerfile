FROM jenkins/jenkins:lts

USER root

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

#Install Trivy

RUN wget https://github.com/aquasecurity/trivy/releases/latest/download/trivy_0.50.1_Linux-64bit.deb \
    && dpkg -i trivy_0.50.1_Linux-64bit.deb \

USER jenkins