"""Check output validation without requiring all nine language runtimes."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_examples


class CheckExamplesTests(unittest.TestCase):
    def run_checker(self, language="python", *, error_stderr=None,
                    error_stdout="", error_code=1, failure_case=None,
                    success_stdout=check_examples.SUCCESS, success_stderr="",
                    success_code=0):
        if error_stderr is None:
            error_stderr = check_examples.ERROR + "\n"

        def run(command, **kwargs):
            env = kwargs.get("env")
            if env is None:  # Build commands do not exercise output validation.
                return subprocess.CompletedProcess(command, 0)
            value = env.get("DEMO_SECRET")
            if value:
                return subprocess.CompletedProcess(
                    command, success_code, success_stdout, success_stderr)
            if failure_case is not None and value != failure_case:
                return subprocess.CompletedProcess(
                    command, 1, "", check_examples.ERROR + "\n")
            return subprocess.CompletedProcess(
                command, error_code, error_stdout, error_stderr)

        output = io.StringIO()
        errors = io.StringIO()
        with patch.object(sys, "argv", ["check_examples.py", language]), \
                patch.object(check_examples.subprocess, "run", side_effect=run), \
                redirect_stdout(output), redirect_stderr(errors):
            check_examples.main()
        return output.getvalue(), errors.getvalue()

    def test_exact_output_passes_all_cases(self):
        for language in check_examples.COMMANDS:
            with self.subTest(language=language):
                output, errors = self.run_checker(language)
                self.assertEqual(output, "".join(
                    f"PASS {language}: {case}\n"
                    for case in ("missing", "empty", "zero", "present")))
                self.assertEqual(errors, "")

    def test_extra_error_prefix_or_suffix_fails(self):
        for language in check_examples.COMMANDS:
            for stderr in ("unexpected\n" + check_examples.ERROR + "\n",
                           check_examples.ERROR + "\nunexpected\n"):
                for case in (None, ""):
                    with self.subTest(language=language, stderr=stderr, case=case):
                        with self.assertRaisesRegex(SystemExit, "output withheld"):
                            self.run_checker(language, error_stderr=stderr,
                                             failure_case=case)

    def test_missing_error_newline_fails(self):
        with self.assertRaises(SystemExit):
            self.run_checker(error_stderr=check_examples.ERROR)

    def test_wrong_error_status_fails(self):
        for code in (0, 2, -1):
            with self.subTest(code=code), self.assertRaises(SystemExit):
                self.run_checker(error_code=code)

    def test_unexpected_error_stdout_fails_without_disclosure(self):
        with self.assertRaises(SystemExit) as raised:
            self.run_checker(error_stdout="synthetic-private-output")
        self.assertNotIn("synthetic-private-output", str(raised.exception))
        self.assertIn("output withheld", str(raised.exception))

    def test_go_launcher_trailer_passes(self):
        output, _ = self.run_checker(
            "go", error_stderr=check_examples.ERROR + "\nexit status 1\n")
        self.assertIn("PASS go: empty", output)

    def test_go_trailer_is_not_allowed_for_other_languages(self):
        for language in check_examples.COMMANDS:
            if language == "go":
                continue
            with self.subTest(language=language), self.assertRaises(SystemExit):
                self.run_checker(
                    language, error_stderr=check_examples.ERROR + "\nexit status 1\n")

    def test_go_rejects_modified_or_repeated_trailer(self):
        for trailer in ("exit status 2\n", "exit status 1\nextra\n",
                        "exit status 1\nexit status 1\n", "exit status 1"):
            with self.subTest(trailer=trailer), self.assertRaises(SystemExit):
                self.run_checker("go", error_stderr=check_examples.ERROR + "\n" + trailer)

    def test_error_diagnostics_withhold_stderr(self):
        with self.assertRaises(SystemExit) as raised:
            self.run_checker(error_stderr="synthetic-private-error")
        self.assertNotIn("synthetic-private-error", str(raised.exception))
        self.assertIn("output withheld", str(raised.exception))

    def test_invalid_success_result_fails(self):
        for changes in ({"success_code": 1}, {"success_stdout": "wrong\n"},
                        {"success_stderr": "unexpected\n"}):
            with self.subTest(changes=changes), self.assertRaises(SystemExit):
                self.run_checker(**changes)


if __name__ == "__main__":
    unittest.main()
