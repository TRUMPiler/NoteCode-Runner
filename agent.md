# NoteCode_Runner — Agent Context

Purpose
- Short notes for an assistant/agent working on this workspace.

Project summary
- A sandboxed code-execution backend for a Notes app. The orchestrator (Flask) accepts HTTP requests, spawns language-specific sandbox containers, pipes JSON into their stdin, and returns JSON from their stdout.

Repository layout (relevant)
- `orchestrator/` — Flask orchestrator and README. Key file: `orchestrator/app.py` (POST `/execute`, GET `/health`).
- `sandboxes/python/` — Python sandbox Dockerfile and `runner.py` (reads JSON from stdin, runs code, returns JSON to stdout).
- `sandboxes/node/` — (pending)
- `sandboxes/c/` — (pending)

Sandbox runner contract
- Input via stdin: JSON object {"code": "...", "stdin": "..."}.
- Runner must write JSON to stdout with at least: `stdout`, `stderr`, `error` (nullable), `exit_code`.
- Runners must enforce an inner timeout (current Python runner: 10s), truncate outputs at 100KB, and sanitize control bytes/ANSI.

Required Docker flags (must always be used)
- `--network none`
- `--memory 64m`
- `--pids-limit 20`
- `--read-only`
- `--tmpfs /sandbox:size=20m,uid=999,gid=999`
- `--tmpfs /tmp:size=10m`
- `--rm -i` (do not persist containers)

Orchestrator behavior (`orchestrator/app.py`)
- Endpoint `POST /execute` accepts {code, language, stdin}.
- Maps `language` to image names: `python` → `sandbox-python`, `node` → `sandbox-node`, `c` → `sandbox-c`.
- Pipes input JSON to `docker run` stdin using the exact flags above.
- Outer timeout is 15s (must be > inner timeout in runners).
- Parses container stdout as JSON; on parse failure, returns structured error including truncated raw stdout/stderr.

Build & run (notes)
- Build python sandbox: `cd sandboxes/python && docker build -t sandbox-python .`
- Quick docker-run test (pipe JSON into container):
  echo '{"code": "print(\"Hello\")", "stdin": ""}' | docker run --rm -i --network none --memory 64m --pids-limit 20 --read-only --tmpfs /sandbox:size=20m,uid=999,gid=999 --tmpfs /tmp:size=10m sandbox-python
- Run orchestrator locally (use venv to avoid system-managed Python):
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r orchestrator/requirements.txt
  python3 orchestrator/app.py

Security & invariants
- Never run sandbox containers as root; images should create an unprivileged `sandbox` user and set `USER sandbox`.
- Always use the exact Docker flags above.
- Outer timeout (orchestrator) must be strictly greater than the inner runner timeout.

Next work items
- Implement `sandboxes/node/` (Node runner + Dockerfile).
- Implement `sandboxes/c/` (compile-then-run runner + Dockerfile).
- (Optional) Implement a container pool in the orchestrator for pre-warmed sandboxes.
- Add integration tests exercising `orchestrator/app.py` with built images.

Where to look first
- `orchestrator/app.py` — orchestrator implementation.
- `sandboxes/python/runner.py` — example runner contract and sanitization.

Contact / notes
- Docker must be available on the host. The orchestrator relies on calling the `docker` CLI.
- Use the exact `docker run` flags to enforce sandboxing guarantees.
