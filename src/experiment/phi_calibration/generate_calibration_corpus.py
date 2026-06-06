# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Dedicated φ-calibration corpus generator (DT-021).

The scenario corpus (S1–S5) was built to *exercise* the experiment: each
scenario probes a single target dimension, so it declares ground truth only for
that dimension and mixes non-Python artifacts (YAML/CI-CD) where radon/bandit do
not apply. That makes it unfit as a *calibration* corpus, where every artifact
needs comparable ground truth across all four statically-validated dimensions
(v4 security, v6 testability, v7 maintainability, v8 technical_debt) with
controlled spread over [0,1].

This module generates such a corpus: ~24 Python artifacts in four families, each
family sweeping ONE axis from clean → degraded so that the calibration dimension
varies while the others stay comparatively stable. Because φ-LLM is validated
*against* static analysis, the ground truth is the static-analysis value actually
measured on each artifact (radon/bandit) — the corpus only needs to guarantee
the range is covered. The Spearman ρ then measures whether the LLM's semantic
judgement tracks the static signal across that range.

Families:
  SEC_*   — identical structure, increasing security risk (drives v4 down)
  CPX_*   — increasing cyclomatic complexity (drives v6 testability down)
  DBT_*   — increasing size/branching/volume (drives v8 debt up)
  MNT_*   — decreasing maintainability: naming, nesting, dead code (drives v7 down)

Usage:
    python -m src.experiment.phi_calibration.generate_calibration_corpus \
        --output src/experiment/phi_calibration/corpus/calibration_corpus.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


# ─── SEC family: security risk sweep (v4) ──────────────────────────────────────
# Same CRUD shape; progressively more insecure patterns (bandit-detectable).

_SEC = {
    "sec_00_clean": '''\
import hashlib
import hmac
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_user(db, username: str):
    """Parameterized query, no secrets, safe comparison."""
    logger.info("Lookup user %s", username)
    row = db.execute(
        text("SELECT id, pw_hash FROM users WHERE username = :u"),
        {"u": username},
    ).fetchone()
    return dict(row) if row else None


def verify(stored_hash: str, candidate: str) -> bool:
    digest = hashlib.sha256(candidate.encode()).hexdigest()
    return hmac.compare_digest(stored_hash, digest)
''',
    "sec_01_low": '''\
import subprocess
import logging

logger = logging.getLogger(__name__)


def list_dir(path: str):
    """Uses subprocess with a fixed arg list — low risk but flagged."""
    logger.info("Listing %s", path)
    result = subprocess.run(["ls", "-la", path], capture_output=True, text=True)
    return result.stdout
''',
    "sec_02_medium": '''\
import logging

logger = logging.getLogger(__name__)


def make_token(seed: str):
    """Weak randomness for a token — medium severity."""
    import random
    logger.info("Generating token")
    return "".join(random.choice("0123456789abcdef") for _ in range(16))


def load_config(path: str):
    with open(path) as f:
        return eval(f.read())  # noqa — insecure eval, medium/high
''',
    "sec_03_high": '''\
import os


def authenticate(db, username: str, password: str):
    query = "SELECT * FROM users WHERE name = '" + username + \\
            "' AND pw = '" + password + "'"
    return db.execute(query).fetchone()


def run_cmd(user_input: str):
    os.system("process_file " + user_input)
''',
    "sec_04_critical": '''\
import os
import pickle


def login(db, u, p):
    q = "SELECT * FROM users WHERE name='" + u + "' AND pw='" + p + "'"
    return db.execute(q).fetchall()


def deserialize(blob):
    return pickle.loads(blob)


def shell(cmd):
    os.system(cmd)


PASSWORD = "admin123"
SECRET_KEY = "hardcoded-secret-do-not-do-this"
''',
    # Extra artifacts to bring SEC family to n=8, filling intermediate severity points
    "sec_05_low_b": '''\
import subprocess
import logging

logger = logging.getLogger(__name__)


def run_report(report_name: str):
    """Fixed args list — low risk; subprocess without shell=True."""
    result = subprocess.run(
        ["generate_report", "--name", report_name],
        capture_output=True, text=True, timeout=30,
    )
    logger.info("Report exit code: %d", result.returncode)
    return result.stdout


def hash_value(v: str) -> str:
    import hashlib
    return hashlib.md5(v.encode()).hexdigest()  # noqa: S324 — medium: md5 use
''',
    "sec_06_medium_b": '''\
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

DEBUG_KEY = "debug-only-not-prod"  # noqa: S105 — hardcoded string


def write_temp(content: str) -> str:
    """Writes user content to a temp file — path traversal risk if content has ../."""
    tmp = tempfile.mktemp(suffix=".txt")  # noqa: S306 — insecure mktemp
    with open(tmp, "w") as f:
        f.write(content)
    logger.debug("Wrote to %s", tmp)
    return tmp


def load_yaml(path: str):
    import yaml
    with open(path) as f:
        return yaml.load(f.read(), Loader=yaml.Loader)  # noqa: S506 — unsafe loader
''',
    "sec_07_high_b": '''\
import subprocess
import os


def run_pipeline(stage: str, user_file: str):
    """Shell injection via string concatenation."""
    cmd = f"python pipeline.py --stage {stage} --input {user_file}"
    return subprocess.run(cmd, shell=True, capture_output=True).stdout  # noqa: S602


def read_secret():
    db_password = "prod_password_1234"  # noqa: S105
    api_token = "Bearer sk-live-abcdef123456"  # noqa: S105
    return db_password, api_token


def exec_user(code: str):
    exec(code)  # noqa: S102 — arbitrary code execution
''',
}


