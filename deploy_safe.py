#!/usr/bin/env python3
"""
deploy_safe.py - SUMBI Analytics bulletproof deployer
USAGE:  python3 /home/ubuntu/sumbi-analytics/deploy_safe.py <candidate.py>

5 GATES. If any gate fails, production stays untouched and only the
candidate is rejected. After deploy, if production health fails, it
automatically rolls back to the previous main.py.

DESIGN (anti-gatekeeper):
- NEVER uses 'pkill -9 -f python' (would kill cron collectors + itself).
- Sandbox is terminated by its own process-group PID only.
- All paths absolute. subprocess instead of os.system.
- Runtime gate uses Streamlit's own AppTest harness (actually runs the
  script, captures exceptions) with a sandbox-port fallback for old
  Streamlit versions.
"""
import sys, os, time, shutil, subprocess, signal, urllib.request

# ===== ENV (this server only) =====
PROJECT       = "/home/ubuntu/sumbi-analytics"
PROD_MAIN     = os.path.join(PROJECT, "main.py")
SERVICE       = "sumbi"
PROD_PORT     = 8501
SANDBOX_PORT  = 8502
SANDBOX_LOG   = "/home/ubuntu/sandbox_deploy.log"
STREAMLIT     = "/home/ubuntu/.local/bin/streamlit"
HTTP_TIMEOUT  = 3
SANDBOX_WAIT  = 12   # seconds to wait for sandbox boot (fallback path)
PROD_WAIT     = 10   # seconds to wait for production health


def log(msg):
    print(f"[deploy] {msg}", flush=True)


def die(msg, code=1):
    log(f"ABORT: {msg}")
    sys.exit(code)


def http_ok(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=HTTP_TIMEOUT) as r:
            return r.status == 200
    except Exception:
        return False


def free_port(port):
    # Kill only whatever holds this exact port (NOT all python).
    subprocess.run(["sudo", "fuser", "-k", f"{port}/tcp"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def runtime_gate_apptest(cand):
    """Best gate: run the script headless via Streamlit AppTest. Returns
    (handled, error_or_None). handled=False means AppTest unavailable."""
    try:
        from streamlit.testing.v1 import AppTest
    except Exception:
        return (False, None)
    prev = os.getcwd()
    os.chdir(PROJECT)  # so relative imports + .streamlit/secrets.toml resolve
    try:
        at = AppTest.from_file(cand, default_timeout=40)
        at.run()
    except Exception as e:
        return (True, f"AppTest crashed: {e}")
    finally:
        os.chdir(prev)
    if at.exception:
        msgs = "; ".join(str(x.value) for x in at.exception)
        return (True, f"runtime exception: {msgs}")
    return (True, None)


def runtime_gate_sandbox(cand):
    """Fallback gate for old Streamlit: boot candidate on 8502, require
    HTTP 200, scan log for tracebacks. Returns error_or_None."""
    free_port(SANDBOX_PORT)
    logf = open(SANDBOX_LOG, "w")
    proc = subprocess.Popen(
        [STREAMLIT, "run", cand,
         "--server.port", str(SANDBOX_PORT),
         "--server.headless", "true",
         "--server.address", "127.0.0.1"],
        stdout=logf, stderr=subprocess.STDOUT,
        cwd=PROJECT, preexec_fn=os.setsid)
    try:
        booted = False
        for _ in range(SANDBOX_WAIT):
            time.sleep(1)
            if http_ok(SANDBOX_PORT):
                booted = True
                break
        logf.flush()
        with open(SANDBOX_LOG, "r", errors="replace") as f:
            sb = f.read()
        crash = any(k in sb for k in (
            "Traceback", "ModuleNotFoundError", "SyntaxError",
            "ImportError", "NameError", "AttributeError"))
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # this group only
        except Exception:
            pass
        free_port(SANDBOX_PORT)
        logf.close()
    if crash:
        return f"traceback in sandbox log: {SANDBOX_LOG}"
    if not booted:
        return f"sandbox HTTP 200 failed after {SANDBOX_WAIT}s: {SANDBOX_LOG}"
    return None


def main():
    if len(sys.argv) != 2:
        die("usage: python3 deploy_safe.py <candidate.py>")
    cand = os.path.abspath(sys.argv[1])
    if not os.path.isfile(cand):
        die(f"candidate not found: {cand}")

    # --- GATE 1: syntax ---
    log("GATE 1: syntax (py_compile)")
    r = subprocess.run([sys.executable, "-m", "py_compile", cand],
                       capture_output=True, text=True)
    if r.returncode != 0:
        die(f"syntax error:\n{r.stderr}")
    log("  syntax OK")

    # --- GATE 2: runtime ---
    log("GATE 2: runtime")
    handled, err = runtime_gate_apptest(cand)
    if handled:
        log("  method: AppTest (script actually executed)")
        if err:
            die(err)
    else:
        log(f"  method: sandbox fallback (port {SANDBOX_PORT})")
        err = runtime_gate_sandbox(cand)
        if err:
            die(err)
    log("  runtime OK (no exceptions)")

    # --- GATE 3: backup ---
    log("GATE 3: backup")
    backup = None
    if os.path.isfile(PROD_MAIN):
        backup = f"{PROD_MAIN}.bak_{int(time.time())}"
        shutil.copy(PROD_MAIN, backup)
        log(f"  backup -> {backup}")
    else:
        log("  no existing main.py (fresh deploy)")

    # --- GATE 4: deploy ---
    log("GATE 4: deploy")
    if cand != PROD_MAIN:
        shutil.copy(cand, PROD_MAIN)
        log("  copied to production")
    else:
        log("  candidate == production (self-check mode, copy skipped)")

    # --- GATE 5: restart + health + auto-rollback ---
    log("GATE 5: systemctl restart + health")
    subprocess.run(["sudo", "systemctl", "restart", SERVICE])
    prod_ok = False
    for _ in range(PROD_WAIT):
        time.sleep(1)
        if http_ok(PROD_PORT):
            prod_ok = True
            break

    if prod_ok:
        log(f"  production OK (HTTP 200, port {PROD_PORT})")
        log("DEPLOY SUCCESS.")
        sys.exit(0)

    log("  production health FAILED -> auto rollback")
    if backup and os.path.isfile(backup):
        shutil.copy(backup, PROD_MAIN)
        subprocess.run(["sudo", "systemctl", "restart", SERVICE])
        time.sleep(PROD_WAIT)
        if http_ok(PROD_PORT):
            die("deploy failed. ROLLBACK OK (previous version restored).", 2)
        die("deploy failed. rollback restart still unhealthy - manual check needed.", 3)
    die("deploy failed. no backup to roll back to - manual check needed.", 4)


if __name__ == "__main__":
    main()
