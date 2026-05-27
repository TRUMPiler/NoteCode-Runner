FROM python:3.11-slim

# Install only what's needed, nothing extra
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN groupadd -r sandbox && useradd -r -g sandbox -s /bin/false -m sandbox

# Create working directory owned by sandbox user
RUN mkdir -p /sandbox && chown sandbox:sandbox /sandbox

# Copy the runner script
COPY runner.py /runner.py
RUN chmod +x /runner.py

# Switch to unprivileged user
USER sandbox

WORKDIR /sandbox

# Flask for the execution API
RUN pip install --no-cache-dir flask --user

EXPOSE 5000

CMD ["python3", "/runner.py"]
