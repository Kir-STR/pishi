# Плагин pishi: дизайн

Дата: 2026-10-27. Основа: ТЗ советника (передано в чате), `docs/idea.md`, `CLAUDE.md` проекта.

## Цель

Собрать из архива `docs/pishi-sokrashchai.skill` репо-плагин с одним источником правил — `skills/pishi-sokrashchai/`.
Из него ставится: Claude Code — скилл, агент и команда; claude.ai и ChatGPT веб — zip скилла;
Codex CLI — скилл из того же плагина. Десктопный ChatGPT — тот же плагин по документации OpenAI, не проверено.

Готово, когда:

- `claude plugin validate .` проходит; плагин ставится в Claude Code из локального marketplace;
  `/pishi:redakt <файл>` возвращает правки «фрагмент → проблема → замена», файл не меняется.
- Codex CLI ставит плагин из того же репо и на просьбе о разборе выполняет скилл:
  читает `references/stop-words.md`, `scan.py` завершается с кодом 0.
- `build.ps1` собирает один zip для загрузки в claude.ai и ChatGPT.
- `scan.py` даёт одинаковый `--json` на файле и на stdin в UTF-8.
- `README.md` описывает плагин и установку на каждой платформе.

## Проверено на стенде до спеки

- **Плагин в корне репо** (`"source": "./"`). `claude plugin validate` (Claude Code 2.1.311): passed with warnings —
  нет `version`; `CLAUDE.md` в корне плагина не грузится как контекст. Оба предупреждения принимаем.
- **Codex CLI 0.163.0** с изолированным `CODEX_HOME`: `codex plugin marketplace add` читает `.claude-plugin/marketplace.json`,
  `codex plugin add pishi@pishi` ставит плагин, `codex debug prompt-input` показывает скилл `pishi:pishi-sokrashchai`
  с целой кириллицей в описании. Агента и команду Codex не загружает. Отдельный манифест для Codex не нужен.
- **Codex копирует плагин при установке** в `$CODEX_HOME/plugins/cache/pishi/pishi/local`. Правка скилла в репо
  не видна, пока не выполнить `codex plugin add pishi@pishi` повторно (удалять перед этим не нужно) — проверено маркером в description.
- **Claude Code с marketplace из локальной папки** грузит плагин на месте, без копии: правки видны в новой сессии
  или после `/reload-plugins` (документация, plugins/loading). Из GitHub-marketplace Claude Code копирует плагин в кеш.
- **scan.py на Windows** (Python 3.14, кодировка по умолчанию cp1251). Вывод в pipe — кракозябры.
  Ввод через pipe читается как cp1251, и сканер ошибается молча: на тестовом тексте 43 слова вместо 15, 0 кандидатов вместо 8.
  Правка только stdout второй случай не лечит; с `stdin.reconfigure` файл и pipe из Git Bash дают 15 слов и 8 кандидатов.
- **Pipe из PowerShell.** PowerShell 7.6 (`$OutputEncoding` = utf-8): 15 слов и 8 кандидатов.
  Windows PowerShell 5.1 (`$OutputEncoding` = us-ascii): 0 слов — кириллица теряется до Python, правкой в scan.py это не лечится.
- **Относительные пути в Codex.** Системный промпт Codex: «Resolve relative paths against the directory containing
  a filesystem-backed `SKILL.md`». Поэтому `scripts/scan.py` и `references/…` в SKILL.md заранее не меняем.
- **`${CLAUDE_PLUGIN_ROOT}`** по документации Claude Code подставляется в Markdown агента и команды;
  в окружении Bash этой переменной нет, поэтому путь пишется прямо в тексте.

## Расхождения с ТЗ советника

