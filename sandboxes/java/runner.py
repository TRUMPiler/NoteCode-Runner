import sys, os, subprocess, json, re

MAX_OUTPUT      = 100 * 1024
COMPILE_TIMEOUT = 15
RUN_TIMEOUT     = 10

ansi = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def sanitize(text):
    return ansi.sub('', text).replace('\x00', '')

def extract_class_name(code):
    # Java filename must match public class name
    # Prefer the class that contains a main method
    m_main = re.search(r'class\s+(\w+)[^{]*\{[\s\S]*?static\s+void\s+main', code)
    if m_main:
        return m_main.group(1)

    # Prefer public class name
    m = re.search(r'public\s+class\s+(\w+)', code)
    if m:
        return m.group(1)

    # Fallback to any top-level class name
    m2 = re.search(r'(?m)^\s*class\s+(\w+)', code)
    if m2:
        return m2.group(1)

    # last resort
    return 'Main'

def main():
    data  = json.loads(sys.stdin.read())
    code  = data.get('code', '')
    stdin = data.get('stdin', '')

    if not code.strip():
        print(json.dumps({"error": "No code provided", "stdout": "", "stderr": "", "exit_code": -1}))
        return

    # Java requires filename to match public class name
    class_name = extract_class_name(code)
    src_path   = f'/sandbox/{class_name}.java'

    with open(src_path, 'w') as f:
        f.write(code)

    # Step 1: Compile
    try:
        compile_result = subprocess.run(
            ["javac", src_path],
            capture_output=True, text=True,
            timeout=COMPILE_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "stdout": "", "stderr": "",
            "error": f"Compilation timed out ({COMPILE_TIMEOUT}s)",
            "exit_code": -1
        }))
        return

    if compile_result.returncode != 0:
        print(json.dumps({
            "stdout"   : "",
            "stderr"   : sanitize(compile_result.stderr[:MAX_OUTPUT]),
            "error"    : "Compilation failed",
            "exit_code": compile_result.returncode
        }))
        return

    # Step 2: Run
    # -cp /sandbox tells java where to find the .class file
    try:
        proc = subprocess.Popen(
            ["java", "-Xmx32m", "-cp", "/sandbox", class_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(
            input=stdin.encode(),
            timeout=RUN_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        print(json.dumps({
            "stdout": "", "stderr": "",
            "error": f"Time limit exceeded ({RUN_TIMEOUT}s)",
            "exit_code": -1
        }))
        return
    finally:
        # Cleanup source file only; keep compiled .class files in /sandbox
        try:
            os.unlink(src_path)
        except:
            pass

    print(json.dumps({
        "stdout"   : sanitize(stdout[:MAX_OUTPUT].decode(errors='replace')),
        "stderr"   : sanitize(stderr[:MAX_OUTPUT].decode(errors='replace')),
        "error"    : None,
        "exit_code": proc.returncode
    }))

if __name__ == '__main__':
    main()
