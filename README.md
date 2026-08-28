# CytoPilot Flow Cytometry Analysis Skill

An MIT-licensed Codex skill for traceable review, replay, adjustment, and validation of conventional flow-cytometry analyses produced by CytoPilot.

This repository contains the complete skill instructions, implementation notes, and a standard-library-only validator for CytoPilot `analysis_report.json` files. It does **not** contain the CytoPilot analysis engine, FlowJo software, real FCS/WSP files, patient/sample data, or proprietary templates.

## Install as a Codex skill

Copy or clone this repository into your Codex skills directory so that `SKILL.md` is at the skill root. The skill can guide a compatible CytoPilot workflow; the bundled validator can also run independently.

## Validate the synthetic example

Python 3.10 or newer is recommended. No third-party Python packages are required.

```bash
python scripts/validate_analysis_report.py examples/analysis_report.synthetic.json --mode exact-wsp --pretty
python -m unittest discover -s tests -v
```

Exit codes are `0` for `VALIDATED`, `1` for `REVIEW_REQUIRED`, and `2` for `REJECTED` or invalid input.

## Scope boundary

The validator checks report structure, arithmetic, hierarchy, mode-specific status, compensation-source labels, and exact-replay cache invariants. It cannot establish biological correctness, sample identity, instrument performance, gate suitability, or the authenticity of input files. A qualified reviewer remains required.

Core analysis commands described in `references/input-output.md` require a compatible CytoPilot installation and are not implemented by this repository.

## Repository layout

- `SKILL.md`: agent workflow and guardrails.
- `agents/openai.yaml`: display metadata.
- `references/`: algorithms, contracts, validation rules, and editor lifecycle.
- `scripts/validate_analysis_report.py`: standalone report validator.
- `examples/`: one synthetic report containing no real measurements.
- `tests/`: standard-library smoke tests.

## Licensing and provenance

Project-authored code and documentation are released under the [MIT License](LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for format/trademark references and the required pre-publication provenance check.

Before publishing under a personal or institutional account, replace “CytoPilot contributors” in `LICENSE` if a different legal copyright holder is required.

## 中文说明

本仓库是可独立安装的 CytoPilot 流式分析 skill，并提供可独立运行的报告验证器。它不包含 CytoPilot 主分析引擎、FlowJo 软件、真实 FCS/WSP、患者信息或实验模板。合成示例仅用于验证文件契约，不能作为生物学或临床依据。
