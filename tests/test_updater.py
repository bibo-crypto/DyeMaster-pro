import pytest

pytest.importorskip("tkinter")

from app.updater import AppUpdater


def test_version_comparison_handles_v_prefix_and_missing_components():
    updater = AppUpdater("1.2.3")
    assert updater._is_newer("v1.2.4", "1.2.3")
    assert updater._is_newer("1.10", "1.9.9")
    assert not updater._is_newer("1.2.3-rc1", "1.2.3")


def test_release_asset_digest_and_zip_selection(monkeypatch):
    updater = AppUpdater("1.0.0")
    release = {
        "assets": [
            {"name": "DyeMasterPro.zip", "browser_download_url": "https://example.test/app.zip", "digest": "sha256:ABC"},
            {"name": "version.txt", "browser_download_url": "https://example.test/version.txt"},
            {"name": "setup.exe", "browser_download_url": "https://example.test/setup.exe"},
        ]
    }
    zip_url, version_url = updater._extract_asset_urls(release)
    assert zip_url.endswith("app.zip")
    assert version_url.endswith("version.txt")
    assert updater._find_asset_digest(release, zip_url) == "abc"
