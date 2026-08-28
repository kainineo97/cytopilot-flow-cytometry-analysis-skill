#!/usr/bin/env python3
"""Validate CytoPilot analysis-report invariants and review conditions."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


REPORT_SCHEMA_VERSION = "cytopilot-analysis-report-1.1"
MAX_EVENT_COUNT = 2**63 - 1
MAX_PERCENT_ABS_TOLERANCE = 0.01
DEFAULT_POLICY: dict[str, Any] = {
    "percent_abs_tolerance": 1e-6,
    "minimum_sample_events": 1000,
    "minimum_population_events": 100,
    "review_zero_event_populations": True,
    "review_report_warnings": True,
}

VALID_MODES = {"exact-wsp", "reusable-wsp", "json-template"}
BAD_SAMPLE_STATUSES = {"UNBOUND", "INCOMPATIBLE_PANEL", "ERROR", "FAILED"}
MODE_REPORT_STATUS = {
    "exact-wsp": "REPLAYED",
    "reusable-wsp": "ANALYZED",
    "json-template": "ANALYZED",
}
MODE_SAMPLE_STATUS = {
    "exact-wsp": {"REPLAYED"},
    "reusable-wsp": {"ANALYZED"},
    "json-template": {"ANALYZED"},
}
MODE_COMPENSATION_SOURCES = {
    "exact-wsp": {"none", "fcs", "workspace"},
    "reusable-wsp": {"none", "fcs_embedded", "workspace_fallback"},
    "json-template": {"none", "fcs_embedded"},
}


def finding(severity: str, rule_id: str, scope: str, message: str) -> dict[str, str]:
    return {"severity": severity, "rule_id": rule_id, "scope": scope, "message": message}


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取 JSON {path}: {exc}") from exc


def load_policy(path: Path | None) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if path is None:
        return policy
    candidate = load_json(path)
    if not isinstance(candidate, dict):
        raise ValueError("policy 必须是 JSON object")
    unknown = sorted(set(candidate) - set(DEFAULT_POLICY))
    if unknown:
        raise ValueError(f"policy 包含未知字段：{unknown}")
    policy.update(candidate)

    tolerance = policy["percent_abs_tolerance"]
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise ValueError("percent_abs_tolerance 必须是非负有限数字")
    if not math.isfinite(float(tolerance)) or tolerance < 0:
        raise ValueError("percent_abs_tolerance 必须是非负有限数字")
    if tolerance > MAX_PERCENT_ABS_TOLERANCE:
        raise ValueError(
            f"percent_abs_tolerance 不得超过 {MAX_PERCENT_ABS_TOLERANCE} 个百分点"
        )

    for key in ("minimum_sample_events", "minimum_population_events"):
        value = policy[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value > MAX_EVENT_COUNT
        ):
            raise ValueError(f"{key} 必须是 0 到 {MAX_EVENT_COUNT} 的整数")
    for key in ("review_zero_event_populations", "review_report_warnings"):
        if not isinstance(policy[key], bool):
            raise ValueError(f"{key} 必须是 boolean")
    return policy


def as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if -MAX_EVENT_COUNT <= value <= MAX_EVENT_COUNT else None


def as_nonnegative_int(value: Any) -> int | None:
    number = as_int(value)
    return number if number is not None and number >= 0 else None


def as_finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def expected_percent(numerator: int, denominator: int) -> float:
    return 100.0 * (numerator / denominator) if denominator else 0.0


def validate_messages(
    value: Any,
    field: str,
    scope: str,
    severity: str,
    policy: dict[str, Any],
) -> list[dict[str, str]]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [finding("ERROR", "MESSAGE_LIST", scope, f"{field} 必须是字符串数组")]
    if not value:
        return []
    if severity == "WARNING" and not policy["review_report_warnings"]:
        return []
    return [finding(severity, field.upper(), scope, f"{field} 包含 {len(value)} 条记录")]


def valid_compensation_source(source: str, mode: str) -> bool:
    if source in MODE_COMPENSATION_SOURCES[mode]:
        return True
    prefix = "workspace_verified_against_fcs:"
    return mode == "exact-wsp" and source.startswith(prefix) and len(source) > len(prefix)


def validate_geometry(gate: dict[str, Any], scope: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    gate_type = gate.get("gate_type")
    if gate_type not in {"rectangle", "polygon"}:
        findings.append(finding("ERROR", "GATE_TYPE", scope, "gate_type 必须是 rectangle 或 polygon"))

    dimensions = gate.get("dimensions")
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or not all(isinstance(item, str) and item for item in dimensions)
        or len(set(dimensions)) != len(dimensions)
    ):
        findings.append(finding("ERROR", "DIMENSIONS", scope, "dimensions 必须是非空且不重复的字符串数组"))
        dimensions = []
    elif gate_type == "polygon" and len(dimensions) != 2:
        findings.append(finding("ERROR", "POLYGON_DIMENSIONS", scope, "polygon 必须恰好有两个 dimensions"))

    geometry = gate.get("geometry")
    if not isinstance(geometry, dict):
        findings.append(finding("ERROR", "GEOMETRY_REQUIRED", scope, "gate 缺少 geometry object"))
        return findings
    geometry_dimensions = geometry.get("dimensions")
    if not isinstance(geometry_dimensions, list) or len(geometry_dimensions) != len(dimensions):
        findings.append(finding("ERROR", "GEOMETRY_DIMENSIONS", scope, "geometry dimensions 与 gate dimensions 不一致"))
    else:
        parameters: list[str] = []
        for item in geometry_dimensions:
            if not isinstance(item, dict) or not isinstance(item.get("parameter"), str) or not item["parameter"]:
                findings.append(finding("ERROR", "GEOMETRY_DIMENSION", scope, "geometry dimension 缺少 parameter"))
                continue
            parameters.append(item["parameter"])
            for bound in ("min", "max"):
                if item.get(bound) is not None and as_finite_number(item.get(bound)) is None:
                    findings.append(finding("ERROR", "GEOMETRY_BOUND", scope, f"{bound} 必须是有限数字或 null"))
        if parameters != dimensions:
            findings.append(finding("ERROR", "GEOMETRY_PARAMETER_MATCH", scope, "geometry 参数顺序与 dimensions 不一致"))

    if not isinstance(geometry.get("events_inside"), bool):
        findings.append(finding("ERROR", "EVENTS_INSIDE", scope, "geometry.events_inside 必须是 boolean"))
    vertices = geometry.get("vertices")
    if gate_type == "polygon":
        if (
            not isinstance(vertices, list)
            or len(vertices) < 3
            or not all(
                isinstance(vertex, list)
                and len(vertex) == 2
                and all(as_finite_number(coordinate) is not None for coordinate in vertex)
                for vertex in vertices
            )
        ):
            findings.append(finding("ERROR", "POLYGON_VERTICES", scope, "polygon 必须有至少三个有限二维顶点"))
    elif gate_type == "rectangle" and vertices not in ([], None):
        findings.append(finding("ERROR", "RECTANGLE_VERTICES", scope, "rectangle 不应包含 polygon vertices"))
    return findings


def validate_gate(
    gate: Any,
    sample_scope: str,
    sample_events: int,
    compensation_source: str,
    mode: str,
    policy: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(gate, dict):
        return [finding("ERROR", "GATE_OBJECT", sample_scope, "gate 不是 JSON object")]

    segments = gate.get("path_segments")
    if (
        not isinstance(segments, list)
        or not segments
        or not all(isinstance(item, str) and item for item in segments)
    ):
        path = str(gate.get("path") or "<invalid-gate-path>")
        scope = f"{sample_scope}/gate:{path}"
        findings.append(finding("ERROR", "GATE_PATH_SEGMENTS", scope, "path_segments 必须是非空字符串数组"))
    else:
        path = "/".join(segments)
        scope = f"{sample_scope}/gate:{path}"
        if gate.get("path") != path:
            findings.append(finding("ERROR", "GATE_PATH_MATCH", scope, "path 与 path_segments 不一致"))

    count = as_nonnegative_int(gate.get("count"))
    parent = as_nonnegative_int(gate.get("parent_count"))
    total = as_nonnegative_int(gate.get("total_count"))
    for label, value in (("count", count), ("parent_count", parent), ("total_count", total)):
        if value is None:
            findings.append(finding("ERROR", "COUNT_TYPE", scope, f"{label} 必须是有效范围内的非负整数"))
    if count is None or parent is None or total is None:
        findings.extend(validate_geometry(gate, scope))
        return findings

    if not (count <= parent <= total):
        findings.append(finding("ERROR", "COUNT_ORDER", scope, "必须满足 count <= parent_count <= total_count"))
    if total != sample_events:
        findings.append(finding("ERROR", "TOTAL_MATCH", scope, f"total_count={total} 与样本 event_count={sample_events} 不一致"))

    tolerance = float(policy["percent_abs_tolerance"])
    for key, expected in (
        ("percent_parent", expected_percent(count, parent)),
        ("percent_total", expected_percent(count, total)),
    ):
        actual = as_finite_number(gate.get(key))
        if actual is None:
            findings.append(finding("ERROR", "PERCENT_TYPE", scope, f"{key} 必须是有限数字"))
        elif actual < 0.0 or actual > 100.0:
            findings.append(finding("ERROR", "PERCENT_RANGE", scope, f"{key}={actual} 超出 [0, 100]"))
        elif not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance):
            findings.append(finding("ERROR", "PERCENT_FORMULA", scope, f"{key}={actual}，按 count/denominator 应为 {expected}"))

    findings.extend(validate_geometry(gate, scope))
    dimensions = gate.get("dimensions")
    if isinstance(dimensions, list) and any(
        isinstance(item, str) and item.startswith("Comp-") for item in dimensions
    ) and compensation_source == "none":
        findings.append(finding("ERROR", "COMPENSATION_REQUIRED", scope, "gate 使用 Comp-* feature，但样本没有补偿来源"))

    status = gate.get("status")
    recorded = gate.get("recorded_count")
    difference = gate.get("count_difference")
    if mode == "exact-wsp":
        recorded_count = as_nonnegative_int(recorded)
        count_difference = as_int(difference)
        if recorded_count is None:
            findings.append(finding("ERROR", "CACHE_REFERENCE", scope, "exact WSP replay 的 recorded_count 必须是非负整数"))
        if count_difference is None:
            findings.append(finding("ERROR", "CACHE_DIFFERENCE_TYPE", scope, "count_difference 必须是有效范围内的整数"))
        if recorded_count is not None and count_difference is not None:
            expected_difference = count - recorded_count
            expected_status = "CACHE_MATCH" if expected_difference == 0 else "CACHE_DIFFERENCE"
            if count_difference != expected_difference:
                findings.append(finding("ERROR", "CACHE_DIFFERENCE_FORMULA", scope, "count_difference 不等于 count - recorded_count"))
            if status != expected_status:
                findings.append(finding("ERROR", "CACHE_STATUS_FORMULA", scope, f"status 应为 {expected_status}"))
            if expected_difference != 0:
                findings.append(finding("ERROR", "CACHE_EQUIVALENCE", scope, "重算 gate count 与 FlowJo cached count 不完全一致"))
    elif recorded is not None or difference is not None or status != "NO_CACHE_REFERENCE":
        findings.append(finding("ERROR", "UNEXPECTED_CACHE", scope, "非 exact 模式不得携带或比较 prototype cached count"))

    minimum = int(policy["minimum_population_events"])
    if count == 0 and policy["review_zero_event_populations"]:
        findings.append(finding("WARNING", "ZERO_POPULATION", scope, "population 为 0 events；不得自动解释为生物学缺失"))
    elif 0 < count < minimum:
        findings.append(finding("WARNING", "LOW_POPULATION_EVENTS", scope, f"population 仅 {count} events，低于审查阈值 {minimum}"))
    return findings


def validate_gate_hierarchy(gates: list[Any], sample_scope: str, sample_events: int) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    by_path: dict[tuple[str, ...], dict[str, Any]] = {}
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        segments = gate.get("path_segments")
        if not isinstance(segments, list) or not segments or not all(isinstance(item, str) and item for item in segments):
            continue
        key = tuple(segments)
        if key in by_path:
            findings.append(finding("ERROR", "DUPLICATE_GATE_PATH", sample_scope, f"重复 gate path_segments：{segments}"))
        else:
            by_path[key] = gate
    for key, gate in by_path.items():
        parent_count = as_nonnegative_int(gate.get("parent_count"))
        if parent_count is None:
            continue
        if len(key) == 1:
            if parent_count != sample_events:
                findings.append(finding("ERROR", "ROOT_PARENT_COUNT", sample_scope, f"root gate {list(key)} 的 parent_count 必须等于样本 event_count"))
            continue
        parent_gate = by_path.get(key[:-1])
        if parent_gate is None:
            findings.append(finding("ERROR", "ORPHAN_GATE", sample_scope, f"gate {list(key)} 缺少父 gate {list(key[:-1])}"))
            continue
        expected_parent = as_nonnegative_int(parent_gate.get("count"))
        if expected_parent is not None and parent_count != expected_parent:
            findings.append(finding("ERROR", "HIERARCHY_PARENT_COUNT", sample_scope, f"gate {list(key)} 的 parent_count={parent_count}，父 gate count={expected_parent}"))
    return findings


def validate_report(report: Any, mode: str, policy: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if not isinstance(report, dict):
        return build_result(mode, policy, [finding("ERROR", "REPORT_OBJECT", "report", "analysis report 必须是 JSON object")])

    if report.get("report_schema_version") != REPORT_SCHEMA_VERSION:
        findings.append(finding("ERROR", "REPORT_SCHEMA_VERSION", "report", f"report_schema_version 必须是 {REPORT_SCHEMA_VERSION}"))
    if report.get("analysis_mode") != mode:
        findings.append(finding("ERROR", "ANALYSIS_MODE", "report", f"报告 analysis_mode 必须与 --mode {mode} 一致"))
    if float(policy["percent_abs_tolerance"]) > float(DEFAULT_POLICY["percent_abs_tolerance"]):
        findings.append(finding("WARNING", "WIDENED_PERCENT_TOLERANCE", "policy", "百分比容差高于默认值，必须记录舍入层和批准依据"))

    report_status = report.get("status")
    if report_status != MODE_REPORT_STATUS[mode]:
        findings.append(finding("ERROR", "REPORT_STATUS", "report", f"{mode} 要求报告状态 {MODE_REPORT_STATUS[mode]}，实际为 {report_status!r}"))
    findings.extend(validate_messages(report.get("warnings"), "report_warnings", "report", "WARNING", policy))

    if mode == "json-template":
        template_status = report.get("template_status")
        if template_status == "draft":
            findings.append(finding("WARNING", "DRAFT_TEMPLATE", "report", "draft template 仅可探索使用，需领域审核"))
        elif template_status == "retired":
            findings.append(finding("ERROR", "RETIRED_TEMPLATE", "report", "retired template 不得用于新分析"))
        elif template_status not in {"validated", "locked"}:
            findings.append(finding("ERROR", "TEMPLATE_STATUS", "report", "template_status 必须是 draft、validated、locked 或 retired"))

    samples = report.get("samples")
    if not isinstance(samples, list) or not samples:
        findings.append(finding("ERROR", "SAMPLES_REQUIRED", "report", "samples 必须是非空数组"))
        return build_result(mode, policy, findings)
    sample_count = as_nonnegative_int(report.get("sample_count"))
    if sample_count != len(samples):
        findings.append(finding("ERROR", "SAMPLE_COUNT", "report", f"sample_count 必须等于 samples 长度 {len(samples)}"))

    seen_sample_ids: set[str] = set()
    seen_fcs_paths: set[str] = set()
    total_gates = 0
    analyzed_samples = 0
    incompatible_samples = 0
    for index, sample in enumerate(samples):
        scope = f"sample[{index}]"
        if not isinstance(sample, dict):
            findings.append(finding("ERROR", "SAMPLE_OBJECT", scope, "sample 不是 JSON object"))
            continue
        name = sample.get("sample_name") or sample.get("fcs_path") or sample.get("sample_id") or index
        scope = f"sample:{name}"
        sample_id = sample.get("sample_id")
        fcs_path = sample.get("fcs_path")
        if not isinstance(sample_id, str) or not sample_id:
            findings.append(finding("ERROR", "SAMPLE_ID", scope, "sample_id 必须是非空字符串"))
        elif sample_id in seen_sample_ids:
            findings.append(finding("ERROR", "DUPLICATE_SAMPLE_ID", scope, f"重复 sample_id：{sample_id}"))
        else:
            seen_sample_ids.add(sample_id)
        if not isinstance(fcs_path, str) or not fcs_path:
            findings.append(finding("ERROR", "FCS_PATH", scope, "fcs_path 必须是非空字符串"))
        else:
            normalized_path = fcs_path.casefold()
            if normalized_path in seen_fcs_paths:
                findings.append(finding("ERROR", "DUPLICATE_FCS_PATH", scope, f"重复 fcs_path：{fcs_path}"))
            else:
                seen_fcs_paths.add(normalized_path)

        status = sample.get("status")
        if status in BAD_SAMPLE_STATUSES:
            incompatible_samples += 1
        if status not in MODE_SAMPLE_STATUS[mode]:
            findings.append(finding("ERROR", "SAMPLE_STATUS", scope, f"{mode} 不接受样本状态 {status!r}"))
        else:
            analyzed_samples += 1

        events = as_nonnegative_int(sample.get("event_count"))
        if events is None:
            findings.append(finding("ERROR", "EVENT_COUNT", scope, f"event_count 必须是 0 到 {MAX_EVENT_COUNT} 的整数"))
            continue
        if events < int(policy["minimum_sample_events"]):
            findings.append(finding("WARNING", "LOW_SAMPLE_EVENTS", scope, f"样本仅 {events} events，低于审查阈值 {policy['minimum_sample_events']}"))

        compensation_source = sample.get("compensation_source")
        if not isinstance(compensation_source, str) or not valid_compensation_source(compensation_source, mode):
            findings.append(finding("ERROR", "COMPENSATION_SOURCE", scope, f"{mode} 的 compensation_source 无效：{compensation_source!r}"))
            compensation_source = "none"
        if compensation_source == "workspace_fallback":
            findings.append(finding("WARNING", "WORKSPACE_MATRIX_FALLBACK", scope, "新 FCS 使用 WSP 原型矩阵，需人工复核"))

        findings.extend(validate_messages(sample.get("warnings"), "sample_warnings", scope, "WARNING", policy))
        findings.extend(validate_messages(sample.get("notices"), "sample_notices", scope, "INFO", policy))

        gates = sample.get("gates")
        if not isinstance(gates, list) or not gates:
            findings.append(finding("ERROR", "GATES_REQUIRED", scope, "已分析样本必须包含非空 gates 数组"))
            continue
        total_gates += len(gates)
        for gate in gates:
            findings.extend(validate_gate(gate, scope, events, compensation_source, mode, policy))
        findings.extend(validate_gate_hierarchy(gates, scope, events))

        if mode == "exact-wsp":
            matches = as_nonnegative_int(sample.get("matches"))
            mismatches = as_nonnegative_int(sample.get("mismatches"))
            if matches != len(gates) or mismatches != 0:
                findings.append(finding("ERROR", "SAMPLE_CACHE_AGGREGATE", scope, "matches/mismatches 与 gate cache 结果不一致"))

    if mode == "exact-wsp":
        if as_nonnegative_int(report.get("total_gate_matches")) != total_gates or as_nonnegative_int(report.get("total_gate_mismatches")) != 0:
            findings.append(finding("ERROR", "REPORT_CACHE_AGGREGATE", "report", "报告 cache 汇总与 gate 数组不一致"))
    else:
        if as_nonnegative_int(report.get("analyzed_count")) != analyzed_samples:
            findings.append(finding("ERROR", "ANALYZED_COUNT", "report", "analyzed_count 与样本状态不一致"))
        if as_nonnegative_int(report.get("incompatible_count")) != incompatible_samples:
            findings.append(finding("ERROR", "INCOMPATIBLE_COUNT", "report", "incompatible_count 与样本状态不一致"))

    return build_result(mode, policy, findings)


def build_result(mode: str, policy: dict[str, Any], findings: list[dict[str, str]]) -> dict[str, Any]:
    errors = sum(item["severity"] == "ERROR" for item in findings)
    warnings = sum(item["severity"] == "WARNING" for item in findings)
    infos = sum(item["severity"] == "INFO" for item in findings)
    decision = "REJECTED" if errors else "REVIEW_REQUIRED" if warnings else "VALIDATED"
    return {
        "decision": decision,
        "mode": mode,
        "policy": policy,
        "summary": {"errors": errors, "warnings": warnings, "info": infos},
        "findings": findings,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="CytoPilot analysis_report.json")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    try:
        report = load_json(args.report)
        policy = load_policy(args.policy)
        result = validate_report(report, args.mode, policy)
    except Exception as exc:
        result = {
            "decision": "REJECTED",
            "mode": args.mode,
            "summary": {"errors": 1, "warnings": 0, "info": 0},
            "findings": [finding("ERROR", "INPUT", "validator", f"{type(exc).__name__}: {exc}")],
        }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return {"VALIDATED": 0, "REVIEW_REQUIRED": 1, "REJECTED": 2}[result["decision"]]


if __name__ == "__main__":
    raise SystemExit(main())
