FROM node:20-alpine

# Create an unprivileged user with uid 999 and gid 999
# This matches the tmpfs mount permissions defined in the orchestrator
RUN addgroup -g 999 sandbox && \
    adduser -u 999 -G sandbox -s /bin/sh -D sandbox

WORKDIR /sandbox

# Copy the Node.js runner script
COPY runner.js /app/runner.js

# Ensure the container runs as the unprivileged user
USER sandbox

CMD ["node", "/app/runner.js"]