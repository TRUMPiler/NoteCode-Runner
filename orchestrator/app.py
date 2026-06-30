from flask import Flask, request, jsonify, make_response
import subprocess
import json
import time
import os

app = Flask(__name__)

# Map logical language names to built images
IMAGES = {
    "python": "sandbox-python",
    "node": "sandbox-node",
    "c": "sandbox-c",
    "java": "sandbox-java",
}

# Aliases and simple canonicalization for incoming `language` values
LANGUAGE_ALIASES = {
    "py": "python",
    "python3": "python",
    "python": "python",
    "js": "node",
    "javascript": "node",
    "node": "node",
    "c": "c",
    "cpp": "c",
    "c++": "c",
    "java": "java",
    "javac": "java",
}

# Exact docker flags required by policy
DOCKER_BASE = [
    "docker",
    "run",
    "--rm",
    "-i",
    "--network",
    "none",
    "--memory",
    "64m",
    "--pids-limit",
    "20",
    "--read-only",
    "--tmpfs",
    "/sandbox:size=20m,uid=999,gid=999,exec",
    "--tmpfs",
    "/tmp:size=10m,exec",
]

# Outer timeout (seconds) - must be > inner runner timeout
OUTER_TIMEOUT = 15


@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


@app.route("/execute", methods=["POST", "OPTIONS"])
def execute():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        resp = make_response(("", 204))
        return resp
    req = request.get_json(silent=True)
    if not req:
        return jsonify({"error": "invalid_json", "message": "expected application/json body"}), 400

    code = req.get("code", "")
    language = req.get("language")
    stdin = req.get("stdin", "")
    code_for_detection = code or ""

    # Normalize language if provided
    if language:
        language = str(language).strip().lower()
        language = LANGUAGE_ALIASES.get(language, language)
    else:
        # If no language provided, try a simple heuristic to detect language from code
        sample = code_for_detection[:4096].lower()
        if "public class" in sample or "system.out" in sample or "import java" in sample:
            language = "java"
        elif "#include" in sample or "int main" in sample:
            language = "c"
        elif "console.log" in sample or sample.strip().startswith("function"):
            language = "node"
        else:
            # default to python
            language = "python"

    image = IMAGES.get(language)
    if not image:
        return jsonify({"error": "unsupported_language", "message": f"language '{language}' is not supported"}), 400

    payload = json.dumps({"code": code, "stdin": stdin})
    cmd = DOCKER_BASE + [image]

    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            input=payload.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=OUTER_TIMEOUT,
        )

        duration = time.time() - start

        raw_out = proc.stdout.decode("utf-8", errors="replace")
        raw_err = proc.stderr.decode("utf-8", errors="replace")

        # Try to parse the sandbox's stdout as JSON. If parsing fails,
        # return a structured error but include the raw outputs.
        try:
            result = json.loads(raw_out)
        except Exception:
            result = {
                "stdout": raw_out[:100 * 1024],
                "stderr": raw_err[:100 * 1024],
                "error": "invalid_sandbox_response",
                "raw_stdout": raw_out[:100 * 1024],
                "raw_stderr": raw_err[:100 * 1024],
            }
            
        # Provide 'output' as an alias for 'stdout' in the API response
        result["output"] = result.get("stdout", "")

        # Attach observability metadata
        result.setdefault("_meta", {})
        result["_meta"].update({"duration_seconds": duration, "docker_exit_code": proc.returncode})

        return jsonify(result)

    except subprocess.TimeoutExpired:
        # The docker run command exceeded the outer timeout.
        return (
            jsonify({"error": "timeout", "message": f"outer timeout of {OUTER_TIMEOUT}s exceeded"}),
            504,
        )
    except Exception as e:
        return jsonify({"error": "internal_error", "message": str(e)}), 500


@app.after_request
def add_cors_headers(response):
    # Allow requests from the frontend during development. Adjust in production.
    response.headers["Access-Control-Allow-Origin"] = os.environ.get("CORS_ORIGIN", "http://localhost:5173")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)