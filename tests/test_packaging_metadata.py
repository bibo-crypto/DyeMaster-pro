from pathlib import Path


def test_release_metadata_is_unified_at_104():
    root = Path(__file__).resolve().parents[1]
    assert (root / "version.txt").read_text(encoding="utf-8").strip() == "1.0.4"
    installer = (root / "installer.iss").read_text(encoding="utf-8")
    assert '#define MyAppVersion "1.0.4"' in installer


def test_spec_places_version_file_next_to_executable():
    root = Path(__file__).resolve().parents[1]
    spec = (root / "DyeMasterPro.spec").read_text(encoding="utf-8")
    assert "('version.txt',  '.')" in spec
    assert "contents_directory='.'" in spec


def test_packaged_version_resolution_prefers_executable_directory(monkeypatch, tmp_path):
    import sys
    import app.config as config

    version_file = tmp_path / "version.txt"
    version_file.write_text("1.0.4\n", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "DyeMasterPro.exe"))
    assert config._resolve_version_file_path() == str(version_file)