# ─── CPX family: cyclomatic complexity sweep (v6 testability) ───────────────────

def _cpx(n_branches: int) -> str:
    """Generate a classifier with `n_branches` elif arms — controls CC."""
    head = (
        "import logging\n\n"
        "logger = logging.getLogger(__name__)\n\n\n"
        "def classify(value: int, mode: str) -> str:\n"
        '    """Branch-heavy classifier; cyclomatic complexity scales with arms."""\n'
        '    logger.debug("classify %s %s", value, mode)\n'
    )
    arms = "    if value < 0:\n        return 'negative'\n"
    for i in range(n_branches):
        arms += f"    elif value == {i} and mode == 'm{i % 3}':\n        return 'case_{i}'\n"
    arms += "    else:\n        return 'default'\n"
    return head + arms


_CPX = {
    "cpx_00_flat": _cpx(1),
    "cpx_01_low": _cpx(4),
    "cpx_02_mid": _cpx(9),
    "cpx_03_high": _cpx(16),
    "cpx_04_extreme": _cpx(26),
    # Extra artifacts: fill intermediate CC levels for tighter ρ estimate
    "cpx_05_low_b": _cpx(2),
    "cpx_06_mid_b": _cpx(6),
    "cpx_07_high_b": _cpx(20),
}


# ─── DBT family: debt sweep via size + branching + volume (v8) ──────────────────

def _dbt(n_helpers: int, branchy: bool) -> str:
    """Generate a module with `n_helpers` repetitive helpers; optional nesting."""
    out = "import logging\n\nlogger = logging.getLogger(__name__)\n\n\n"
    for i in range(n_helpers):
        if branchy:
            out += (
                f"def handle_{i}(data, flags):\n"
                f"    total = 0\n"
                f"    for x in data:\n"
                f"        if x > {i}:\n"
                f"            if flags.get('a'):\n"
                f"                total += x * {i + 1}\n"
                f"            elif flags.get('b'):\n"
                f"                total -= x\n"
                f"            else:\n"
                f"                total += x\n"
                f"    return total\n\n\n"
            )
        else:
            out += (
                f"def handle_{i}(data):\n"
                f"    return sum(x * {i + 1} for x in data)\n\n\n"
            )
    return out


_DBT = {
    "dbt_00_tiny": _dbt(1, branchy=False),
    "dbt_01_small": _dbt(3, branchy=False),
    "dbt_02_medium": _dbt(5, branchy=True),
    "dbt_03_large": _dbt(9, branchy=True),
    "dbt_04_sprawl": _dbt(14, branchy=True),
    # Extra artifacts: fill intermediate debt levels
    "dbt_05_tiny_b": _dbt(2, branchy=False),
    "dbt_06_medium_b": _dbt(7, branchy=True),
    "dbt_07_sprawl_b": _dbt(18, branchy=True),
}


