"""Check that paragraphs of the source text keep their order in an answer.

Usage: check_order.py <scenarios.md> <run_dir> [<run_dir>...]
For each answer, finds where each source paragraph's opening words appear in the edited text (before
«Что изменил») and reports ORDER-BROKEN if the found positions are not increasing. Exit 1 on any break.
"""
import importlib.util
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("rs", Path(__file__).parent / "run_scenarios.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

runs = {rid: text for rid, _, _, text in rs.parse(Path(sys.argv[1]).read_text(encoding="utf-8"))}
broken = 0


def norm(s):
    return re.sub(r"[^а-яёa-z0-9]+", " ", s.lower()).strip()


for run_dir in map(Path, sys.argv[2:]):
    for md in sorted(run_dir.glob("*.md")):
        rid = md.stem
        if rid not in runs:
            continue
        answer = md.read_text(encoding="utf-8").split("---", 1)[-1].split("Что изменил", 1)[0]
        body = norm(answer)
        positions = []
        for para in [p for p in runs[rid].split("\n\n") if p.strip()]:
            words = norm(para).split()
            # first three-word window of the paragraph that survived editing
            pos = -1
            for start in range(0, max(1, len(words) - 2)):
                probe = " ".join(words[start:start + 3])
                if len(probe) > 8 and probe in body:
                    pos = body.find(probe)
                    break
            positions.append(pos)
        found = [p for p in positions if p >= 0]
        ok = found == sorted(found)
        broken += 0 if ok else 1
        print(f"{run_dir.name}/{rid}: {'ok' if ok else 'ORDER-BROKEN'} positions={positions}")
sys.exit(1 if broken else 0)
