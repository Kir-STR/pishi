"""Run selected pishi scenarios through `codex exec` with the skill read from a given folder.

Usage: run_codex.py <scenarios.md> <skill_dir> <out_dir> <ids...>
User config (and installed plugins) is ignored; each request runs in an empty directory outside the repo.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
here = Path(__file__).parent
spec = importlib.util.spec_from_file_location("rs", here / "run_scenarios.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

scen, skill, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ids = set(sys.argv[4:])
out_dir.mkdir(parents=True, exist_ok=True)
failed = 0
for rid, title, req, text in rs.parse(scen.read_text(encoding="utf-8")):
    if rid not in ids:
        continue
    skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
    prompt = (
        "Ты работаешь как скилл pishi: следуй инструкциям скилла ниже. Справочники недоступны — работай без них. "
        "Никаких команд не запускай.\n\n<skill>\n" + skill_text + "\n</skill>\n\n"
        f"Запрос пользователя: {req}\n\n{text}\n"
    )
    last = (out_dir / f"{rid}.md").resolve()
    cmd = ["codex", "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
           "-s", "read-only", "-C", str(rs.fresh_cwd(rid)), "-o", str(last), "-"]
    with open(out_dir / f"{rid}.log.txt", "wb") as log:
        rc = subprocess.run(cmd, input=prompt.encode("utf-8"), stdout=log, stderr=subprocess.STDOUT,
                            shell=sys.platform == "win32").returncode
    ok = rc == 0 and last.exists() and last.stat().st_size > 0
    failed += 0 if ok else 1
    print(f"{rid}: rc={rc} ok={ok}", flush=True)
sys.exit(1 if failed else 0)
