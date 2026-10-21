"""The playbook format's schema, and the case table every implementation of it runs.

`schemas/0.1/playbook.schema.json` says what a `playbook.json` may hold, as a reader of
0.1 reads it, and this repository is where the format is published. A reader that checks documents
with code of its own vendors the schema and the table beside it, and a pair
mirrored across two repositories drifts in whichever direction nobody is looking.
So the cases live beside the schema, in `playbook.cases.json`, and a vendoring
repository runs the same table with its own checker. Each invalid case is a valid
one with exactly one change, which is what makes "it failed" mean "it failed for
that change".
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
README = (ROOT / "README.md").read_text(encoding="utf-8")
VERSION = "0.1"
SCHEMA = json.loads((SCHEMAS / VERSION / "playbook.schema.json").read_text(encoding="utf-8"))
CASES = json.loads((SCHEMAS / VERSION / "playbook.cases.json").read_text(encoding="utf-8"))
VALID: dict[str, Any] = {case["name"]: case["document"] for case in CASES["valid"]}
VALIDATOR = Draft202012Validator(SCHEMA)


def _tokens(pointer: str) -> list[str]:
    """RFC 6901: split a JSON Pointer, and unescape ``~1`` before ``~0``."""
    assert pointer.startswith("/"), f"not a JSON Pointer: {pointer!r}"
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def _apply(document: Any, change: dict[str, Any]) -> Any:
    """Apply one RFC 6902 add, replace or remove to a copy of *document*.

    Stricter than the RFC on purpose: an ``add`` must create a member rather than
    overwrite one, and a ``replace`` or ``remove`` must find one, so a case whose
    path is misspelt fails here instead of passing because its base was invalid.
    """
    changed = copy.deepcopy(document)
    *parents, last = _tokens(change["path"])
    target = changed
    for token in parents:
        target = target[int(token)] if isinstance(target, list) else target[token]
    op = change["op"]
    if isinstance(target, list):
        index = int(last)
        if op == "add":
            target.insert(index, change["value"])
        elif op == "replace":
            target[index] = change["value"]
        elif op == "remove":
            del target[index]
        else:
            raise AssertionError(f"unknown op {op!r}")
        return changed
    if op == "add":
        assert last not in target, f"add would overwrite {change['path']}"
        target[last] = change["value"]
    elif op == "replace":
        assert last in target, f"nothing to replace at {change['path']}"
        target[last] = change["value"]
    elif op == "remove":
        assert last in target, f"nothing to remove at {change['path']}"
        del target[last]
    else:
        raise AssertionError(f"unknown op {op!r}")
    return changed


def _errors(document: Any) -> list[str]:
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '(root)'}: {error.message}"
        for error in VALIDATOR.iter_errors(document)
    ]


def test_the_schema_is_a_draft_2020_12_schema() -> None:
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("name", ["playbook.schema.json", "playbook.cases.json"])
def test_each_file_is_written_as_a_script_rewrites_it(name: str) -> None:
    """Two spaces, characters as written and a final newline: what ``json.dumps(indent=2,
    ensure_ascii=False)`` writes. So a hand edit and a scripted one make the same diff, and a
    repository that copies the files can compare them byte for byte."""
    raw = (SCHEMAS / VERSION / name).read_text(encoding="utf-8")
    assert raw == json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n"


def test_its_identifier_names_the_directory_it_is_published_from() -> None:
    """The ``$id`` is permanent once served, and the directory is the format's major and minor."""
    assert SCHEMA["$id"] == f"https://sigrix.io/schemas/muster/{VERSION}/playbook.schema.json"
    assert re.fullmatch(SCHEMA["properties"]["format_version"]["pattern"], VERSION)
    assert CASES["schema"] == SCHEMA["$id"], "the case table names another schema"


@pytest.mark.parametrize("name", list(VALID))
def test_a_valid_case_validates(name: str) -> None:
    assert _errors(VALID[name]) == []


@pytest.mark.parametrize("case", CASES["invalid"], ids=[case["name"] for case in CASES["invalid"]])
def test_an_invalid_case_fails(case: dict[str, Any]) -> None:
    assert case["base"] in VALID, f"{case['name']!r} is built on {case['base']!r}, which is not a valid case"
    document = _apply(VALID[case["base"]], case["change"])
    assert document != VALID[case["base"]], "the change changed nothing"
    assert _errors(document), f"{case['name']!r} validates, so the schema allows what the case says it refuses"


