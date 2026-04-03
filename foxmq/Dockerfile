FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

# Download FoxMQ
ARG FOXMQ_VERSION=0.3.1
ARG TARGETARCH=amd64
RUN curl -LO https://github.com/tashigit/foxmq/releases/download/v${FOXMQ_VERSION}/foxmq_${FOXMQ_VERSION}_linux-${TARGETARCH}.zip \
    && unzip foxmq_${FOXMQ_VERSION}_linux-${TARGETARCH}.zip \
    && chmod +x foxmq \
    && mv foxmq /usr/local/bin/ \
    && rm foxmq_${FOXMQ_VERSION}_linux-${TARGETARCH}.zip

WORKDIR /foxmq

COPY setup.sh /foxmq/setup.sh
RUN chmod +x /foxmq/setup.sh

EXPOSE 1883 19793

ENTRYPOINT ["foxmq"]
