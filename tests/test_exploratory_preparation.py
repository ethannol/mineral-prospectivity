"""Non-browser regression: source scripts always receive isolated bookkeeping."""

import importlib.util
import sys
from pathlib import Path


def load_helper():
    path = Path(__file__).resolve().parents[1] / "exploratory/prepare_inputs.py"
    spec = importlib.util.spec_from_file_location("supplementary_prepare", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preparation_overrides_primary_environment(monkeypatch, tmp_path):
    helper = load_helper()
    monkeypatch.setattr(helper, "ROOT", tmp_path)
    primary = tmp_path / "artifacts"
    primary.mkdir()
    original = primary / "numbers.json"
    original.write_text("published baseline")
    monkeypatch.setenv("CAIRN_LEDGER", str(original))
    monkeypatch.setenv("CAIRN_CHECKS", str(primary / "checks.jsonl"))
    calls = []

    def fake_run(command, *, cwd, env, check):
        calls.append(command)
        assert cwd == tmp_path and check
        assert command[0] == sys.executable
        assert (
            Path(env["CAIRN_LEDGER"]) == tmp_path / "reports/exploratory/preparation/numbers.json"
        )
        assert (
            Path(env["CAIRN_CHECKS"]) == tmp_path / "reports/exploratory/preparation/checks.jsonl"
        )
        Path(env["CAIRN_LEDGER"]).write_text("supplementary bookkeeping")

    monkeypatch.setattr(helper.subprocess, "run", fake_run)
    helper.prepare_inputs()
    assert [Path(c[1]).name for c in calls] == helper.STEPS
    assert original.read_text() == "published baseline"


def test_refuses_primary_ledger_symlink(monkeypatch, tmp_path):
    import pytest

    helper = load_helper()
    monkeypatch.setattr(helper, "ROOT", tmp_path)
    primary = tmp_path / "artifacts"
    primary.mkdir()
    original = primary / "numbers.json"
    original.write_text("published baseline")
    output = tmp_path / "reports/exploratory/preparation"
    output.mkdir(parents=True)
    (output / "numbers.json").symlink_to(original)

    def forbidden(*args, **kwargs):
        pytest.fail("refusal must happen before any source script executes")

    monkeypatch.setattr(helper.subprocess, "run", forbidden)
    with pytest.raises(ValueError, match="escapes"):
        helper.prepare_inputs()
    assert original.read_text() == "published baseline"
