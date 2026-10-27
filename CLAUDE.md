# pishi

Плагин для редактуры текстов по книге «Пиши, сокращай» (Ильяхов, Сарычева).
Правила живут в одном скилле; из него ставится в Claude Code, claude.ai, ChatGPT и Codex.

## Структура

```
.claude-plugin/plugin.json       манифест плагина
.claude-plugin/marketplace.json  marketplace из одного плагина
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
| claude.ai | скилл (zip из `build.ps1`) |
| ChatGPT веб/мобильный | скилл (тот же zip) |
| Codex CLI | скилл из плагина |
| ChatGPT десктоп (не проверено) | скилл из плагина |

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
- После правки скилла платформы обновляются по-разному:
  - Claude Code с локальным marketplace читает репо напрямую — новая сессия или `/reload-plugins`;
  - Codex копирует плагин при установке — повторить `codex plugin add pishi@pishi`
    (для GitHub-marketplace перед этим `codex plugin marketplace upgrade pishi`);
  - claude.ai и ChatGPT веб — запустить `build.ps1` и перезалить zip;
  - ChatGPT десктоп — способ обновления не проверен.

## Проверка

Тестовый текст — `docs/sample.txt` (локально, не в git).

- `python skills/pishi/scripts/scan.py <файл> --json` и то же через pipe: одинаковый JSON, код 0.
- `claude plugin validate .`: passed; предупреждения только про `version` и `CLAUDE.md`.
- `pwsh ./build.ps1`: в zip одна папка `pishi/` с SKILL.md внутри, имена через `/`.
- Claude Code: `/plugin marketplace add ./pishi` из родительского каталога → установка → `/pishi:redakt <тестовый файл>`.
- Codex: `codex plugin marketplace add <путь к репо>` → `codex plugin add pishi@pishi` →
  в `codex debug prompt-input` есть `pishi:pishi`.
