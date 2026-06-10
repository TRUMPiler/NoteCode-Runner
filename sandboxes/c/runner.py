#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import json
import re

MAX_OUTPUT_BYTES = 100 * 1024
COMPILE_TIMEOUT = 10
RUN_TIMEOUT = 10

ansi = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def sanitize(text):
    if text is None:
        return ""
    return ansi.sub('', text).replace('\x00', '')

def main():
    raw = sys.stdin.read()
    data = json.loads(raw)
    code = data.get('code', '')
    stdin = data.get('stdin', '')

    if not code.strip():
        print(json.dumps({"error": "No code provided", "stdout": "", "stderr": "", "exit_code": -1}))
        return

    # Write source to the tmpfs (source can live in /sandbox)
    src_path = '/sandbox/main.c'
    with open(src_path, 'w') as f:
        f.write(code)

    # Compile
    # Compile the binary into the sandbox tmpfs so it can be executed (tmpfs mounted with exec)
    out_bin = '/sandbox/main'
    try:
        compile_proc = subprocess.run(['gcc', src_path, '-o', out_bin], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=COMPILE_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(json.dumps({"stdout": "", "stderr": "", "error": f"Compilation timed out ({COMPILE_TIMEOUT}s)", "exit_code": -1}))
        return

    if compile_proc.returncode != 0:
        print(json.dumps({
            "stdout": "",
            "stderr": sanitize(compile_proc.stderr[:MAX_OUTPUT_BYTES].decode(errors='replace')),
            "error": "Compilation failed",
            "exit_code": compile_proc.returncode
        }))
        return

    # Run
    try:
        proc = subprocess.Popen(['/sandbox/main'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(input=stdin.encode(), timeout=RUN_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            print(json.dumps({"stdout": "", "stderr": "", "error": f"Time limit exceeded ({RUN_TIMEOUT}s)", "exit_code": -1}))
            return
    except Exception as e:
        print(json.dumps({"stdout": "", "stderr": str(e), "error": "runtime_error", "exit_code": -1}))
        return
    finally:
        # Keep compiled binary in /home/sandbox (writable exec area), remove source
        try:
            os.unlink(src_path)
        except:
            pass

    print(json.dumps({
        "stdout": sanitize(stdout[:MAX_OUTPUT_BYTES].decode(errors='replace')),
        "stderr": sanitize(stderr[:MAX_OUTPUT_BYTES].decode(errors='replace')),
        "error": None,
        "exit_code": proc.returncode
    }))

if __name__ == '__main__':
    main()
