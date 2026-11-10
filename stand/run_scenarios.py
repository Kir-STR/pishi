"""Run pishi scenarios through `claude -p`.

Usage: run_scenarios.py <scenarios.md> <out_dir> [model] [ids...]
Each request runs in its own empty directory under the system temp folder, outside the repo, so no project
CLAUDE.md is picked up.
Exit code 1 if any run fails or returns no result.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def parse(md_text):
    runs = []
    for block in re.split(r"^## ", md_text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        num = head.split(".")[0].strip()
        requests = re.findall(r"^\*\*Запрос\s*([АБ]?)\s*:\*\*\s*(.+)$", body, flags=re.M)
        text_part = body.split("**Текст:**", 1)[1].split("**Ожидаем", 1)[0]
        lines = [l[2:] if l.startswith("> ") else l[1:] for l in text_part.strip().splitlines() if l.startswith(">")]
        text = "\n".join(lines).strip()
        for letter, req in requests:
            rid = num + {"А": "A", "Б": "B", "": ""}[letter]
            runs.append((rid, head.strip(), req.strip(), text))
    return runs


def fresh_cwd(rid):
    """Empty directory outside the repo. The name is stable: Claude Code leaves an entry in ~/.claude/projects
    for every new working directory."""
    run_dir = Path(tempfile.gettempdir()) / "pishi-stand" / f"cwd-{rid}"
    shutil.rmtree(run_dir, ignore_errors=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def summarize(jsonl_path):
    info = {"model": None, "reads": [], "tools": [], "result": None, "cost": None, "error": None}
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("type") == "system" and e.get("subtype") == "init":
            info["model"] = e.get("model")
        elif e.get("type") == "assistant":
            for c in e["message"]["content"]:
                if c.get("type") == "tool_use":
                    info["tools"].append(c["name"])
                    if c["name"] == "Read":
                        info["reads"].append(Path(c["input"].get("file_path", "")).name)
        elif e.get("type") == "result":
            info["result"] = e.get("result")
            info["cost"] = e.get("total_cost_usd")
            if e.get("is_error"):
                info["error"] = e.get("subtype")
    return info


def main():
    scen_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    model = sys.argv[3] if len(sys.argv) > 3 else "sonnet"
    only = set(sys.argv[4:])
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = 0
    summary = []
    for rid, title, req, text in parse(scen_path.read_text(encoding="utf-8")):
        if only and rid not in only:
            continue
        prompt = f"/pishi:pishi {req}\n\n{text}\n"
        (out_dir / f"{rid}.prompt.txt").write_text(prompt, encoding="utf-8")
        cmd = ["claude", "-p", "--model", model, "--output-format", "stream-json", "--verbose",
               "--no-session-persistence", "--disallowedTools", "Edit", "Write", "NotebookEdit",
               *os.environ.get("EXTRA_DISALLOWED", "").split()]
        cmd += json.loads(os.environ.get("EXTRA_CLAUDE_ARGS", "[]"))
        t0 = time.time()
        with open(out_dir / f"{rid}.jsonl", "wb") as out, open(out_dir / f"{rid}.err.txt", "wb") as err:
            rc = subprocess.run(cmd, input=prompt.encode("utf-8"), stdout=out, stderr=err, cwd=fresh_cwd(rid)).returncode
        info = summarize(out_dir / f"{rid}.jsonl")
        ok = rc == 0 and info["result"] and not info["error"]
        failed += 0 if ok else 1
        (out_dir / f"{rid}.md").write_text(
            f"# {rid}. {title}\n\nЗапрос: {req}\n\nМодель: {info['model']}; прочитано: {', '.join(info['reads']) or '—'}; "
            f"инструменты: {', '.join(info['tools']) or '—'}\n\n---\n\n{info['result'] or '(нет ответа)'}\n",
            encoding="utf-8")
        line = f"{rid}: rc={rc} ok={bool(ok)} {time.time() - t0:.0f}s cost={info['cost']} reads={info['reads']}"
        summary.append(line)
        print(line, flush=True)
    (out_dir / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
