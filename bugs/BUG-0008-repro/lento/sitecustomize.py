# Only the job runner (python -m sima.jobs run ...) starts slowly, as under load.
import time
try:
    if b"sima.jobs" in open("/proc/self/cmdline", "rb").read():
        time.sleep(1.0)
except OSError:
    pass
