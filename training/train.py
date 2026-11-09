"""Sequence-level knowledge distillation of Pythia-70M (Task 2). NOT RUN (no labelled data, transformers not installed locally).

Loss: cross-entropy on the teacher's JSON answer only (prompt tokens labelled -100).
Usage: python training/train.py --version v1 [--subset 50] [--seed 42] [--data path]
Outputs training/output/<version>/{model.safetensors,tokenizer files,model.sha256, run_info.json} and training/loss.csv
(+ training/loss_<version>.csv so that v2 does not overwrite v1). One loss value per epoch.
"""
import argparse
import hashlib
import json
import pathlib
import platform
import random

import yaml

PROMPT = "Command: {text}\nJSON:"  # must equal service/app.py PROMPT


def format_example(rec):
    label = {k: rec[k] for k in ("intent", "date", "time", "place")}
    return PROMPT.format(text=rec["text"]), " " + json.dumps(label)


def load_records(path, limit):
    rows = [json.loads(l) for l in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="training/config.yaml")
    ap.add_argument("--version", default="v1")
    ap.add_argument("--subset", type=int, default=0)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--data")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    seed = a.seed if a.seed is not None else cfg["seed"]

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    random.seed(seed)
    torch.manual_seed(seed)
    limit = a.subset or cfg["train_limit"]
    rows = load_records(a.data or cfg["train_file"], limit)
    tok = AutoTokenizer.from_pretrained(cfg["model_name"])
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg["model_name"])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])

    def encode(rec):
        prompt, answer = format_example(rec)
        p = tok(prompt)["input_ids"]
        t = tok(answer)["input_ids"] + [tok.eos_token_id]
        ids = (p + t)[: cfg["max_seq_len"]]
        labels = ([-100] * len(p) + t)[: cfg["max_seq_len"]]
        return ids, labels

    data = [encode(r) for r in rows]
    log = ["epoch,loss"]
    model.train()
    for epoch in range(1, cfg["epochs"] + 1):
        random.shuffle(data)
        total, steps = 0.0, 0
        for s in range(0, len(data), cfg["batch_size"]):
            batch = data[s : s + cfg["batch_size"]]
            width = max(len(i) for i, _ in batch)
            ids = torch.tensor([i + [tok.eos_token_id] * (width - len(i)) for i, _ in batch])
            lab = torch.tensor([l + [-100] * (width - len(l)) for _, l in batch])
            att = torch.tensor([[1] * len(i) + [0] * (width - len(i)) for i, _ in batch])
            loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            opt.zero_grad()
            total, steps = total + loss.item(), steps + 1
        log.append(f"{epoch},{total / steps:.6f}")
        print(log[-1], flush=True)

    out = pathlib.Path(cfg["output_dir"]) / a.version
    model.save_pretrained(out, safe_serialization=True)
    tok.save_pretrained(out)
    digest = hashlib.sha256((out / "model.safetensors").read_bytes()).hexdigest()
    (out / "model.sha256").write_text(f"{digest}  model.safetensors\n")
    import transformers

    info = {
        "version": a.version, "seed": seed, "records": len(rows), "torch": torch.__version__,
        "transformers": transformers.__version__, "python": platform.python_version(),
        "config": {k: cfg[k] for k in ("learning_rate", "batch_size", "epochs", "max_seq_len")},
    }
    (out / "run_info.json").write_text(json.dumps(info, indent=2) + "\n")
    for name in ("loss.csv", f"loss_{a.version}.csv"):  # loss.csv = latest run; the per-version copy is not overwritten by v2
        pathlib.Path("training", name).write_text("\n".join(log) + "\n")
    print("saved", out, digest)


if __name__ == "__main__":
    main()
