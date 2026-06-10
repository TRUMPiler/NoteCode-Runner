FROM ubuntu:22.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 999 -r sandbox || true && useradd -u 999 -r -g 999 -s /usr/sbin/nologin -m -r sandbox || true
RUN mkdir -p /sandbox && chown 999:999 /sandbox

COPY runner.py /runner.py
RUN chmod +x /runner.py || true

USER sandbox
WORKDIR /sandbox

CMD ["python3", "/runner.py"]
