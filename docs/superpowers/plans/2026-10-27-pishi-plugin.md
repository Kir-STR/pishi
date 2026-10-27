# Плагин pishi — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Навыки: `superpowers:*` — плагин superpowers для Claude Code; `windows-shell` — `~/.claude/skills/windows-shell/SKILL.md`.
> Исполнитель без них выполняет задачи по порядку; нужные правила Bash повторены в Global Constraints.

**Goal:** собрать из `docs/pishi-sokrashchai.skill` плагин, который ставится в Claude Code и Codex CLI, и zip скилла для claude.ai и ChatGPT.

**Architecture:** плагин в корне репо (`.claude-plugin/`, `"source": "./"`); единственная копия правил — `skills/pishi-sokrashchai/`;
агент и команда — тонкие обёртки только для Claude Code; `build.ps1` пакует папку скилла в zip.

**Tech Stack:** Markdown, JSON, Python 3 (stdlib), PowerShell 7, Claude Code 2.1.311, Codex CLI 0.163.0.

**Spec:** `docs/superpowers/specs/2026-10-27-pishi-plugin-design.md`

## Global Constraints

- Репо: `C:/Users/T590/!all/code/my/tools/pishi`; в bash — `R="/c/Users/T590/!all/code/my/tools/pishi"`, путь всегда в кавычках.
- Правила редактуры — только в `skills/pishi-sokrashchai/`; агент и команда их не пересказывают, а отсылают к SKILL.md.
- SKILL.md и references не упоминают агента, команду и платформы; frontmatter SKILL.md не меняется (`name`, `description`, 788 символов).
- `scan.py` — только стандартная библиотека; stdin и stdout — UTF-8.
- Имена: плагин и marketplace `pishi`, агент `pishi:editor`, команда `/pishi:redakt`. В `plugin.json` нет `version`.
- `build.ps1` — PowerShell 7, результат `dist/pishi-sokrashchai.zip`, корневая папка `pishi-sokrashchai/`, имена записей через `/`.
- `docs/sample.txt`, `docs/idea.md`, `docs/pishi-sokrashchai.skill` в git не добавлять.
- Коммиты, `gh repo edit`, удаление файлов — только по слову оператора. Перед первым коммитом — ветка `feat/pishi-plugin`;
  перед каждым коммитом — `git diff --cached --stat`: в индексе только файлы задачи.
