"""
Automated Test Runner for Editor-AI-App.
Executes each test suite in an isolated process to prevent PyQt/QMediaPlayer thread pollution,
and reports aggregate results across all unit & UI tests.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def run_tests():
    start_time = time.time()
    test_files = sorted(Path("tests").glob("test_*.py"))
    total_tests = 0
    failed_files = []

    print("=" * 65)
    print(f"RUNNING ALL {len(test_files)} TEST SUITES (ISOLATED EXECUTION)")
    print("=" * 65)

    for tf in test_files:
        cmd = [sys.executable, "-m", "unittest", f"tests/{tf.name}"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
            output = proc.stderr + "\n" + proc.stdout
            m = re.search(r"Ran (\d+) tests? in ([\d\.]+)s", output)
            if m:
                ran = int(m.group(1))
                duration = float(m.group(2))
            else:
                ran = 0
                duration = 0.0
            total_tests += ran

            if proc.returncode == 0 and "OK" in output:
                print(f"  [PASS] {tf.name:<38} ({ran:2d} tests in {duration:.2f}s)", flush=True)
            else:
                print(f"  [FAIL] {tf.name:<38}", flush=True)
                print(output, flush=True)
                failed_files.append(tf.name)
        except subprocess.TimeoutExpired:
            print(f"  [FAIL] {tf.name:<38} (TIMEOUT > 45s)", flush=True)
            failed_files.append(tf.name)

    elapsed = time.time() - start_time
    print("=" * 65, flush=True)
    print(f"SUMMARY: {total_tests} tests across {len(test_files)} suites executed in {elapsed:.2f}s.", flush=True)
    if failed_files:
        print(f"FAILED SUITES: {failed_files}", flush=True)
        sys.exit(1)
    else:
        print(">>> ALL TESTS PASSED 100% (0 errors, 0 failures)! <<<", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
