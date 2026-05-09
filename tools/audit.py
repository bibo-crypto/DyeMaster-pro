"""
DyeMaster Pro - periodic code audit runner

Runs lightweight static checks and emits a Markdown report.
No external dependencies required.
"""

from __future__ import annotations

import argparse
import compileall
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = ["main.py", "app", "ui"]


@dataclass
class Finding:
    category: str
    severity: str  # info|warn|error
    message: str
    evidence: str | None = None


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
        out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        return proc.returncode, out.strip()
    except FileNotFoundError:
        return 127, ""


def _has_rg() -> bool:
    code, _ = _run(["rg", "--version"], cwd=REPO_ROOT)
    return code == 0


def _rg(pattern: str, paths: list[str], extra: list[str] | None = None) -> list[str]:
    if not _has_rg():
        return []
    cmd = ["rg", "-n", pattern, "-S", "--no-heading"]
    if extra:
        cmd += extra
    cmd += paths
    code, out = _run(cmd, cwd=REPO_ROOT)
    if code not in (0, 1):  # 1 == no matches
        return [f"[rg failed] {' '.join(cmd)}", out]
    return [line for line in out.splitlines() if line.strip()]


def _compile(paths: list[str]) -> bool:
    ok = True
    for p in paths:
        target = REPO_ROOT / p
        if not target.exists():
            continue
        if target.is_dir():
            ok = compileall.compile_dir(str(target), quiet=1) and ok
        else:
            ok = compileall.compile_file(str(target), quiet=1) and ok
    return ok


def _find_orphan_pyc(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for p in paths:
        root = REPO_ROOT / p
        if not root.exists() or not root.is_dir():
            continue
        for pyc in root.rglob("__pycache__/*.pyc"):
            base = pyc.stem  # e.g. foo.cpython-314
            base = re.sub(r"\.cpython-\d+$", "", base)
            expected = pyc.parent.parent / f"{base}.py"
            if not expected.exists():
                findings.append(
                    Finding(
                        category="dead-code",
                        severity="warn",
                        message="Orphan .pyc without matching .py source (stale cache)",
                        evidence=f"{pyc.relative_to(REPO_ROOT)} -> missing {expected.relative_to(REPO_ROOT)}",
                    )
                )
    return findings


def _scan_hardcoded_paths() -> list[Finding]:
    lines = _rg(r"([A-Za-z]:\\\\|/Users/|/home/|\\\\\\\\)", DEFAULT_PATHS)
    out: list[Finding] = []
    for line in lines[:80]:
        out.append(Finding("portability", "warn", "Possible hardcoded filesystem path", evidence=line))
    return out


def _scan_todos() -> list[Finding]:
    lines = _rg(r"\b(TODO|FIXME|HACK)\b", DEFAULT_PATHS)
    return [Finding("maintainability", "info", "TODO/FIXME marker", evidence=l) for l in lines[:120]]


def _scan_bare_excepts() -> list[Finding]:
    lines = _rg(r"except\s+Exception\s*:\s*(pass|return|$)", DEFAULT_PATHS)
    out: list[Finding] = []
    for l in lines[:120]:
        out.append(Finding("reliability", "warn", "Broad except Exception may hide bugs", evidence=l))
    return out


def _scan_duplicate_comment_lines() -> list[Finding]:
    findings: list[Finding] = []
    for rel in ["main.py"] + [str(p) for p in (REPO_ROOT / "app").glob("*.py")] + [str(p) for p in (REPO_ROOT / "ui").glob("*.py")]:
        path = Path(rel)
        if not path.is_absolute():
            path = REPO_ROOT / rel
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        prev = None
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if prev and stripped and stripped == prev and (stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''")):
                findings.append(
                    Finding(
                        "maintainability",
                        "info",
                        "Duplicate consecutive comment/doc line",
                        evidence=f"{path.relative_to(REPO_ROOT)}:{idx} {stripped[:120]}",
                    )
                )
            prev = stripped
    return findings[:80]


def generate_report(findings: list[Finding], compile_ok: bool, output_path: Path) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    errors = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warn")
    infos = sum(1 for f in findings if f.severity == "info")

    lines: list[str] = []
    lines.append(f"# DyeMaster Pro - Audit Report")
    lines.append("")
    lines.append(f"- Generated: `{ts}`")
    lines.append(f"- Repo root: `{REPO_ROOT}`")
    lines.append(f"- Compile: `{'OK' if compile_ok else 'FAIL'}`")
    lines.append(f"- Findings: `{errors} error / {warns} warn / {infos} info`")
    lines.append("")

    by_cat: dict[str, list[Finding]] = {}
    for f in findings:
        by_cat.setdefault(f.category, []).append(f)

    for cat in sorted(by_cat.keys()):
        lines.append(f"## {cat}")
        for f in by_cat[cat]:
            ev = f.evidence.replace("`", "'") if f.evidence else ""
            lines.append(f"- **{f.severity}**: {f.message}" + (f" — `{ev}`" if ev else ""))
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(REPO_ROOT / "audit_report.md"))
    args = parser.parse_args(argv)

    compile_ok = _compile(DEFAULT_PATHS)

    findings: list[Finding] = []
    if not compile_ok:
        findings.append(Finding("build", "error", "Python compileall failed"))

    findings += _find_orphan_pyc(["app", "ui"])
    findings += _scan_todos()
    findings += _scan_bare_excepts()
    findings += _scan_hardcoded_paths()
    findings += _scan_duplicate_comment_lines()

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    generate_report(findings, compile_ok=compile_ok, output_path=out_path)
    print(f"Wrote report: {out_path}")
    return 0 if compile_ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

