import sys
import os
import subprocess
import tempfile
import json
import re

MAX_OUTPUT_BYTES = 100 * 1024
TIMEOUT_SECONDS  = 10

def sanitize(text):
    ansi = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi.sub('', text).replace('\x00', '')

def main():
    raw  = sys.stdin.read()
    data = json.loads(raw)
    code  = data.get('code', '')
    stdin = data.get('stdin', '')

    if not code.strip():
        print(json.dumps({"error": "No code provided", "stdout": "", "stderr": "", "exit_code": -1}))
        return

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/sandbox', delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        proc = subprocess.Popen(
            ["python3", tmp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = proc.communicate(input=stdin.encode(), timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            print(json.dumps({"stdout": "", "stderr": "", "error": f"Time limit exceeded ({TIMEOUT_SECONDS}s)", "exit_code": -1}))
            return

        print(json.dumps({
            "stdout"   : sanitize(stdout[:MAX_OUTPUT_BYTES].decode(errors='replace')),
            "stderr"   : sanitize(stderr[:MAX_OUTPUT_BYTES].decode(errors='replace')),
            "error"    : None,
            "exit_code": proc.returncode
        }))
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

if __name__ == '__main__':
    main()
