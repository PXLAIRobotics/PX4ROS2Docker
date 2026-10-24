#!/usr/bin/env python3
"""Keep PX4 and its Gazebo children in one owned group and clean it on exit."""
import os
import signal
import subprocess
import sys
import time

child = subprocess.Popen(sys.argv[1:], start_new_session=True)
interrupted = False
interrupted_at = None


def forward(signum, _frame):
    global interrupted, interrupted_at
    interrupted = True
    if interrupted_at is None:
        interrupted_at = time.monotonic()
    try:
        os.killpg(child.pid, signal.SIGTERM if signum == signal.SIGHUP else signum)
    except ProcessLookupError:
        pass


signal.signal(signal.SIGINT, forward)
signal.signal(signal.SIGTERM, forward)
signal.signal(signal.SIGHUP, forward)
try:
    while child.poll() is None:
        if interrupted_at is not None and time.monotonic() - interrupted_at > 8:
            os.killpg(child.pid, signal.SIGKILL)
        time.sleep(0.1)
    result = child.returncode
finally:
    # PX4 may exit before a simulator process it launched; reap the whole group.
    try:
        os.killpg(child.pid, signal.SIGTERM)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.killpg(child.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
sys.exit(0 if interrupted else (result if result >= 0 else 128 - result))
