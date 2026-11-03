"""Crystal extractor (tree-sitter-crystal, optional [crystal] extra)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from graphify.detect import CODE_EXTENSIONS
from graphify.extract import extract, extract_crystal
from graphify.rcfile import LANGUAGE_ALIASES

FIXTURES = Path(__file__).parent / "fixtures"

needs_crystal = pytest.mark.skipif(
    importlib.util.find_spec("tree_sitter_crystal") is None,
    reason="tree-sitter-crystal not installed (optional [crystal] extra)",
)


def _sample():
    return extract_crystal(FIXTURES / "sample.cr")


def _label_of(r):
    return {n["id"]: n["label"] for n in r["nodes"]}


def _edges(r, relation):
    labels = _label_of(r)
    return {
        (labels.get(e["source"], e["source"]), labels.get(e["target"], e["target"]))
        for e in r["edges"]
        if e["relation"] == relation
    }


def test_cr_is_a_code_extension():
    assert ".cr" in CODE_EXTENSIONS


def test_crystal_rc_alias():
    assert LANGUAGE_ALIASES["crystal"] == ".cr"


@needs_crystal
def test_crystal_no_error():
    assert "error" not in _sample()


@needs_crystal
def test_crystal_finds_qualified_types():
    labels = set(_label_of(_sample()).values())
    for name in ("Billing", "Billing::Invoice", "Billing::Money", "Billing::Status",
                 "Billing::Repo", "Api::Invoices::Show"):
        assert name in labels, name


@needs_crystal
def test_crystal_generic_type_label_drops_type_params():
    labels = set(_label_of(_sample()).values())
    assert not any("(T)" in label for label in labels)


@needs_crystal
def test_crystal_finds_typed_methods():
    labels = set(_label_of(_sample()).values())
    for name in (".total()", ".paid?()", ".pay!()", ".round_cents()", ".build()",
                 ".zero?()", ".find()", "format_cents()"):
        assert name in labels, name


@needs_crystal
def test_crystal_suffixed_methods_get_distinct_ids():
    ids = {n["id"] for n in _sample()["nodes"]}
    assert any(i.endswith("_paid_pred") for i in ids)
    assert any(i.endswith("_pay_bang") for i in ids)


@needs_crystal
def test_crystal_inherits_edges():
    inherits = _edges(_sample(), "inherits")
    assert ("Billing::Invoice", "BaseModel") in inherits
    assert ("Api::Invoices::Show", "ApiAction") in inherits


@needs_crystal
def test_crystal_include_and_extend_are_mixins():
    mixins = _edges(_sample(), "mixes_in")
    assert ("Billing::Invoice", "Timestamps") in mixins
    assert ("Billing::Invoice", "Lookup") in mixins


@needs_crystal
def test_crystal_calls_inside_class():
    calls = _edges(_sample(), "calls")
    assert (".total()", ".round_cents()") in calls
    assert (".pay!()", ".total()") in calls


@needs_crystal
def test_extract_dispatches_cr_files(tmp_path):
    f = tmp_path / "invoice.cr"
    f.write_text("module Billing\n  class Invoice\n    def total : Int64\n      0_i64\n    end\n  end\nend\n")
    r = extract([f], cache_root=tmp_path / "cache", root=tmp_path, parallel=False)
    labels = {n["label"] for n in r["nodes"]}
    assert "Billing::Invoice" in labels
    assert ".total()" in labels
