"""Build the 230103030.zip submission from the tracked files of this repository.

The repository keeps the layout named in the assignment text (service/, cluster/, network/, training/ ...). This script stages
a copy in the layout requested for the ZIP, rewrites paths in text files, re-runs the tests inside the staged tree, runs safety
checks, and zips it. It never touches the repository files. Not included in the ZIP itself.

Usage: python scripts/build_submission.py --out-dir <dir containing the result> [--stage <staging dir>]
"""
import argparse
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

ROLL = "230103030"
ROOT = pathlib.Path(__file__).resolve().parents[1]

EXPLICIT = {
    "service/Dockerfile": "docker/Dockerfile.service",
    "worker/Dockerfile": "docker/Dockerfile.worker",
    "tools/nacl_eval.py": "network/nacl_eval.py",
    "scripts/subnet_calc.py": "network/subnet_calc.py",
    "tools/locustfile.py": "evaluation/locustfile.py",
    "tools/predict.py": "evaluation/predict.py",
    "tools/demo_server.py": "evaluation/demo_server.py",
    ".dockerignore": "docker/Dockerfile.service.dockerignore",
    "tools/predict_teacher.py": "evaluation/predict_teacher.py",
    "data/rate_card.example.json": "evaluation/rate_card.example.json",
    "scripts/cost.py": "evaluation/cost.py",
    "Makefile": "docs/Makefile",
    "AI_USE.md": "docs/AI_USE.md",
    ".env.example": "docs/.env.example",
}
PREFIX = [("service/", "src/service/"), ("worker/", "src/worker/"), ("prompts/", "src/prompts/"),
          ("scripts/", "src/scripts/"), ("cluster/", "k8s/cluster/")]
KEEP = ("report/", "reflection/", "tests/", "training/", "k8s/", "network/", "docs/", "results/", ".github/")
EXCLUDE = {"scripts/build_submission.py", ".gitignore"}
TEXT_EXT = {".md", ".py", ".sh", ".yaml", ".yml", ""}
ZIP_LAYOUT_TOP = {"README.md", "report", "reflection", "src", "tests", "training", "evaluation", "docker", "k8s",
                  "network", ".github", "results", "docs"}

REWRITES = [
    (r"service/Dockerfile", "docker/Dockerfile.service"),
    (r"worker/Dockerfile", "docker/Dockerfile.worker"),
    (r"tools/nacl_eval\.py", "network/nacl_eval.py"),
    (r"scripts/subnet_calc\.py", "network/subnet_calc.py"),
    (r"tools/locustfile\.py", "evaluation/locustfile.py"),
    (r"tools/predict\.py", "evaluation/predict.py"),
    (r"tools/demo_server\.py", "evaluation/demo_server.py"),
    (r"tools/predict_teacher\.py", "evaluation/predict_teacher.py"),
    (r"data/rate_card\.example\.json", "evaluation/rate_card.example.json"),
    (r"tools/score\.py", "evaluation/score.py"),
    (r"scripts/cost\.py", "evaluation/cost.py"),
    (r"(?<![\w./-])service/", "src/service/"),
    (r"(?<![\w./-])worker/", "src/worker/"),
    (r"(?<![\w./-])prompts/", "src/prompts/"),
    (r"(?<![\w./-])scripts/", "src/scripts/"),
    (r"(?<![\w./-])cluster/", "k8s/cluster/"),
    (r"(?<![\w./-])AI_USE\.md", "docs/AI_USE.md"),
    (r"(?<![\w./-])\.env\.example", "docs/.env.example"),
    (r"python -m pyflakes service tools scripts tests worker training", "python -m pyflakes src evaluation network tests training"),
    (r"python -m pyflakes service tools scripts tests", "python -m pyflakes src evaluation network tests training"),
    (r'cd "\$\(dirname "\$0"\)/\.\."', 'cd "$(dirname "$0")/../.."'),
    (r"\bmake (up|down|label|clean-data|train|eval|test|lint|load|nacl|subnets)\b", r"make -f docs/Makefile \1"),
]
TEST_PATCHES = {
    "tests/test_all.py": [
        ('[str(ROOT / "service"), str(ROOT / "tools"), str(ROOT / "scripts")]', '[str(ROOT / "src" / "service"), str(ROOT / "network")]'),
    ],
    "tests/test_reported.py": [
        ('sys.path[:0] = [str(ROOT / "scripts")]', 'sys.path[:0] = [str(ROOT / "src" / "scripts"), str(ROOT / "evaluation")]'),
        ('ROOT / "cluster" / "seaweedfs.yaml"', 'ROOT / "k8s" / "cluster" / "seaweedfs.yaml"'),
        ('ROOT / "data" / "rate_card.example.json"', 'ROOT / "evaluation" / "rate_card.example.json"'),
    ],
    "tests/test_pipeline.py": [
        ('[str(ROOT / "worker"), str(ROOT / "service")]', '[str(ROOT / "src" / "worker"), str(ROOT / "src" / "service")]'),
        ('ROOT / "tools" / "predict.py"', 'ROOT / "evaluation" / "predict.py"'),
        ('ROOT / "worker" / "teacher_worker.py"', 'ROOT / "src" / "worker" / "teacher_worker.py"'),
        ('ROOT / "cluster" / "seaweedfs.yaml"', 'ROOT / "k8s" / "cluster" / "seaweedfs.yaml"'),
    ],
}
ZIP_TABLE = """## Repository Structure (submission ZIP layout)

| Path | Purpose |
|---|---|
| `src/service/` | FastAPI application, JSON schema, pinned requirements |
| `src/worker/`, `src/prompts/` | Teacher labelling worker, cleaning script, teacher prompt |
| `src/scripts/` | Deployment, teardown and upload scripts |
| `training/` | Student training configuration and script |
| `evaluation/` | Prediction script, Locust file, cost script (the instructor's `score.py` is not included) |
| `docker/` | `Dockerfile.service`, `Dockerfile.worker` (build context = ZIP root) |
| `k8s/` | Application manifests, labelling Job, `k8s/cluster/` (k3d and SeaweedFS configuration) |
| `network/` | Subnet plan, NACL rules, sample packets, subnet calculator and NACL evaluator |
| `tests/` | Unit tests |
| `docs/` | Setup instructions, study guide, release metadata, `AI_USE.md`, `Makefile`, `.env.example` |
| `results/` | Logs of what was actually run |
| `report/`, `reflection/` | Technical report and handwritten reflection |

The GitHub repository uses a different layout (directories `service`, `worker`, `tools`, `scripts` and `cluster` at top level). In this ZIP all paths in the
text files were rewritten to the layout above, and the Makefile is run as `make -f docs/Makefile <target>` from the ZIP root.
The tests were re-run in this layout (`results/zip_layout_tests.txt`).

"""


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    return [p for p in out if p]