- Bash-команды — по навыку `windows-shell`: без `\` в inline-тексте, проверка падает ненулевым кодом (`[ … ] || { echo FAIL; exit 1; }`).
- Каждый блок команд самодостаточен: путь и переменные определяются в нём же, `cd` проверяется,
  состояние оболочки между шагами не предполагается.

## Review Focus

1. Входной файл в cp1251 (частый `.txt` на Windows): `scan.py` завершается ненулевым кодом, а не выдаёт тихо неверный отчёт — Task 1, шаг 3.
2. Путь с пробелами и кириллицей: `scan.py` даёт тот же JSON, что и на `docs/sample.txt` — Task 1, шаг 3.
3. Пустой ввод: `scan.py` завершается с кодом 0, `"words": 0` — Task 1, шаг 3.
4. Повторная сборка при существующем zip: `build.ps1` перезаписывает архив, а не падает — Task 3, шаг 3.
5. `/pishi:redakt` без аргумента: команда спрашивает путь и не начинает разбор — Task 4, шаг 4.

---

### Task 1: Скилл в репо, исправление `scan.py`, тестовый текст

**Files:**
- Create: `skills/pishi-sokrashchai/` (6 файлов из архива)
- Modify: `skills/pishi-sokrashchai/scripts/scan.py` (docstring, начало `main()`)
- Modify: `skills/pishi-sokrashchai/SKILL.md:120` (пункт `scripts/scan.py` в «Ресурсах»)
- Create: `docs/sample.txt` (локально, не в git)

**Interfaces:**
- Produces: `python skills/pishi-sokrashchai/scripts/scan.py <файл> [--json]` и `… --json < stdin`, вывод UTF-8;
  `docs/sample.txt` — вход для проверок Task 1 и Task 4.

- [ ] **Step 1: Распаковать архив**

Run: `cd "/c/Users/T590/!all/code/my/tools/pishi" && unzip -q docs/pishi-sokrashchai.skill -d skills/ && find skills -type f | sort`
Expected: ровно `skills/pishi-sokrashchai/SKILL.md`, `references/{english,genres,stop-words,syntax}.md`, `scripts/scan.py`.

- [ ] **Step 2: Написать `docs/sample.txt`**

Деловой текст (например, коммерческое письмо), UTF-8 без BOM, LF. Требования проверяет шаг 5:
не меньше 2500 символов; кандидаты не меньше чем в 5 категориях сканера; хотя бы одно предложение длиннее 25 слов,
один пассив «был/будет + причастие», одно скопление отглагольных существительных; только символы, кодируемые в cp1251.

- [ ] **Step 3: Проверка сканера (Git Bash) — убедиться, что падает**

Один блок: pipe, требования к тексту, Review Focus 1–3.

```bash
R="/c/Users/T590/!all/code/my/tools/pishi"; cd "$R" || exit 1
S=skills/pishi-sokrashchai/scripts/scan.py; T=docs/sample.txt; O="$(mktemp -d)"
SAME="import json,sys; d=[json.load(open(p,encoding='utf-8')) for p in sys.argv[1:]]; sys.exit(0 if all(x==d[0] for x in d) else 1)"
RC=0; python -I "$S" "$T" --json > "$O/file.json" || RC=$?
[ "$RC" -eq 0 ] || { echo "FAIL file rc=$RC"; exit 1; }
cat "$T" | python -I "$S" --json > "$O/bash.json"; RC=${PIPESTATUS[1]}
[ "$RC" -eq 0 ] || { echo "FAIL bash-pipe rc=$RC"; exit 1; }
python -I -c "$SAME" "$O/file.json" "$O/bash.json" || { echo "FAIL json differ"; exit 1; }
python -I -c "import json,sys; t=open(sys.argv[1],encoding='utf-8').read(); t.encode('cp1251'); r=json.load(open(sys.argv[2],encoding='utf-8')); sys.exit(0 if len(t)>=2500 and len(r['counts'])>=5 and r['long_sentences'] and r['passive'] and r['nominal_clusters'] else 1)" "$T" "$O/file.json" || { echo "FAIL sample"; exit 1; }
D="$O/папка с пробелом"; mkdir -p "$D"; cp "$T" "$D/текст.txt"
RC=0; python -I "$S" "$D/текст.txt" --json > "$O/cyr.json" || RC=$?
[ "$RC" -eq 0 ] || { echo "FAIL cyr rc=$RC"; exit 1; }
python -I -c "$SAME" "$O/file.json" "$O/cyr.json" || { echo "FAIL cyr differ"; exit 1; }
python -I -c "import sys; open(sys.argv[2],'wb').write(open(sys.argv[1],encoding='utf-8').read().encode('cp1251'))" "$T" "$O/cp1251.txt" || { echo "FAIL cp1251 prep"; exit 1; }
[ -s "$O/cp1251.txt" ] || { echo "FAIL cp1251 prep empty"; exit 1; }
RC=0; python -I "$S" "$O/cp1251.txt" --json > /dev/null 2> "$O/cp1251.err" || RC=$?
[ "$RC" -ne 0 ] || { echo "FAIL cp1251 accepted silently"; exit 1; }
grep -q UnicodeDecodeError "$O/cp1251.err" || { echo "FAIL cp1251 unexpected error"; cat "$O/cp1251.err"; exit 1; }
OUT="$(printf '' | python -I "$S" --json)"; RC=$?
[ "$RC" -eq 0 ] || { echo "FAIL empty rc=$RC"; exit 1; }
case "$OUT" in *'"words": 0'*) echo "PASS $O" ;; *) echo "FAIL empty"; exit 1 ;; esac
```

Expected: `FAIL json differ` (до исправления stdout уходит в cp1251, `json.load` не читает файл).

- [ ] **Step 4: Исправить `scan.py`**

Первые строки тела `main()`:

```python
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
```

В docstring после строки `python scan.py file.txt --json` добавить строку:
`stdin — UTF-8; в Windows PowerShell 5.1 передавай путь к файлу, а не pipe.`

- [ ] **Step 5: Проверка сканера — убедиться, что проходит**

Run: блок шага 3 в Git Bash → Expected: `PASS <каталог>`. Если падает только `FAIL sample` —
дописать текст в `docs/sample.txt` и повторить.

Run (PowerShell 7): записать блок во временный `check-pwsh.ps1` и запустить `pwsh -NoProfile -File <путь>`.
`$OutputEncoding` задаёт кодировку pipe в python — это и есть условие «stdin — UTF-8»;
`[Console]::OutputEncoding` — чтение вывода python обратно.

```powershell
Set-Location "C:/Users/T590/!all/code/my/tools/pishi"
$OutputEncoding = [Text.UTF8Encoding]::new(); [Console]::OutputEncoding = [Text.UTF8Encoding]::new()
$S = "skills/pishi-sokrashchai/scripts/scan.py"; $O = Join-Path ([IO.Path]::GetTempPath()) "pishi-pwsh"
New-Item -ItemType Directory -Force $O | Out-Null
python -I $S docs/sample.txt --json > "$O/file.json"; if ($LASTEXITCODE) { throw "file rc=$LASTEXITCODE" }
Get-Content -Raw -Encoding utf8 docs/sample.txt | python -I $S --json > "$O/pwsh.json"; if ($LASTEXITCODE) { throw "pipe rc=$LASTEXITCODE" }
python -I -c "import json,sys; d=[json.load(open(p,encoding='utf-8')) for p in sys.argv[1:]]; sys.exit(0 if all(x==d[0] for x in d) else 1)" "$O/file.json" "$O/pwsh.json"
if ($LASTEXITCODE) { throw "json differ" }; "PASS"
```

Expected: `PASS`.

- [ ] **Step 6: Правило сбоя сканера в SKILL.md**

В конец пункта `scripts/scan.py` (строка 120) дописать предложение:
`Если сканер не запустился или завершился ошибкой, продолжай без него и одной строкой упомяни это в ответе.`

Run:

```bash
R="/c/Users/T590/!all/code/my/tools/pishi"; cd "$R" || exit 1
diff <(unzip -p docs/pishi-sokrashchai.skill pishi-sokrashchai/SKILL.md) skills/pishi-sokrashchai/SKILL.md
diff <(unzip -p docs/pishi-sokrashchai.skill pishi-sokrashchai/scripts/scan.py) skills/pishi-sokrashchai/scripts/scan.py
if grep -n -i -E 'editor|redakt|субагент|claude code|codex|chatgpt' skills/pishi-sokrashchai/SKILL.md skills/pishi-sokrashchai/references/*.md; then echo "FAIL platform mention"; exit 1; fi
```

Expected: оба diff завершаются с кодом 1 (различия есть — это ожидаемо): первый — только строка 120;
второй — только строка docstring и две строки в `main()`. grep ничего не находит, сообщения `FAIL` нет.

- [ ] **Step 7: Коммит (по слову оператора)**

```bash
cd "/c/Users/T590/!all/code/my/tools/pishi" || exit 1
git add skills/ &&
git commit -m "feat: add pishi-sokrashchai skill with UTF-8 fix for scan.py"
```

---

### Task 2: Манифесты, агент, команда

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `agents/editor.md`, `commands/redakt.md`

**Interfaces:**
- Consumes: `skills/pishi-sokrashchai/SKILL.md`, `scripts/scan.py` (Task 1).
- Produces: плагин `pishi`, marketplace `pishi`, агент `pishi:editor`, команда `/pishi:redakt <путь>`.

- [ ] **Step 1: `.claude-plugin/plugin.json`**

Поля: `name: "pishi"`; `description` — одна фраза о редактуре по «Пиши, сокращай» (скилл, агент-редактор, `/pishi:redakt`);
`author: {"name": "Kirill Bogdanov", "email": "kirill.bogdanov@strela.digital"}`; `repository: "https://github.com/Kir-STR/pishi"`. Без `version`.

- [ ] **Step 2: `.claude-plugin/marketplace.json`**

Верхний уровень: `name: "pishi"`, `description`, `owner` (как `author` выше), `plugins`:
один элемент `{"name": "pishi", "source": "./", "description": …}`. Без `version`.

- [ ] **Step 3: `agents/editor.md`**

Frontmatter: `name: editor`; `description` — когда звать: разбор текстового файла по «Пиши, сокращай», правки
«фрагмент → проблема → замена» без изменения файла; `tools: Read, Grep, Glob, Bash`.

Тело — пять пунктов спеки дословно по смыслу, пути через `${CLAUDE_PLUGIN_ROOT}`:
1) первым шагом прочитать `${CLAUDE_PLUGIN_ROOT}/skills/pishi-sokrashchai/SKILL.md`, references — оттуда же, когда их требует SKILL.md;
2) прочитать файл из задания;
3) если SKILL.md предписывает сканер — `python "${CLAUDE_PLUGIN_ROOT}/skills/pishi-sokrashchai/scripts/scan.py" "<файл>"`,
   результат и сбой — по правилам SKILL.md;
4) режим B (разбор) из SKILL.md, правки в его формате «фрагмент» → проблема → замена;
5) файлы не создавать и не менять; Bash — только для `scan.py`.

- [ ] **Step 4: `commands/redakt.md`**

Frontmatter: `description` (разбор файла редактором по «Пиши, сокращай»), `argument-hint: <путь к файлу>`.
Тело: вызвать субагента `pishi:editor` на файле `$ARGUMENTS`; если аргумента нет — спросить путь и больше ничего не делать;
ответ агента показать как есть; в файл ничего не вносить, пока пользователь не попросит.

- [ ] **Step 5: Валидация**

Run: `cd "/c/Users/T590/!all/code/my/tools/pishi" && claude plugin validate .`
Expected: `✔ Validation passed with warnings`; до блока «Plugin directory checks» предупреждения только про `version`
и `CLAUDE.md at the plugin root`. Блок «Plugin directory checks» (LICENSE, иконка) — вне рамок.

- [ ] **Step 6: Коммит (по слову оператора)**

```bash
cd "/c/Users/T590/!all/code/my/tools/pishi" || exit 1
git add .claude-plugin/ agents/ commands/ &&
git commit -m "feat: add plugin manifests, editor agent and redakt command"
```

---

### Task 3: Сборка zip

**Files:**
- Create: `build.ps1`, `.gitignore`, `.gitattributes`

**Interfaces:**
- Consumes: `skills/pishi-sokrashchai/` (Task 1).
- Produces: `pwsh -NoProfile -File build.ps1` → `dist/pishi-sokrashchai.zip`, путь к архиву в stdout, код 0.

- [ ] **Step 1: `.gitattributes` и `.gitignore`**

`.gitattributes`: `* text=auto eol=lf`. `.gitignore`: `dist/`, `.claude/settings.local.json`, `__pycache__/`.

- [ ] **Step 2: `build.ps1`**

`#Requires -Version 7`; `$ErrorActionPreference = 'Stop'`; пути от `$PSScriptRoot`; создать `dist/`, удалить старый
`dist/pishi-sokrashchai.zip`, затем `[IO.Compression.ZipFile]::CreateFromDirectory(<skills/pishi-sokrashchai>, <zip>, 'Optimal', $true)`;
напечатать полный путь к архиву.

- [ ] **Step 3: Сборка и проверка архива (Review Focus 4)**

Run: `cd "/c/Users/T590/!all/code/my/tools/pishi" && pwsh -NoProfile -File build.ps1 && pwsh -NoProfile -File build.ps1` → Expected: оба запуска с кодом 0.

Проверка архива (Git Bash):

```bash
R="/c/Users/T590/!all/code/my/tools/pishi"; cd "$R" || exit 1
python -I -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); n=sorted(i.filename for i in z.infolist() if not i.is_dir()); p='pishi-sokrashchai/'; e=sorted([p+'SKILL.md',p+'scripts/scan.py']+[p+'references/'+f+'.md' for f in ('english','genres','stop-words','syntax')]); ok=n==e and not any(chr(92) in x for x in n) and not any(13 in z.read(x) for x in n); print(n); sys.exit(0 if ok else 1)" dist/pishi-sokrashchai.zip || { echo "FAIL zip"; exit 1; }
```

Expected: печатает 6 имён, код 0.

Run: `cd "/c/Users/T590/!all/code/my/tools/pishi" && git check-ignore dist/pishi-sokrashchai.zip .claude/settings.local.json`
Expected: обе строки напечатаны, код 0.

- [ ] **Step 4: Коммит (по слову оператора)**

```bash
cd "/c/Users/T590/!all/code/my/tools/pishi" || exit 1
git add build.ps1 .gitignore .gitattributes &&
git commit -m "build: add build.ps1 packaging the skill zip"
```

---

### Task 4: Установка и сквозные проверки

**Files:** нет изменений в репо. Меняются настройки Claude Code и `~/.codex` — разрешено оператором (спека, проверки 6 и 7).

**Interfaces:**
- Consumes: всё из Task 1–3, `docs/sample.txt`.

- [ ] **Step 1: Codex с изолированным `CODEX_HOME` (проверка 5 спеки)**

Run (Git Bash):

```bash
( R="/c/Users/T590/!all/code/my/tools/pishi"; export CODEX_HOME="$(mktemp -d)"
  codex plugin marketplace add "$R" && codex plugin add pishi@pishi || { echo "FAIL codex install"; exit 1; }
  codex debug prompt-input "t" > "$CODEX_HOME/prompt.json" 2>/dev/null || { echo "FAIL prompt-input"; exit 1; }
  grep -q 'pishi:pishi-sokrashchai' "$CODEX_HOME/prompt.json" || { echo "FAIL skill not listed"; exit 1; }
  echo PASS )
```

Подоболочка: `CODEX_HOME` не переживает блок.

Expected: `PASS` (предупреждение про PATH aliases во временном каталоге — норма).

- [ ] **Step 2: Установка в Claude Code**

Run (Git Bash, из родительского каталога):

```bash
cd "/c/Users/T590/!all/code/my/tools" || exit 1
claude plugin marketplace add ./pishi && claude plugin install pishi@pishi || { echo "FAIL install"; exit 1; }
claude plugin details pishi@pishi
```

Expected: в `details` есть скилл `pishi-sokrashchai`, агент `editor`, команда `redakt`.

- [ ] **Step 3: `/pishi:redakt` на тестовом тексте (проверка 6 спеки)**

Run (Git Bash, из родительского каталога):

```bash
R="/c/Users/T590/!all/code/my/tools/pishi"; cd "$R/.." || exit 1
LOG="$(mktemp)"; H1="$(sha256sum pishi/docs/sample.txt)" || { echo "FAIL hash before"; exit 1; }
RC=0; claude -p "/pishi:redakt pishi/docs/sample.txt" --allowedTools "Bash(python *)" > "$LOG" 2>&1 || RC=$?
H2="$(sha256sum pishi/docs/sample.txt)" || { echo "FAIL hash after"; exit 1; }
[ "$RC" -eq 0 ] || { echo "FAIL rc=$RC"; exit 1; }
[ "$H1" = "$H2" ] || { echo "FAIL file changed"; exit 1; }
N="$(grep -c '→' "$LOG" || true)"; [ "$N" -ge 3 ] || { echo "FAIL format, arrows=$N"; exit 1; }
echo "PASS $LOG"
```

Expected: `PASS`; глазами по `$LOG` — разбор в формате «фрагмент → проблема → замена».
Проверяются формат и неизменность файла (проверка 6 спеки); запуск сканера проверяется сквозным прогоном Codex (шаг 5).

- [ ] **Step 4: Review Focus 5 — команда без аргумента**

Run: `cd "/c/Users/T590/!all/code/my/tools" && claude -p "/pishi:redakt"`
Expected: ответ просит путь к файлу; разбора и правок нет. Вызовы инструментов не проверяются.

- [ ] **Step 5: Codex, сквозной прогон (проверка 7 спеки)**

Установка в настоящий `~/.codex` (без `CODEX_HOME`):

Сначала записать фильтр лога файлом `C:/Users/T590/AppData/Local/Temp/pishi-codex-check.py` (инструментом Write, по `windows-shell`). Затем:

```bash
R="/c/Users/T590/!all/code/my/tools/pishi"; CHECK="/c/Users/T590/AppData/Local/Temp/pishi-codex-check.py"
[ -f "$CHECK" ] || { echo "FAIL no filter"; exit 1; }
env -u CODEX_HOME codex plugin marketplace add "$R" && env -u CODEX_HOME codex plugin add pishi@pishi || { echo "FAIL codex install"; exit 1; }
E="$(mktemp -d)"; cp "$R/docs/sample.txt" "$E/sample.txt" || { echo "FAIL copy"; exit 1; }; echo "$E"
RC=0; env -u CODEX_HOME codex exec --json -s read-only --skip-git-repo-check -C "$E" "Разбери текст в файле sample.txt по принципам «Пиши, сокращай»: что не так и как исправить." > "$E/log.jsonl" || RC=$?
[ "$RC" -eq 0 ] || { echo "FAIL exec rc=$RC"; exit 1; }
python -I "$CHECK" "$E/log.jsonl" </dev/null || { echo "FAIL filter"; exit 1; }
```

`env -u` снимает `CODEX_HOME` только для этих команд — проверяется настоящий `~/.codex`.

Фильтр ищет на любой вложенности объекты со строковым `command` и печатает для каждого `command`, `exit_code` и начало вывода.
Код 1, если нет обоих: (а) команды чтения `stop-words.md` с `exit_code == 0`; (б) команды с `python`, `scan.py` и `sample.txt` с `exit_code == 0`.

Решение принимается глазами по напечатанным событиям: (а) — в выводе текст файла `stop-words.md`, а не `ls` или `echo`;
(б) — в выводе отчёт сканера («Слов: …» или JSON с `words`). Если Codex читает файлы событием другого типа,
поправить фильтр под фактический тип, сохранив оба условия.

Expected: фильтр завершается с кодом 0, оба условия подтверждены по выводу. При провале — сначала причина (путь, sandbox, настройка), исправление в рамках задачи;
если нужно менять требования или архитектуру — обсуждаем с оператором. SKILL.md вслепую не подгонять.

---

### Task 5: README, CLAUDE.md, описание для GitHub

**Files:**
- Modify: `README.md` (сейчас `# pishi`), `CLAUDE.md` (разделы «Где работает», «Проверка»)

**Interfaces:**
- Consumes: команды и статусы, подтверждённые в Task 4.

- [ ] **Step 1: README.md**

Разделы по спеке («Компоненты → README.md»): что это и как устроено, ограничения и оговорки (из `docs/idea.md`);
установка по платформам — команды для GitHub (`Kir-STR/pishi`) и локальной папки; десктопный ChatGPT отдельной строкой
со статусом «не проверено» и ссылкой на https://developers.openai.com/plugins/build/plugins; использование
(`/pishi:redakt <файл>` — агент предлагает правки, не применяя их); обновление после правки скилла по платформам —
заметным предупреждением, с пометкой, что команды для GitHub проверяются после публикации.

- [ ] **Step 2: Проверка README**

```bash
cd "/c/Users/T590/!all/code/my/tools/pishi" || exit 1
for s in '/pishi:redakt' 'codex plugin add pishi@pishi' 'reload-plugins' 'build.ps1' 'не проверено' 'не применяя'; do
  grep -q -F -- "$s" README.md || { echo "FAIL missing: $s"; exit 1; }
done
if grep -n -E '(^|[^:a-z])/redakt' README.md; then echo "FAIL short command name"; exit 1; fi
echo PASS
```

Expected: `PASS`.

- [ ] **Step 3: CLAUDE.md**

«Где работает»: убрать колонку «Как», добавить строку «Установка — в README.md» и «Codex читает `.claude-plugin/`, отдельный манифест не нужен».
«Проверка»: добавить `claude plugin validate .`; для Codex — `codex plugin add pishi@pishi` и `codex debug prompt-input`;
тестовый текст — `docs/sample.txt` (локально, не в git).

- [ ] **Step 4: Описание для GitHub «About»**

Подготовить одну строку описания и 5–8 topics, показать оператору. Применять `gh repo edit Kir-STR/pishi --description … --add-topic …`
только по его слову.

- [ ] **Step 5: Коммит (по слову оператора)**

```bash
cd "/c/Users/T590/!all/code/my/tools/pishi" || exit 1
git add README.md CLAUDE.md docs/superpowers/ &&
git commit -m "docs: add README, project CLAUDE.md, spec and plan"
```

---

### Task 6: Удаление материалов советника (по слову оператора)

**Files:**
- Delete: `docs/idea.md`, `docs/pishi-sokrashchai.skill` (не в git — безвозвратно)
- Modify: `CLAUDE.md` (строка `docs/` в «Структуре»)

- [ ] **Step 1: Спросить оператора; без «удаляй» задачу не выполнять.**

- [ ] **Step 2: Удалить и поправить CLAUDE.md**

Run: `cd "/c/Users/T590/!all/code/my/tools/pishi" && rm docs/idea.md docs/pishi-sokrashchai.skill && ls docs`
Expected: `sample.txt`, `superpowers`.

В «Структуре» CLAUDE.md строку `docs/ …` заменить на `docs/superpowers/   спеки и планы`.

- [ ] **Step 3: Коммит (по слову оператора)**

```bash
cd "/c/Users/T590/!all/code/my/tools/pishi" || exit 1
git add CLAUDE.md &&
git commit -m "docs: drop advisor materials reference"
```

---

## Ручные проверки оператора (мне недоступны)

- Загрузить `dist/pishi-sokrashchai.zip` в claude.ai (Customize → Skills) и в ChatGPT веб (Skills → Upload) и попросить разбор текста.
- Десктопный ChatGPT: установить плагин из Plugins Directory (Work или Codex) и попросить разбор. До этой проверки статус в README — «не проверено».
