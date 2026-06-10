FROM node:18-slim
FROM node:20-alpine

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Create an unprivileged user with uid 999 and gid 999
# This matches the tmpfs mount permissions defined in the orchestrator
RUN addgroup -g 999 sandbox && \
    adduser -u 999 -G sandbox -s /bin/sh -D sandbox

RUN groupadd -g 999 -r sandbox || true && useradd -u 999 -r -g 999 -s /usr/sbin/nologin -m -r sandbox || true
RUN mkdir -p /sandbox && chown 999:999 /sandbox
WORKDIR /sandbox

COPY runner.py /runner.py
RUN chmod +x /runner.py || true
# Copy the Node.js runner script
COPY runner.js /app/runner.js

# Ensure the container runs as the unprivileged user
USER sandbox
WORKDIR /sandbox

CMD ["python3", "/runner.py"]
CMD ["node", "/app/runner.js"]
