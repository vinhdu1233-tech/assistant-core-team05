import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from assistant_core.errors import DataError


@dataclass(frozen=True)
class Office:
    name: str
    room: str
    hours: str


class OfficeDirectory:
    def __init__(self, offices: list[Office]):
        self._offices = offices

    @classmethod
    def from_csv(cls, path: Path) -> "OfficeDirectory":
        try:
            with path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)

                required = {"name", "room", "hours"}
                if not required.issubset(set(reader.fieldnames or [])):
                    raise DataError("Office CSV must contain name, room, hours columns.")

                offices = []
                for row in reader:
                    name = (row.get("name") or "").strip()
                    room = (row.get("room") or "").strip()
                    hours = (row.get("hours") or "").strip()

                    if not name or not room or not hours:
                        raise DataError("Office CSV contains an incomplete row.")

                    offices.append(Office(name, room, hours))

                return cls(offices)

        except DataError:
            raise
        except (OSError, UnicodeError, csv.Error) as exc:
            raise DataError(f"Cannot read office CSV: {path}") from exc

    @property
    def names(self) -> set[str]:
        return {office.name for office in self._offices}

    def find(self, text: str) -> Office | None:
        query = text.casefold()

        for office in self._offices:
            if office.name.casefold() in query:
                return office

        return None


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    text: str


class Handbook:
    def __init__(self, rules: list[Rule]):
        self._rules = rules

    @classmethod
    def from_json(cls, path: Path) -> "Handbook":
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise DataError("Handbook JSON must contain a list of rules.")

            rules = []
            for item in data:
                if not isinstance(item, dict):
                    raise DataError("Each handbook rule must be an object.")

                rule_id = item.get("id")
                title = item.get("title")
                text = item.get("text")

                if not all(isinstance(value, str) and value.strip() for value in (rule_id, title, text)):
                    raise DataError("Each rule must have non-empty id, title and text.")

                rules.append(
                    Rule(
                        id=rule_id.strip(),
                        title=title.strip(),
                        text=text.strip(),
                    )
                )

            return cls(rules)

        except DataError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DataError(f"Cannot read handbook JSON: {path}") from exc

    def search(self, query: str) -> Rule | None:
        def keywords(text: str) -> set[str]:
            return {word for word in re.findall(r"[a-z0-9]+", text.casefold()) if len(word) > 3}

        query_words = keywords(query)

        if not query_words:
            return None

        best_rule = None
        best_score = 0

        for rule in self._rules:
            searchable_text = f"{rule.title} {rule.text}"
            rule_words = keywords(searchable_text)
            score = len(query_words & rule_words)

            if score > best_score:
                best_score = score
                best_rule = rule

        return best_rule
