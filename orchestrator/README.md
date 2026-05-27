# Orchestrator

Simple Flask orchestrator that accepts POST /execute and runs a sandbox container.

Quick start:

```bash
python3 -m pip install -r orchestrator/requirements.txt
python3 orchestrator/app.py
```

Example request:

```bash
curl -sS -X POST "http://localhost:5000/execute" -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello from sandbox\")", "language": "python", "stdin": ""}' | jq
```
