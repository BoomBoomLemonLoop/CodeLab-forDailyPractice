"""Run local checks and regenerate all evidence, stopping on any command failure."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
out = ROOT / "artifacts"
out.mkdir(exist_ok=True)
commands = [
    (
        "tests.log",
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_geometry.py", "-v"],
    ),
    ("numerical_verification.log", [sys.executable, "verify_numerics.py"]),
    ("generation.log", [sys.executable, "run_g0.py"]),
    ("artifact_verification.log", [sys.executable, "verify_artifacts.py"]),
]
for name, command in commands:
    print("Running:", " ".join(command), flush=True)
    with (out / name).open("w", encoding="utf-8") as stream:
        stream.write("COMMAND: " + " ".join(command) + "\n")
        stream.flush()
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    print(name, "exit code", result.returncode, flush=True)
    if result.returncode:
        print((out / name).read_text(encoding="utf-8"))
        sys.exit(result.returncode)
print("Completed. See README.md and artifacts/; this is not CFD or physical validation.")
