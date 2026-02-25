from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Reverse mapping for cp1252 special code points (0x80-0x9F range).
REV_CP1252 = {
    0x20AC: 0x80,
    0x201A: 0x82,
    0x0192: 0x83,
    0x201E: 0x84,
    0x2026: 0x85,
    0x2020: 0x86,
    0x2021: 0x87,
    0x02C6: 0x88,
    0x2030: 0x89,
    0x0160: 0x8A,
    0x2039: 0x8B,
    0x0152: 0x8C,
    0x017D: 0x8E,
    0x2018: 0x91,
    0x2019: 0x92,
    0x201C: 0x93,
    0x201D: 0x94,
    0x2022: 0x95,
    0x2013: 0x96,
    0x2014: 0x97,
    0x02DC: 0x98,
    0x2122: 0x99,
    0x0161: 0x9A,
    0x203A: 0x9B,
    0x0153: 0x9C,
    0x017E: 0x9E,
    0x0178: 0x9F,
}

MARKERS = {0x00D8, 0x00D9, 0x00C3, 0x00C2, 0x00E2}


def has_mojibake(text: str) -> bool:
    return any(ord(ch) in MARKERS for ch in text)


def try_recover(text: str) -> str:
    if not has_mojibake(text):
        return text

    raw = bytearray()
    for ch in text:
        o = ord(ch)
        if o <= 0xFF:
            raw.append(o)
            continue
        if o in REV_CP1252:
            raw.append(REV_CP1252[o])
            continue
        return text

    try:
        fixed = raw.decode("utf-8")
    except UnicodeDecodeError:
        return text

    return fixed if fixed != text else text


def build_literal(old: str, new_value: str) -> str:
    m = re.match(r"^([rRuUbBfF]*)(\"\"\"|'''|\"|')", old, re.DOTALL)
    if m:
        prefix, quote = m.group(1), m.group(2)
        prefix = "".join(ch for ch in prefix if ch.lower() in {"r", "u"})
    else:
        prefix = ""
        quote = '"""' if "\n" in new_value else '"'

    if quote in ('"""', "'''"):
        escaped = new_value.replace("\\", "\\\\").replace(quote, "\\" + quote)
        return f"{prefix}{quote}{escaped}{quote}"

    escaped = (
        new_value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace(quote, "\\" + quote)
    )
    return f"{prefix}{quote}{escaped}{quote}"


def process_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    offsets = [0]
    total = 0
    for line in lines:
        total += len(line)
        offsets.append(total)

    def idx(line: int, col: int) -> int:
        return offsets[line - 1] + col

    edits: list[tuple[int, int, str]] = []

    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT and has_mojibake(tok.string):
            body = tok.string[1:]
            fixed = try_recover(body)
            if fixed != body:
                edits.append((idx(tok.start[0], tok.start[1]), idx(tok.end[0], tok.end[1]), "#" + fixed))

    try:
        tree = ast.parse(src.lstrip("\ufeff"))
    except SyntaxError:
        tree = None
    doc_nodes: list[ast.Constant] = []

    def collect_docstring_node(body: list[ast.stmt]) -> None:
        if body and isinstance(body[0], ast.Expr):
            v = body[0].value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                doc_nodes.append(v)

    if tree is not None:
        collect_docstring_node(tree.body)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                collect_docstring_node(node.body)

        for node in doc_nodes:
            if has_mojibake(node.value):
                start = idx(node.lineno, node.col_offset)
                end = idx(node.end_lineno, node.end_col_offset)
                old = src[start:end]
                fixed_value = try_recover(node.value)
                if fixed_value != node.value:
                    edits.append((start, end, build_literal(old, fixed_value)))

    if not edits:
        return False

    out = src
    for start, end, rep in sorted(edits, key=lambda t: t[0], reverse=True):
        out = out[:start] + rep + out[end:]

    if out != src:
        path.write_text(out, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = []
    for py_file in ROOT.rglob("*.py"):
        try:
            if process_file(py_file):
                changed.append(py_file.relative_to(ROOT).as_posix())
        except Exception:
            continue

    print(f"changed {len(changed)} files")
    for item in changed:
        print(item)


if __name__ == "__main__":
    main()
