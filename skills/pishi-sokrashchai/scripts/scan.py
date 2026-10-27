#!/usr/bin/env python3
"""
Сканер кандидатов в стоп-слова для русского текста.

Использование:
    python scan.py file.txt
    cat file.txt | python scan.py
    python scan.py file.txt --json
stdin — UTF-8; в Windows PowerShell 5.1 передавай путь к файлу, а не pipe.

Ищет: стоп-слова по категориям, длинные предложения, пассив,
скопления отглагольных существительных. Результат — подсказка для
редактора, а не вердикт: каждое срабатывание проверяется по смыслу.
"""

import json
import re
import sys

# Шаблоны по категориям. \b в Python 3 работает с кириллицей.
W = r"\w*"
CATEGORIES = {
    "вводные": [
        r"как известно", r"стоит отметить", r"следует (?:отметить|сказать|подчеркнуть)",
        r"необходимо (?:отметить|подчеркнуть)", r"важно (?:понимать|отметить)",
        r"по сути", r"на самом деле", r"в принципе", r"так сказать",
        r"безусловно", r"разумеется", r"естественно", r"собственно",
        r"в целом", r"как правило",
    ],
    "усилители": [
        r"очень", r"крайне", r"максимально", r"абсолютно", r"совершенно",
        r"действительно", r"чрезвычайно", r"невероятно", r"колоссальн" + W,
        r"по-настоящему",
    ],
    "оценки": [
        r"качественн" + W, r"эффективн" + W, r"уникальн" + W, r"лучш(?:ий|ая|ее|ие|их|им|ими|ей|ую|его|ему)",
        r"надёжн" + W, r"надежн" + W, r"профессиональн" + W, r"удобн" + W,
        r"выгодн" + W, r"инновационн" + W, r"современн" + W, r"прекрасн" + W,
        r"отличн(?:ый|ая|ое|ые|ого|ой|ому|ым|ыми|ых|ую)", r"комфортн" + W, r"премиальн" + W,
    ],
    "штампы": [
        r"индивидуальн\w* подход\w*", r"команд\w* профессионал\w*",
        r"широк\w* ассортимент\w*", r"динамично развива\w*",
        r"в кратчайшие сроки", r"на высшем уровне", r"залог\w* успеха",
        r"под ключ", r"комплексн\w* подход\w*", r"лидер\w* рынка",
        r"доступн\w* цен\w*", r"гибк\w* систем\w* скидок",
    ],
    "канцелярит": [
        r"осуществл" + W, r"явля(?:ется|ются|лся|лась|лось|лись|ясь)",
        r"данн(?:ый|ая|ое|ого|ой|ому|ую)",
        r"в целях", r"в рамках", r"в связи с", r"в части", r"на предмет",
        r"по вопросу", r"вышеуказанн" + W, r"имеет место", r"вследствие",
        r"в случае(?: если)?", r"при наличии", r"посредством",
        r"в соответствии с", r"с целью", r"ввиду",
        r"производ(?:ит|ят|ится|ятся)", r"предоставлени" + W, r"обеспечени" + W,
    ],
    "неопределённость": [
        r"некотор" + W, r"\bряд\b", r"определённ" + W, r"различн" + W,
        r"разнообразн" + W, r"множеств" + W, r"некий", r"некая", r"некое",
        r"и т\. ?д\.", r"и др\.", r"и прочее", r"в ряде случаев",
    ],
    "обобщения": [
        r"всегда", r"никогда", r"любой", r"любая", r"любое", r"любых", r"никто",
    ],
    "время": [
        r"в настоящее время", r"на сегодняшний день", r"в данный момент",
        r"на текущий момент", r"на данном этапе", r"в ближайшее время",
        r"в скором времени", r"своевременн" + W,
    ],
    "модальность": [
        r"позволя(?:ет|ют|ющ\w*)", r"способству" + W, r"да[её]т возможность",
        r"стара(?:емся|ется|ются)", r"стрем(?:имся|ится|ятся)", r"призван" + W,
        r"необходимо", r"следует",
    ],
    "местоимения": [
        r"наш(?:и|их|им|ими|его|ему|ей|у|а|е)?", r"сво(?:й|я|ё|е|и|их|им|ими|его|ему|ей|ю)",
    ],
    "эвфемизмы": [
        r"оптимизаци\w* (?:штата|расходов|персонала)", r"корректировк\w* (?:цен|тариф)\w*",
        r"непредвиденн\w* обстоятельств\w*", r"временн\w* трудност\w*",
        r"отрицательн\w* динамик\w*",
    ],
}

