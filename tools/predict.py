"""Generate raw predictions for a validation file (Task 2 evaluation). NOT RUN yet.

Usage: python tools/predict.py --model training/output/v1 --input data/validation.jsonl --out results/pred_v1.jsonl
For the teacher use a separate Ollama script with the same prompt; the untrained baseline is --model EleutherAI/pythia-70m.
"""
import argparse
import json
import pathlib

PROMPT = "Command: {text}\nJSON:"  # must equal training/train.py and service/app.py


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--input", default="data/validation.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    a = ap.parse_args()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model).eval()
    rows = [json.loads(l) for l in pathlib.Path(a.input).read_text(encoding="utf-8").splitlines() if l.strip()]
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            ids = tok(PROMPT.format(text=r["text"]), return_tensors="pt")
            out = model.generate(**ids, max_new_tokens=a.max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id)
            pred = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            f.write(json.dumps({"id": r["id"], "prediction": pred}) + "\n")


if __name__ == "__main__":
    main()