def test_case_names_are_unique() -> None:
    names = [case["name"] for case in CASES["valid"] + CASES["invalid"]]
    assert len(names) == len(set(names))


def test_a_reader_reads_any_minor_of_its_major() -> None:
    """A minor version only adds members a reader of an earlier one can ignore, so the
    pattern admits every ``0.x`` and nothing else."""
    pattern = SCHEMA["properties"]["format_version"]["pattern"]
    assert all(re.fullmatch(pattern, version) for version in ("0.1", "0.2", "0.10"))
    assert not any(re.fullmatch(pattern, version) for version in ("1.0", "0", "0.1.0", "v0.1"))


def _objects(schema: dict[str, Any], place: str) -> list[tuple[dict[str, Any], str]]:
    """Every object schema the documents hold, with the pattern of the paths it sits at.

    Walked from the root: a member's object is at ``<place>/<member>``, a list's items at
    ``<place>/<member>/<index>``, and a ``$ref`` is followed into ``$defs``. A ``$ref`` to
    a string (``path``) is no object, and is left out.
    """
    if "$ref" in schema:
        schema = SCHEMA["$defs"][schema["$ref"].rsplit("/", 1)[1]]
    if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        return _objects(schema["items"], f"{place}/[0-9]+")
    if schema.get("type") != "object":
        return []
    found = [(schema, place)]
    for member, child in schema.get("properties", {}).items():
        found += _objects(child, f"{place}/{member}")
    return found


def test_every_member_appears_in_a_valid_case() -> None:
    """A member no valid document carries is one nothing shows a writer how to write."""
    members = {member for schema, _ in _objects(SCHEMA, "") for member in schema.get("properties", {})}
    used: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            used.update(value)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for document in VALID.values():
        walk(document)
    assert members - used == set()


def test_every_required_member_has_a_case_without_it() -> None:
    """Derived from the schema, so a member made required later needs its case too."""
    removed = {case["change"]["path"] for case in CASES["invalid"] if case["change"]["op"] == "remove"}
    wanted = {f"{place}/{member}" for schema, place in _objects(SCHEMA, "") for member in schema.get("required", [])}
    missing = {pattern for pattern in wanted if not any(re.fullmatch(pattern, path) for path in removed)}
    assert missing == set()


def test_every_object_the_documents_hold_is_located() -> None:
    """The canary for the two tests above: a definition the walk cannot reach it cannot check."""
    located = {id(schema) for schema, _ in _objects(SCHEMA, "")}
    objects = {name for name, definition in SCHEMA["$defs"].items() if definition.get("type") == "object"}
    assert objects == {"file", "slot"}, "the format grew an object: say where it sits"
    assert all(id(SCHEMA["$defs"][name]) in located for name in objects)
    # The slots member is an object of its own, holding the two lists.
    assert any(place == "/slots" for _, place in _objects(SCHEMA, ""))


def test_the_helper_refuses_a_change_that_finds_nothing() -> None:
    """The guard on the guard: a misspelt path must not read as a passing case."""
    base = VALID["the least a playbook may say"]
    with pytest.raises(AssertionError):
        _apply(base, {"op": "remove", "path": "/titel"})
    with pytest.raises(AssertionError):
        _apply(base, {"op": "add", "path": "/title", "value": "x"})


def test_the_readmes_example_is_the_first_valid_case() -> None:
    """The README shows a whole playbook, folder and document; this keeps it the one the table runs."""
    example = re.search(r"```json\n(.*?)\n```", README, re.DOTALL)
    assert example, "the README shows no document"
    document = json.loads(example.group(1))
    assert document == CASES["valid"][0]["document"]
    assert re.findall(r"^[├└]── (\S+)", README, re.MULTILINE) == ["playbook.json", *document["order"]]


def test_the_readmes_tables_name_every_member_and_every_role() -> None:
    """The two tables restate the schema's members and roles, so they are held to it both ways."""
    rows = set(re.findall(r"^\| `([^`]+)` \|", README, re.MULTILINE))
    members = set(SCHEMA["properties"])
    roles = set(SCHEMA["$defs"]["file"]["properties"]["role"]["enum"])
    assert rows == members | roles