COMPILED = {
    cat: [re.compile(r"(?<!\w)(?:" + p + r")(?!\w)", re.IGNORECASE) for p in pats]
    for cat, pats in CATEGORIES.items()
}

PASSIVE = re.compile(
    r"(?<!\w)(?:был[аои]?|будет|будут)\s+\w+(?:ан|ен|ён|ят|ит)[аоы]?(?!\w)", re.IGNORECASE
)
PASSIVE_SJA = re.compile(r"(?<!\w)\w+(?:ется|ются|ится|ятся)(?!\w)", re.IGNORECASE)
NOMINAL = re.compile(r"(?<!\w)\w{4,}(?:ание|ение|ация|ании|ении|ации|ания|ения|ации)(?!\w)", re.IGNORECASE)
WORD = re.compile(r"\w+", re.UNICODE)

LONG_SENTENCE = 25


def split_sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]


def scan(text):
    words_total = len(WORD.findall(text))
    hits = {cat: [] for cat in COMPILED}
    for cat, regs in COMPILED.items():
        for rx in regs:
            for m in rx.finditer(text):
                hits[cat].append(m.group(0).lower())

    sentences = split_sentences(text)
    long_sents, passive_sents, nominal_sents = [], [], []
    for s in sentences:
        n = len(WORD.findall(s))
        if n > LONG_SENTENCE:
            long_sents.append({"words": n, "text": s[:160] + ("…" if len(s) > 160 else "")})
        if PASSIVE.search(s):
            passive_sents.append(s[:160])
        noms = NOMINAL.findall(s)
        if len(noms) >= 2:
            nominal_sents.append({"nouns": noms, "text": s[:160]})

    stop_total = sum(len(v) for v in hits.values())
    return {
        "words": words_total,
        "sentences": len(sentences),
        "stop_candidates": stop_total,
        "stop_density_pct": round(100 * stop_total / words_total, 1) if words_total else 0,
        "by_category": {k: sorted(set(v), key=v.index) for k, v in hits.items() if v},
        "counts": {k: len(v) for k, v in hits.items() if v},
        "long_sentences": long_sents,
        "passive": passive_sents,
        "nominal_clusters": nominal_sents,
        "sja_forms": len(PASSIVE_SJA.findall(text)),
    }


def print_report(r):
    print(f"Слов: {r['words']}, предложений: {r['sentences']}")
    print(f"Кандидатов в стоп-слова: {r['stop_candidates']} ({r['stop_density_pct']}% слов)")
    print()
    if r["by_category"]:
        print("По категориям:")
        for cat, words in r["by_category"].items():
            print(f"  {cat} ({r['counts'][cat]}): {', '.join(words)}")
        print()
    if r["long_sentences"]:
        print(f"Длинные предложения (>{LONG_SENTENCE} слов): {len(r['long_sentences'])}")
        for s in r["long_sentences"]:
            print(f"  [{s['words']}] {s['text']}")
        print()
    if r["passive"]:
        print(f"Пассив (был/будет + причастие): {len(r['passive'])}")
        for s in r["passive"]:
            print(f"  {s}")
        print()
    if r["nominal_clusters"]:
        print(f"Скопления отглагольных существительных: {len(r['nominal_clusters'])}")
        for s in r["nominal_clusters"]:
            print(f"  [{', '.join(s['nouns'])}] {s['text']}")
        print()
    print(f"Форм на -ся (возможный пассив, проверить): {r['sja_forms']}")
    print("\nЭто подсказки: проверь каждое срабатывание по смыслу.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if args:
        with open(args[0], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    result = scan(text)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()
