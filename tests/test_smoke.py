from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_analysis_report.py"
EXAMPLE = ROOT / "examples" / "analysis_report.synthetic.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_analysis_report", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidatorSmokeTest(unittest.TestCase):
    def test_synthetic_exact_report_validates(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(EXAMPLE), "--mode", "exact-wsp"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["decision"], "VALIDATED")

    def test_cache_difference_is_rejected(self) -> None:
        validator = load_validator()
        report = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        report["samples"][0]["gates"][0]["recorded_count"] = 999
        result = validator.validate_report(report, "exact-wsp", dict(validator.DEFAULT_POLICY))
        self.assertEqual(result["decision"], "REJECTED")
        rules = {item["rule_id"] for item in result["findings"]}
        self.assertIn("CACHE_EQUIVALENCE", rules)


if __name__ == "__main__":
    unittest.main()
