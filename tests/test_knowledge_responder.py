import json

import pytest

from assistant_core.errors import DataError, ProviderError
from assistant_core.knowledge import (
    Handbook,
    OfficeDirectory,
    Rule,
)
from assistant_core.responder import (
    StubLLMResponder,
    TemplateResponder,
)


def test_office_lookup(tmp_path):
    path = tmp_path / "offices.csv"
    path.write_text(
        "name,room,hours\nLibrary,B.201,Mon-Sat 07:00-20:00\n",
        encoding="utf-8",
    )

    directory = OfficeDirectory.from_csv(path)
    office = directory.find("Where is the library?")

    assert office is not None
    assert office.room == "B.201"
    assert "Library" in directory.names


def test_office_not_found(tmp_path):
    path = tmp_path / "offices.csv"
    path.write_text(
        "name,room,hours\nLibrary,B.201,Mon-Sat 07:00-20:00\n",
        encoding="utf-8",
    )

    directory = OfficeDirectory.from_csv(path)

    assert directory.find("Where is the cafeteria?") is None


def test_office_missing_column(tmp_path):
    path = tmp_path / "offices.csv"
    path.write_text("name,room\nLibrary,B.201\n", encoding="utf-8")

    with pytest.raises(DataError):
        OfficeDirectory.from_csv(path)


def test_office_incomplete_row(tmp_path):
    path = tmp_path / "offices.csv"
    path.write_text(
        "name,room,hours\nLibrary,B.201,\n",
        encoding="utf-8",
    )

    with pytest.raises(DataError):
        OfficeDirectory.from_csv(path)


def test_handbook_search(tmp_path):
    path = tmp_path / "handbook.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "H1",
                    "title": "Thesis registration",
                    "text": "Students need 120 credits.",
                },
                {
                    "id": "H2",
                    "title": "Exam absence",
                    "text": "Medical evidence is required.",
                },
            ]
        ),
        encoding="utf-8",
    )

    handbook = Handbook.from_json(path)
    rule = handbook.search("thesis registration")

    assert rule is not None
    assert rule.id == "H1"


def test_handbook_empty_query(tmp_path):
    path = tmp_path / "handbook.json"
    path.write_text("[]", encoding="utf-8")

    handbook = Handbook.from_json(path)

    assert handbook.search("") is None


def test_handbook_invalid_json(tmp_path):
    path = tmp_path / "handbook.json"
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(DataError):
        Handbook.from_json(path)


def test_handbook_missing_field(tmp_path):
    path = tmp_path / "handbook.json"
    path.write_text(
        json.dumps([{"id": "H1", "title": "Thesis registration"}]),
        encoding="utf-8",
    )

    with pytest.raises(DataError):
        Handbook.from_json(path)


def test_template_responder():
    rule = Rule(
        id="H1",
        title="Thesis registration",
        text="Students need 120 credits.",
    )

    answer = TemplateResponder().explain("thesis", rule)

    assert "Thesis registration" in answer
    assert "120 credits" in answer


def test_stub_responder_success():
    rule = Rule(
        id="H1",
        title="Thesis registration",
        text="Students need 120 credits.",
    )

    answer = StubLLMResponder().explain("thesis", rule)

    assert "120 credits" in answer


def test_stub_responder_failure():
    rule = Rule(
        id="H1",
        title="Thesis registration",
        text="Students need 120 credits.",
    )

    with pytest.raises(ProviderError):
        StubLLMResponder(fail=True).explain("thesis", rule)


def test_handbook_search_ignores_common_short_words(tmp_path):
    path = tmp_path / "handbook.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "H1",
                    "title": "Credit load",
                    "text": "This is a rule about credit load.",
                }
            ]
        ),
        encoding="utf-8",
    )

    handbook = Handbook.from_json(path)

    assert handbook.search("is") is None
