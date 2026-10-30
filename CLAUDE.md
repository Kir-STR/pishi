# pishi

Плагин для редактуры текстов по книге «Пиши, сокращай» (Ильяхов, Сарычева).
Правила живут в одном скилле; из него ставится в Claude Code, claude.ai, ChatGPT и Codex.

## Структура

```
.claude-plugin/plugin.json       манифест плагина
.claude-plugin/marketplace.json  marketplace из одного плагина
.claude-plugin/icon.png          иконка листинга в каталоге плагинов Anthropic
skills/pishi/        единственная копия правил: SKILL.md, references/, scripts/scan.py
agents/editor.md                 субагент-редактор, только Claude Code
commands/redakt.md               /pishi:redakt <путь>, только Claude Code
build.ps1                        zip скилла → dist/pishi.zip (dist/ в .gitignore)
README.md                        описание репо и установка для людей
LICENSE                          MIT
docs/superpowers/                спеки и планы
```

## Где работает

| Платформа | Что ставится |
|---|---|
| Claude Code | плагин целиком |
| Claudian (Obsidian) | плагин из Claude Code (`~/.claude/plugins`) |
| claude.ai | скилл (zip из `build.ps1`) |
| ChatGPT веб/мобильный | скилл (тот же zip) |
| Codex CLI | скилл из плагина |
| ChatGPT десктоп | скилл из плагина |

Установка — в README.md. Codex читает `.claude-plugin/`, отдельный манифест не нужен.
Агент и команда есть только в Claude Code. Для других платформ обёрток не пишем: они читают SKILL.md напрямую.

## Правила

- Зависимость в одну сторону: агент и команда ссылаются на скилл. SKILL.md и references/ не упоминают
  агента, команду и конкретные платформы — тот же текст читают Claude, ChatGPT и Codex.
- Правила редактуры — только в `skills/pishi/`. Агент и команда их не пересказывают, а отсылают к SKILL.md.
- Frontmatter SKILL.md — только `name` и `description` (формат Agent Skills, общий для платформ; description ≤ 1024 символов).
- `scan.py` — только стандартная библиотека Python 3; stdin и stdout — UTF-8 независимо от кодировки консоли
  (Windows PowerShell 5.1 передаёт pipe не в UTF-8 — там передавать путь к файлу).
- Не держать копию скилла в `~/.claude/skills/` или `~/.codex/skills/` — платформа увидит два одинаковых скилла.
  Скилл, загруженный в claude.ai, Claude Code подтягивает как `anthropic-skills:pishi`; отключается
  `"skillOverrides": {"anthropic-skills:pishi": "off"}` в `~/.claude/settings.json` — ключ с полным именем:
  короткий `"pishi"` совпадает с именем скилла плагина и копию из claude.ai не отключает (проверено).
- После правки скилла платформы обновляются по-разному:
  - Claude Code с локальным marketplace читает репо напрямую — новая сессия или `/reload-plugins`;
  - Codex копирует плагин при установке — повторить `codex plugin add pishi@pishi`
    (для GitHub-marketplace перед этим `codex plugin marketplace upgrade pishi`);
  - claude.ai и ChatGPT — выпустить релиз (ниже) и перезалить zip;
  - ChatGPT десктоп — способ обновления не проверен.
- Готовый zip раздаётся через GitHub Releases, не через git: README ссылается на
  `releases/latest/download/pishi.zip`. Релиз — по слову пользователя, после push в `main`:
  `pwsh ./build.ps1`, затем `gh release create vГГГГ.ММ.ДД dist/pishi.zip --target <sha>`.
- Каталог плагинов Anthropic (claude.ai, Cowork, Claude Code) берёт версии из подвижного тега `stable`,
  а не из `main`. Выпуск в каталог — тоже по слову пользователя: `git tag -f stable <sha>`, `git push -f origin stable`.
  Подаёт пользователь из личного аккаунта claude.ai (Pro). Иконку `.claude-plugin/icon.png` портал берёт
  один раз, при первом сохранении; позже её не сменить.

## Проверка

Тестовый текст — `docs/sample.txt` (локально, не в git).

- `python skills/pishi/scripts/scan.py <файл> --json` и то же через pipe: одинаковый JSON, код 0.
- `claude plugin validate .`: passed; предупреждения только про `version` и `CLAUDE.md`.
- `pwsh ./build.ps1`: в zip одна папка `pishi/` с SKILL.md внутри, имена через `/`.
- Claude Code: `/plugin marketplace add ./pishi` из родительского каталога → установка → `/pishi:redakt <тестовый файл>`.
- Codex: `codex plugin marketplace add <путь к репо>` → `codex plugin add pishi@pishi` →
  в `codex debug prompt-input` есть `pishi:pishi`.
