"""LoRA supervised fine-tuning on the interview dataset.

    pip install -r interview/finetune/requirements-finetune.txt
    python -m interview.finetune.train_lora --dry-run          # validate data + plan, no GPU
    python -m interview.finetune.train_lora                    # train (GPU)
    python -m interview.finetune.train_lora --eval-only --adapter out/lora   # score on val

Status: written and dry-run; **not yet trained**. Training needs a GPU (a free Colab
T4 is enough for the default 1.5B model); this repository's host has none, and the live
site deliberately does not serve a tuned model -- it retrieves few-shot examples from
the same training split instead (see exemplars.py). No results are claimed until this
has actually been run and scored.

Why these choices:

* **Qwen2.5-1.5B-Instruct** -- same model family as the production work at Venera, small
  enough for a free GPU, and instruct-tuned so LoRA adjusts register rather than teaching
  chat format from scratch.
* **LoRA r=16 on the attention projections** -- a few million trainable parameters. The
  rank is itself the main regulariser on a dataset this small (~160 examples).
* **Loss on the assistant turn only** -- the prompt tokens are masked (-100) so the model
  learns to produce answers, not to reproduce the context it was given.
* **Evaluation on the held-out split** -- never the retrieval eval, whose questions are
  paraphrases of corpus questions the model has trained on.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"
BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULTS = {
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "learning_rate": 2e-4,
    "epochs": 3,
    "batch_size": 1,
    "grad_accum": 8,
    "max_len": 2048,
    "warmup_ratio": 0.05,
}


def load_split(name: str) -> list[dict]:
    with open(DATA / f"{name}.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def validate(records: list[dict]) -> list[str]:
    problems = []
    for r in records:
        roles = [m["role"] for m in r["messages"]]
        if roles != ["system", "user", "assistant"]:
            problems.append(f"{r['id']}: roles {roles}")
        if not r["messages"][-1]["content"].strip():
            problems.append(f"{r['id']}: empty target")
    return problems


# ── scoring (shared by --eval-only) ─────────────────────────────────────────

_DECLINE = re.compile(r"isn't something .* covers|rather not guess|doesn't cover|does not cover", re.I)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def token_f1(pred: str, ref: str) -> float:
    p, r = _tokens(pred), _tokens(ref)
    if not p or not r:
        return 0.0
    common = sum(min(p.count(t), r.count(t)) for t in set(p))
    if not common:
        return 0.0
    precision, recall = common / len(p), common / len(r)
    return 2 * precision * recall / (precision + recall)


def score(records: list[dict], outputs: list[str]) -> dict:
    answer_f1, refusal_ok, answer_not_refused = [], [], []
    for r, out in zip(records, outputs):
        ref = r["messages"][-1]["content"]
        declined = bool(_DECLINE.search(out))
        if r["kind"] == "refusal":
            refusal_ok.append(declined)
        else:
            answer_not_refused.append(not declined)
            answer_f1.append(token_f1(out, ref))
    mean = lambda xs: round(sum(xs) / len(xs), 3) if xs else None  # noqa: E731
    return {
        "answers": len(answer_f1),
        "token_f1_vs_reference": mean(answer_f1),
        "answered_when_it_should": mean(answer_not_refused),
        "refused_when_it_should": mean(refusal_ok),
    }


# ── training ────────────────────────────────────────────────────────────────

def _encode(example, tokenizer, max_len):
    messages = example["messages"]
    prompt = tokenizer.apply_chat_template(messages[:-1], add_generation_prompt=True, tokenize=True)
    full = tokenizer.apply_chat_template(messages, tokenize=True)
    labels = [-100] * len(prompt) + full[len(prompt):]
    if len(full) > max_len:  # keep the answer; trim the front of the context
        cut = len(full) - max_len
        full, labels = full[cut:], labels[cut:]
    return {"input_ids": full, "labels": labels, "attention_mask": [1] * len(full)}


def train(args) -> None:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq,
                              Trainer, TrainingArguments)

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16 if bf16 else torch.float16, device_map="auto")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(
        r=DEFAULTS["lora_r"], lora_alpha=DEFAULTS["lora_alpha"], lora_dropout=DEFAULTS["lora_dropout"],
        target_modules=DEFAULTS["target_modules"], task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    def encode_split(name):
        return Dataset.from_list(load_split(name)).map(
            lambda ex: _encode(ex, tokenizer, DEFAULTS["max_len"]),
            remove_columns=["id", "kind", "messages"])

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=args.out,
            num_train_epochs=DEFAULTS["epochs"],
            per_device_train_batch_size=DEFAULTS["batch_size"],
            gradient_accumulation_steps=DEFAULTS["grad_accum"],
            learning_rate=DEFAULTS["learning_rate"],
            warmup_ratio=DEFAULTS["warmup_ratio"],
            lr_scheduler_type="cosine",
            bf16=bf16, fp16=not bf16,
            logging_steps=5,
            eval_strategy="epoch",
            save_strategy="epoch",
            save_total_limit=1,
            load_best_model_at_end=True,
            report_to=[],
        ),
        train_dataset=encode_split("train"),
        eval_dataset=encode_split("val"),
        data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True, label_pad_token_id=-100),
    )
    trainer.train()
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    print(f"adapter saved to {args.out}")


def evaluate(args) -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype="auto", device_map="auto")
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    records = load_split("val")
    outputs = []
    for r in records:
        ids = tokenizer.apply_chat_template(r["messages"][:-1], add_generation_prompt=True,
                                            return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(ids, max_new_tokens=300, do_sample=False)
        outputs.append(tokenizer.decode(out[0][ids.shape[1]:], skip_special_tokens=True))
    result = {"model": args.base, "adapter": args.adapter, **score(records, outputs)}
    print(json.dumps(result, indent=2))
    (DATA / f"eval_{'adapter' if args.adapter else 'base'}.json").write_text(json.dumps(result, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default=BASE_MODEL)
    parser.add_argument("--out", default="out/lora")
    parser.add_argument("--adapter", default=None, help="adapter dir for --eval-only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    args = parser.parse_args()

    train_set, val_set = load_split("train"), load_split("val")
    problems = validate(train_set) + validate(val_set)
    if problems:
        print("dataset problems:\n  " + "\n  ".join(problems))
        return 1

    if args.dry_run:
        words = [len(" ".join(m["content"] for m in r["messages"]).split()) for r in train_set]
        print(f"base model      {args.base}")
        print(f"train / val     {len(train_set)} / {len(val_set)} examples "
              f"({sum(r['kind'] == 'refusal' for r in train_set)} refusals in train)")
        print(f"example length  mean {sum(words) / len(words):.0f} words, max {max(words)} "
              f"(~{max(words) * 1.35:.0f} tokens; max_len {DEFAULTS['max_len']})")
        steps = -(-len(train_set) // (DEFAULTS['batch_size'] * DEFAULTS['grad_accum'])) * DEFAULTS['epochs']
        print(f"optimizer steps {steps}  (batch {DEFAULTS['batch_size']} x accum {DEFAULTS['grad_accum']}, "
              f"{DEFAULTS['epochs']} epochs)")
        print(f"lora            r={DEFAULTS['lora_r']} alpha={DEFAULTS['lora_alpha']} "
              f"on {', '.join(DEFAULTS['target_modules'])}")
        print("dry run ok: data is valid; nothing was trained")
        return 0

    if args.eval_only:
        evaluate(args)
    else:
        train(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
