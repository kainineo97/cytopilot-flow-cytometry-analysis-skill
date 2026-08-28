# Contributing

By submitting a contribution, you agree that it may be distributed under this repository's MIT License and that you have the right to contribute it.

Use synthetic fixtures. Never commit real patient/sample data, FCS/WSP files, absolute laboratory paths, credentials, proprietary templates, or copied prompts/manuals without documented redistribution rights.

Before opening a pull request:

```bash
python -m unittest discover -s tests -v
python scripts/validate_analysis_report.py examples/analysis_report.synthetic.json --mode exact-wsp --pretty
```

Changes to validation thresholds, accepted status values, compensation sources, or exact-replay rules must include a rationale and tests. Computational validation must not be presented as biological or clinical validation.
