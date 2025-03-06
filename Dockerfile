FROM python:3.11-slim

ARG BUILD_VERSION
ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING=utf-8
ENV DEBIAN_FRONTEND=noninteractive
ENV BUILD_VERSION=$BUILD_VERSION

USER root 

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    iputils-ping \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN groupadd -g 1000 worker_group && \
    useradd -rm -d /home/default-user -s /bin/bash -g worker_group -u 1000 default-user

WORKDIR /worker
COPY --chown=default-user:worker_group ./src /worker/src
COPY --chown=default-user:worker_group ./worker.py /worker
COPY --chown=default-user:worker_group ./requirements.txt /worker

USER default-user

RUN pip3 install --no-cache-dir --user -r requirements.txt

ENV PATH="/home/default-user/.local/bin:${PATH}"

EXPOSE 3080

CMD ["python", "worker.py"]


