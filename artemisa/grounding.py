"""Grounding check for AI recaps: does the recap only use facts from its input?

The recap prompt tells Claude to use only the standings it is given. This checks that
deterministically, from the exact text Claude received (`recap.recap_input`):

- every number in the recap must be a fact from the standings (a score, a 10s or Xs
  count, the size of a category) or a gap between two archers of the same category
  (e.g. "won by 13 points");
- every capitalized two-word name ("Juan Gómez") must end in a word that appears in an
  archer, category or competition name.

It is deliberately simple and strict: a flagged recap is worth a human look, and the
numbers rule catches the most damaging mistake (an invented score). Numbers written as
words ("one point") and claims like "most Xs of the day" are not checked.
"""
import re
from itertools import combinations

LINE = re.compile(r"^(?P<category>[^:\n]+): (?P<archers>.+)$", re.MULTILINE)
ARCHER = re.compile(r"(?P<name>[^,()]+?) \((?P<score>\d+) pts, (?P<tens>\d+) tens, (?P<xs>\d+) Xs\)")
NUMBER = re.compile(r"(?<![\w.])\d+(?![\w.]*\d)")
WORD = r"[^\W\d_][\w'’-]*"
CAPITALIZED_PAIR = re.compile(rf"\b({WORD})\s+({WORD})")


def parse_input(prompt_input):
    """{category: [{'name', 'score', 'tens', 'xs'}, ...]} plus the competition name."""
    competition = prompt_input.split("\n", 1)[0].removeprefix("Competition: ").strip()
    categories = {}
    for line in LINE.finditer(prompt_input):
        if line["category"] in ("Competition", "Final standings by category"):
            continue
        categories[line["category"]] = [
            {"name": m["name"].strip(), "score": int(m["score"]), "tens": int(m["tens"]), "xs": int(m["xs"])}
            for m in ARCHER.finditer(line["archers"])
        ]
    return competition, categories


def allowed_numbers(categories):
    numbers = set()
    for archers in categories.values():
        numbers.add(len(archers))
        for archer in archers:
            numbers.update((archer["score"], archer["tens"], archer["xs"]))
        for a, b in combinations(archers, 2):  # margins between archers in a category
            for key in ("score", "tens", "xs"):
                numbers.add(abs(a[key] - b[key]))
    numbers.add(len(categories))
    numbers.add(sum(len(archers) for archers in categories.values()))
    return numbers


def grounding_issues(recap_text, prompt_input):
    """List of problems found; an empty list means the recap passed."""
    competition, categories = parse_input(prompt_input)
    issues = []

    numbers = allowed_numbers(categories)
    numbers.update(int(n) for n in NUMBER.findall(competition))
    for found in NUMBER.findall(recap_text):
        if int(found) not in numbers:
            issues.append(f"number not in the standings: {found}")

    vocabulary = {
        word.lower()
        for phrase in [competition, *categories, *(a["name"] for archers in categories.values() for a in archers)]
        for word in re.findall(WORD, phrase)
    }
    for first, second in CAPITALIZED_PAIR.findall(recap_text):
        if first[0].isupper() and second[0].isupper():
            word = re.sub(r"['’]s$", "", second).lower()
            if word not in vocabulary:
                issues.append(f"name not in the standings: {first} {second}")

    return issues
