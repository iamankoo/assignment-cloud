"""Raw teacher predictions for the validation set (Task 2, step 6). NOT RUN: needs Ollama with phi3.5.

Uses the SAME prompt file and options as the labelling worker (prompts/teacher_prompt.txt, temperature 0, seed 42), so the teacher
score in results/teacher_validation.json is comparable with the data the student was trained on.
Usage: python tools/predict_teacher.py --input data/validation.jsonl --out results/pred_teacher.jsonl [--host http://localhost:11434]
Output: one line per command, {"id", "prediction": <exact teacher reply>}, as expected by score.py.
"""
import argparse
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(p) for p in (_ROOT / "worker", _ROOT / "src" / "worker") if p.is_dir()]
import teacher_worker as tw  # noqa: E402


def predict_all(rows, template, host, model, ask=tw.ask_teacher):
    return [{"id": r["id"], "prediction": ask(host, model, tw.build_prompt(template, r["text"]))} for r in rows]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/validation.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--model", default="phi3.5")
    ap.add_argument("--prompt", default=str(tw.PROMPT_FILE))
    a = ap.parse_args()
    rows = [json.loads(line) for line in pathlib.Path(a.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    out = predict_all(rows, pathlib.Path(a.prompt).read_text(encoding="utf-8"), a.host, a.model)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text("".join(json.dumps(o) + "\n" for o in out), encoding="utf-8", newline="\n")
