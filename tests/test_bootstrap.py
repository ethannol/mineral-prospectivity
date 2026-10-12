"""Bootstrap refusal is tested without cloning or installing dependencies."""

import importlib.util
from pathlib import Path

import pytest


def load_bootstrap():
    path = Path(__file__).resolve().parents[1] / "scripts/bootstrap.py"
    spec = importlib.util.spec_from_file_location("mineral_bootstrap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "head,dirty",
    [("wrong-revision", ""), ("a184e0732989373856039dea2919ccd96a88e8b1", " M source.py")],
)
def test_existing_wrong_or_dirty_checkout_never_changes(monkeypatch, tmp_path, head, dirty):
    module = load_bootstrap()
    project = tmp_path / "project"
    project.mkdir()
    (tmp_path / "cairn-mineral-baseline").mkdir()
    monkeypatch.setattr(module, "ROOT", project)
    monkeypatch.setattr(
        module, "git_output", lambda directory, *args: head if args[0] == "rev-parse" else dirty
    )

    def forbidden(*args, **kwargs):
        pytest.fail("refusal must not clone, checkout or sync anything")

    monkeypatch.setattr(module.subprocess, "run", forbidden)
    with pytest.raises(RuntimeError, match="refusing"):
        module.bootstrap()


def test_correct_clean_checkout_only_syncs_locked(monkeypatch, tmp_path):
    module = load_bootstrap()
    project = tmp_path / "project"
    project.mkdir()
    (tmp_path / "cairn-mineral-baseline").mkdir()
    monkeypatch.setattr(module, "ROOT", project)
    monkeypatch.setattr(
        module,
        "git_output",
        lambda directory, *args: module.SDK_SHA if args[0] == "rev-parse" else "",
    )
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda cmd, **kwargs: calls.append((cmd, kwargs)))
    module.bootstrap()
    assert calls == [
        (["uv", "sync", "--locked", "--group", "dev"], {"cwd": project, "check": True})
    ]