| ТЗ | Решение | Почему |
|---|---|---|
| scan.py: только `sys.stdout.reconfigure` | плюс `sys.stdin.reconfigure(encoding="utf-8")` | стенд: ввод через pipe даёт неверный результат без ошибки |
| build.ps1 пакует `.skill` для claude.ai | пакует `dist/pishi-sokrashchai.zip` | один файл для claude.ai и ChatGPT: оба принимают `.zip`, про `.skill` в ChatGPT данных нет |
| «в чатах плагинов нет, только скилл» | Codex CLI ставит этот же плагин; десктопный ChatGPT — ожидаемо, не проверено | Codex CLI — стенд; десктоп — [OpenAI: plugins](https://developers.openai.com/plugins/build/plugins): «Local marketplaces appear in the Plugins Directory in Work mode or Codex in the ChatGPT desktop app» |
| SKILL.md без изменений | одно предложение: при ошибке сканера продолжать без него | правило нужно на всех платформах, а агент Claude Code — только одна из них |
| editor «только для чтения», но с Bash | Bash оставляем, запрет правок — инструкцией в агенте | Bash по команде не ограничить; риск принят |

## Структура

```
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
skills/pishi-sokrashchai/   SKILL.md, references/ (4 файла), scripts/scan.py
agents/editor.md
commands/redakt.md
build.ps1                   → dist/pishi-sokrashchai.zip
README.md
CLAUDE.md
.gitignore, .gitattributes
docs/superpowers/           спеки и планы
```

## Компоненты

### skills/pishi-sokrashchai/

Распаковка архива с двумя правками.

- `scan.py`: в начале `main()` две строки — `sys.stdout.reconfigure(encoding="utf-8")` и `sys.stdin.reconfigure(encoding="utf-8")`;
  в docstring одна строка контракта: «stdin — UTF-8; в Windows PowerShell 5.1 передавай путь к файлу, а не pipe».
- SKILL.md: в описание `scripts/scan.py` в разделе «Ресурсы» добавить одно предложение —
  «Если сканер не запустился или завершился ошибкой, продолжай без него и одной строкой упомяни это в ответе».
  Агента, команду и платформы SKILL.md не упоминает; frontmatter не меняется — только `name` и `description` (788 символов).

### .claude-plugin/plugin.json

`name: "pishi"`, `description`, `author` (`name`, `email`), `repository: "https://github.com/Kir-STR/pishi"`.
Без `version`: по документации Claude Code заданная версия держит пользователей на ней до смены,
а без неё версией для GitHub-источника служит SHA коммита («To let users track commits instead, leave `version` out») —
не нужно помнить о ручном повышении.

### .claude-plugin/marketplace.json

`name: "pishi"`, `owner`, `description`, один плагин: `name: "pishi"`, `source: "./"`, `description`.

### agents/editor.md

Frontmatter: `name: editor`; `description` — разбор текстового файла по «Пиши, сокращай», правки без изменения файла;
`tools: Read, Grep, Glob, Bash`.

Тело не пересказывает правила, а отсылает к скиллу:

1. Первым шагом прочитать `${CLAUDE_PLUGIN_ROOT}/skills/pishi-sokrashchai/SKILL.md`;
   references читать оттуда же, когда их требует SKILL.md.
2. Прочитать файл из задания.
3. Если SKILL.md предписывает сканер, запустить
   `python "${CLAUDE_PLUGIN_ROOT}/skills/pishi-sokrashchai/scripts/scan.py" "<файл>"`; результат и сбой сканера —
   по правилам SKILL.md, агент их не повторяет.
4. Работать в режиме B (разбор) из SKILL.md и вернуть правки в его формате: «фрагмент» → проблема → замена.
5. Файлы не создавать и не менять; Bash — только для `scan.py`.

### commands/redakt.md

Frontmatter: `description`, `argument-hint: <путь к файлу>`.
Тело: вызвать субагента `pishi:editor` на файле `$ARGUMENTS`; без аргумента — спросить путь;
ответ агента показать как есть; в файл ничего не вносить, пока пользователь не попросит.

Команда остаётся в `commands/`, а не в `skills/`: всё из `skills/` видят Codex и ChatGPT, а команда нужна только в Claude Code.

### build.ps1

PowerShell 7 (`#Requires -Version 7`). Пересоздаёт `dist/pishi-sokrashchai.zip` из `skills/pishi-sokrashchai/`
с корневой папкой `pishi-sokrashchai/` (`[IO.Compression.ZipFile]::CreateFromDirectory` с `includeBaseDirectory`),
печатает путь к архиву, при ошибке завершается с ненулевым кодом.
Ограничение на PowerShell 7 — потому что `Compress-Archive` в Windows PowerShell 5.1 может записать пути с `\`,
которые ломают распаковку вне Windows; проверка ниже ловит это независимо от версии.

### README.md

Для людей, не для агента:

- что это и как устроено — из раздела «Как устроен» в `docs/idea.md`;
- ограничения и оговорки — из одноимённых разделов `idea.md`;
- установка по платформам — таблица и команды (единственное место с инструкцией по установке для пользователя;
  в CLAUDE.md остаются только команды проверки);
- использование: `/pishi:redakt <файл>` в Claude Code — агент предлагает правки, не применяя их;
  на остальных платформах — просьба отредактировать или разобрать текст, скилл подхватывается по описанию;
- десктопный ChatGPT (режим Work или Codex) — отдельной строкой со статусом «не проверено» и шагами из
  [OpenAI: plugins](https://developers.openai.com/plugins/build/plugins): добавить marketplace, перезапустить приложение,
  установить из Plugins Directory;
- обновление после правки скилла — заметным предупреждением, потому что платформы ведут себя по-разному:
  - Claude Code, marketplace из локальной папки: новая сессия или `/reload-plugins`;
  - Claude Code, marketplace из GitHub: `claude plugin update pishi@pishi`, затем `/reload-plugins`;
  - Codex CLI: плагин копируется при установке — повторить `codex plugin add pishi@pishi`,
    для GitHub-marketplace перед этим `codex plugin marketplace upgrade pishi`;
  - десктопный ChatGPT: способ обновления в документации не описан — не проверено;
  - claude.ai и ChatGPT веб: `build.ps1` и перезалить zip.

  Команды для GitHub-варианта взяты из документации и `--help`; проверяются после публикации репо.

Описание для GitHub «About» (одна строка и topics) готовится вместе с README.
Ставится через `gh repo edit` только по отдельному слову пользователя.

### Служебные файлы

- `.gitignore`: `dist/`, `.claude/settings.local.json`, `__pycache__/`.
- `.gitattributes`: `* text=auto eol=lf`. В репо `core.autocrlf=true`; без этого файлы в zip из свежего клона получат CRLF.

### Правки CLAUDE.md

- «Где работает»: убрать колонку «Как», добавить «Установка — в README.md»
  и строку «Codex читает `.claude-plugin/`, отдельный манифест не нужен».
- Строку `docs/` заменить на `docs/superpowers/  спеки и планы`.
- «Проверка»: добавить `claude plugin validate .`; для Codex — `codex plugin add pishi@pishi` и `codex debug prompt-input`.

### Удаление материалов советника

Последний шаг, после README и всех проверок: удалить `docs/idea.md` и `docs/pishi-sokrashchai.skill`.
Их нет в git, удаление безвозвратно; к этому моменту содержимое перенесено в `skills/`, README и CLAUDE.md.
Выполняется только по слову пользователя.

## Проверка

Тестовый текст — `docs/sample.txt`: около 2500 знаков делового текста с типичными стоп-словами.
Не часть плагина и хранится только локально (решение оператора). Свежий клон не содержит данных
для повторения проверок 1, 6 и 7 на том же входе.

Выполняю сам:

1. `scan.py` на `docs/sample.txt`: полный `--json` при чтении файла и stdin совпадает, оба запуска завершаются с кодом 0.
   Pipe — из Git Bash и PowerShell 7; точные команды — в плане. Один раз — то же для копии файла по пути с пробелами и кириллицей.
2. `claude plugin validate .` — passed; допустимы только предупреждения про `version` и `CLAUDE.md`.
   Блок «plugin directory checks» (LICENSE, иконка) на результат не влияет и относится к публикации в каталог — вне рамок.
3. `pwsh ./build.ps1` — в zip ровно 6 файлов под `pishi-sokrashchai/`, имена записей через `/`.
4. В SKILL.md и references нет `editor`, `redakt`, `субагент`, `Claude Code`, `Codex`, `ChatGPT`.
5. Codex с изолированным `CODEX_HOME`: `marketplace add`, `plugin add`, в `debug prompt-input` есть `pishi:pishi-sokrashchai`.
6. Claude Code: из родительского каталога `/plugin marketplace add ./pishi`, `/plugin install pishi@pishi`
   (меняет твои настройки Claude Code — это и есть целевая установка), затем в той же сессии `/pishi:redakt pishi/docs/sample.txt`:
   ответ в формате «фрагмент → проблема → замена», хеш файла до и после совпадает (быстрая проверка, не доказательство запрета записи).
7. Codex CLI, сквозной прогон: плагин ставится в настоящий `~/.codex` (разрешено оператором); `codex exec --json`
   из каталога вне репо с просьбой разобрать копию `docs/sample.txt`. В логе: прочитан `references/stop-words.md`,
   `scan.py` завершился с кодом 0. Если нет — сначала устанавливаю причину. Ошибку пути или настройки исправляю
в рамках задачи; если исправление требует менять требования или архитектуру — обсуждаем. SKILL.md вслепую не подгоняю.

Выполняет пользователь (мне недоступно): загрузка zip в claude.ai и ChatGPT; установка плагина в десктопном ChatGPT.

## Вне рамок

LICENSE и иконка (нужны для публикации в каталог Anthropic; лицензию выбирает автор), Cowork и Claudian,
аналог агента и команды для Codex, корневой `plugin.json` в формате OpenAI, публикация в каталоги плагинов.
