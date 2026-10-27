"""Check the public behavior of each demo using synthetic environment values."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUCCESS = "Sotto demo: secret loaded successfully.\n"
ERROR = "DEMO_SECRET is missing or empty. Set it with `sotto set DEMO_SECRET`, then run this demo with `sotto run -- <command>`."
COMMANDS = {
    "python": [sys.executable, "python/main.py"],
    "javascript": ["node", "javascript/main.js"],
    "typescript": ["node", "typescript/main.ts"],
    "java": ["java", "java/Main.java"],
    "csharp": ["dotnet", "run", "--no-build", "--no-restore", "--project", "csharp/Demo.csproj"],
    "php": ["php", "php/main.php"],
    "go": ["go", "run", "go/main.go"],
    "rust": [str(ROOT / "rust/target/debug" / ("demo.exe" if os.name == "nt" else "demo"))],
    "cpp": [str(ROOT / "cpp/build" / ("demo.exe" if os.name == "nt" else "demo"))],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("languages", nargs="*", help="Default: all nine languages")
    args = parser.parse_args()
    languages = args.languages or list(COMMANDS)
    for language in languages:
        if language not in COMMANDS:
            parser.error(f"Unknown language: {language}")

    if "csharp" in languages:
        subprocess.run(["dotnet", "build", "csharp/Demo.csproj", "--nologo"], cwd=ROOT, check=True)
    if "rust" in languages:
        subprocess.run(["cargo", "build", "--quiet", "--manifest-path", "rust/Cargo.toml"], cwd=ROOT, check=True)
    if "cpp" in languages:
        subprocess.run(["cmake", "-S", "cpp", "-B", "cpp/build"], cwd=ROOT, check=True)
        subprocess.run(["cmake", "--build", "cpp/build", "--config", "Release"], cwd=ROOT, check=True)

    for language in languages:
        for label, value in [("missing", None), ("empty", ""), ("zero", "0"), ("present", "synthetic-secret-do-not-print-42")]:
            env = os.environ.copy()
            env.pop("DEMO_SECRET", None)
            if value is not None:
                env["DEMO_SECRET"] = value
            result = subprocess.run(COMMANDS[language], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
            if value:
                passed = result.returncode == 0 and result.stdout == SUCCESS and result.stderr == ""
            else:
                expected_errors = [ERROR + "\n"]
                if language == "go":
                    # `go run` can append its own diagnostic after the demo exits.
                    expected_errors.append(ERROR + "\nexit status 1\n")
                passed = result.returncode == 1 and result.stdout == "" and result.stderr in expected_errors
            if not passed:
                raise SystemExit(f"FAIL {language}: {label}; unexpected exit code or output (output withheld)")
            print(f"PASS {language}: {label}")


if __name__ == "__main__":
    main()