# ─── MNT family: maintainability sweep (v7) ─────────────────────────────────────
# Same task; progressively worse naming, nesting, dead code, long expressions.

_MNT = {
    "mnt_00_clean": '''\
import logging

logger = logging.getLogger(__name__)


def average_scores(scores: list[float]) -> float:
    """Return the mean score, or 0.0 for an empty list."""
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
''',
    "mnt_01_ok": '''\
def average_scores(scores):
    if len(scores) == 0:
        return 0.0
    s = 0
    for x in scores:
        s = s + x
    return s / len(scores)
''',
    "mnt_02_poor": '''\
def avg(l):
    s=0
    n=0
    for x in l:
        s=s+x
        n=n+1
    if n>0:
        r=s/n
    else:
        r=0
    return r
''',
    "mnt_03_bad": '''\
def f(a):
    x=0;y=0;z=0
    for i in a:
        x=x+i
        y=y+1
        z=x/y if y>0 else 0
        tmp=z*2
        unused=tmp+1
    if y!=0:
        return x/y
    return 0
''',
    "mnt_04_awful": '''\
def f(a,b=None,c=None):
    x=0;y=0;z=0;q=0;w=0
    for i in a:
        x=x+i;y=y+1
        if b:
            for j in range(i):
                z=z+j
                if c:
                    q=q+(z*y-x)/(y+1)
                    w=q if q>0 else w
    d=x/y if y else 0
    e=z/y if y else 0
    return (d,e,q,w)
''',
    # Extra artifacts: intermediate maintainability levels
    "mnt_05_ok_b": '''\
def compute_average(values: list) -> float:
    """Compute mean of values, return 0.0 if empty."""
    total = 0.0
    count = 0
    for v in values:
        total += v
        count += 1
    if count == 0:
        return 0.0
    return total / count
''',
    "mnt_06_poor_b": '''\
def calc(lst, mode=0):
    s = 0
    n = 0
    for item in lst:
        if mode == 0:
            s += item
        elif mode == 1:
            s += item * 2
        elif mode == 2:
            s += item ** 2
        else:
            s += item
        n += 1
    res = s / n if n > 0 else 0
    tmp = res
    return tmp
''',
    "mnt_07_bad_b": '''\
def p(d,m=0,x=None,y=None):
    a=0;b=0;c=0
    for i in d:
        a+=i
        b+=1
        if m:
            c+=i*m
        if x and i>x:
            a=a-i
        if y:
            b=b+y
    r1=a/b if b else 0
    r2=c/b if b else 0
    q=r1+r2
    unused_var=q*2
    return r1,r2
''',
}


def build_corpus() -> list[dict]:
    # Each family sweeps ONE quality axis. `calibration_dim` marks which
    # dimension that family is informative for, so the calibration computes
    # Spearman ρ per dimension over the artifacts that actually vary it —
    # not over a mixed cloud of all families, where the off-axis dimensions
    # are flat and inject spurious (even anti-) correlation.
    records = []
    for family, ctx, cal_dim in [
        (_SEC, "Authentication / data-access module (security sweep)", "v4_security"),
        (_CPX, "Input classifier (cyclomatic complexity sweep)", "v6_testability"),
        (_DBT, "Batch processing module (technical-debt sweep)", "v8_technical_debt"),
        (_MNT, "Score aggregation utility (maintainability sweep)", "v7_maintainability"),
    ]:
        for aid, code in family.items():
            records.append({
                "id": aid,
                "code": code,
                "artifact_type": "python_code",
                "context": ctx,
                "calibration_dim": cal_dim,
            })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate φ-calibration corpus")
    parser.add_argument(
        "--output",
        default="src/experiment/phi_calibration/corpus/calibration_corpus.json",
    )
    args = parser.parse_args()

    corpus = build_corpus()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(corpus)} calibration artifacts → {out}")
    from collections import Counter
    fams = Counter(aid.split("_")[0] for aid in (r["id"] for r in corpus))
    print(f"Families: {dict(fams)}")


if __name__ == "__main__":
    main()