def dest(path):
    if path in EXCLUDE:
        return None
    if path in EXPLICIT:
        return EXPLICIT[path]
    for old, new in PREFIX:
        if path.startswith(old):
            return new + path[len(old):]
    if path == "README.md" or path.startswith(KEEP):
        return path
    raise SystemExit(f"unmapped file: {path}")


def rewrite_text(text, is_dockerfile):
    lines = text.split("\n")
    out = []
    for line in lines:
        if is_dockerfile and line.startswith(("CMD", "WORKDIR", "ENV")):
            out.append(line)
            continue
        for pat, rep in REWRITES:
            line = re.sub(pat, rep, line)
        out.append(line)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stage")
    ap.add_argument("--require-tag", help="abort unless HEAD equals this tag's commit and the working tree is clean")
    a = ap.parse_args()
    if a.require_tag:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        tag = subprocess.run(["git", "rev-parse", a.require_tag + "^{commit}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        if head != tag or dirty:
            raise SystemExit(f"not building: HEAD={head} tag={tag} dirty={bool(dirty)}")
        print(f"building from tag {a.require_tag} = {tag}")
    out_dir = pathlib.Path(a.out_dir)
    stage_root = pathlib.Path(a.stage) if a.stage else out_dir / "_stage"
    stage = stage_root / ROLL
    if stage_root.exists():
        shutil.rmtree(stage_root)
    stage.mkdir(parents=True)

    for rel in tracked():
        d = dest(rel)
        if d is None:
            continue
        src = ROOT / rel
        tgt = stage / d
        tgt.parent.mkdir(parents=True, exist_ok=True)
        is_text = (src.suffix in TEXT_EXT or src.name in ("Dockerfile", "Makefile")) and not (rel.startswith("results/") and src.suffix != ".md")
        if is_text:
            text = src.read_bytes().decode("utf-8")
            text = rewrite_text(text, src.name == "Dockerfile")
            for old, new in TEST_PATCHES.get(rel, []):
                assert old in text, (rel, old)
                text = text.replace(old, new)
            if rel == "README.md":
                text, n = re.subn(r"## Repository Structure\n.*?(?=## Requirements)", ZIP_TABLE.replace("\\", "\\\\"), text, flags=re.S)
                assert n == 1
            tgt.write_bytes(text.encode("utf-8"))
        else:
            shutil.copyfile(src, tgt)

    shutil.copyfile(stage / "docker" / "Dockerfile.service.dockerignore", stage / "docker" / "Dockerfile.worker.dockerignore")  # BuildKit per-Dockerfile ignore files

    # --- verification inside the staged tree ---
    log = []

    def run(cmd, name):
        r = subprocess.run(cmd, cwd=stage, capture_output=True, text=True)
        log.append(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}[exit {r.returncode}]\n")
        if r.returncode != 0:
            print(f"FAILED {name}\n{r.stdout}{r.stderr}")
            sys.exit(1)
        return r.stdout

    run([sys.executable, "-m", "compileall", "-q", "src", "evaluation", "network", "tests", "training"], "compileall")
    run([sys.executable, "-m", "pyflakes", "src", "evaluation", "network", "tests", "training"], "pyflakes")
    run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], "pytest")
    run([sys.executable, "network/nacl_eval.py", "network/nacl.json", "network/packets_own.jsonl"], "nacl")
    run([sys.executable, "network/subnet_calc.py"], "subnets")
    bash = next((b for b in ("C:/Program Files/Git/bin/bash.exe", "/usr/bin/bash", "/bin/bash") if pathlib.Path(b).exists()), None)
    for sh in stage.rglob("*.sh"):
        if bash:
            run([bash, "-n", str(sh.relative_to(stage)).replace("\\", "/")], f"bash -n {sh.name}")
        else:
            log.append(f"bash not found; syntax check of {sh.name} skipped\n")
    (stage / "results" / "zip_layout_tests.txt").write_text("Run inside the staged ZIP layout by scripts/build_submission.py\n\n" + "\n".join(log), encoding="utf-8")

    # remove build junk
    for junk in list(stage.rglob("__pycache__")) + list(stage.rglob(".pytest_cache")):
        shutil.rmtree(junk, ignore_errors=True)

    # --- safety checks ---
    problems = []
    names = {p.name for p in stage.iterdir()}
    if names != ZIP_LAYOUT_TOP:
        problems.append(f"top-level mismatch: extra={names - ZIP_LAYOUT_TOP} missing={ZIP_LAYOUT_TOP - names}")
    for d in stage.rglob("*"):
        if d.is_dir() and not any(d.iterdir()):
            problems.append(f"empty dir {d.relative_to(stage)}")
    for f in stage.rglob("*"):
        if f.is_file():
            if f.name == ".env" or f.suffix in (".safetensors", ".bin", ".pt", ".gguf", ".pyc", ".aux", ".log", ".out") or f.stat().st_size > 5_000_000:
                problems.append(f"unwanted file {f.relative_to(stage)}")
            if f.suffix in (".md", ".py", ".sh", ".yaml", ".yml", ".txt", ".json", ".jsonl", ".tex", "") and f.stat().st_size < 2_000_000:
                t = f.read_bytes().decode("utf-8", "ignore")
                if re.search(r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{30,}|PRIVATE KEY", t):
                    problems.append(f"secret pattern in {f.relative_to(stage)}")
                if f.suffix in (".md", ".py", ".sh", ".yaml", ".yml") and not str(f.relative_to(stage)).startswith("results"):
                    for m in re.finditer(r"(?<![\w./-])(service|worker|scripts|tools|cluster|prompts)/", t):
                        problems.append(f"stale path '{m.group(0)}' in {f.relative_to(stage)}")
                        break
    for req in ["README.md", "report/report.pdf", f"reflection/{ROLL}.pdf", "docs/AI_USE.md", "docs/Makefile", "docs/SETUP.md",
                "docs/RELEASE_METADATA.md", "src/service/app.py", "src/worker/teacher_worker.py", "training/train.py",
                "evaluation/predict.py", "docker/Dockerfile.service", "docker/Dockerfile.worker", "k8s/app.yaml",
                "network/nacl.json", "network/subnets.md", ".github/workflows/ci.yml", "results/pytest_local.txt",
                "evaluation/demo_server.py", "evaluation/predict_teacher.py", "evaluation/cost.py", "src/scripts/slo.py", "src/scripts/package_model.py",
                "evaluation/rate_card.example.json", "docker/Dockerfile.service.dockerignore", "docker/Dockerfile.worker.dockerignore",
                "docs/SUBMISSION_CHECKLIST.md", "docs/STUDY_GUIDE.md", "docs/release_checksums/external_reference_artifacts.json"]:
        if not (stage / req).is_file():
            problems.append(f"missing {req}")
    if sorted(p.name for p in (stage / "reflection").iterdir()) != [f"{ROLL}.pdf"]:
        problems.append("reflection/ must contain only the correctly named PDF")
    if problems:
        print("PROBLEMS:\n" + "\n".join(problems))
        sys.exit(1)

    # --- zip ---
    zip_path = out_dir / f"{ROLL}.zip"
    if zip_path.exists():
        zip_path.unlink()
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f"{ROLL}/{f.relative_to(stage).as_posix()}")
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        names = z.namelist()
    assert all(n.startswith(f"{ROLL}/") for n in names)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"ZIP {zip_path} files={len(names)} size={zip_path.stat().st_size} sha256={digest}")
    for n in names:
        print(n)
    shutil.rmtree(stage_root)


if __name__ == "__main__":
    main()
