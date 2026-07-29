from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_required_files_exist():
    assert (ROOT / "app.py").exists()
    assert (ROOT / "requirements.txt").exists()
    assert (ROOT / "data" / "sample_user_history.csv").exists()


def test_branding_is_updated():
    assert 'APP_NAME = "GenAI Prompt Assistant"' in APP
    assert 'AUTHOR_NAME = "Yashvi Mehta"' in APP
    assert 'MENTOR_NAME = "Dr. Qingyang Xiao"' in APP
    assert "Yashvi AI Prompt Assistant" not in APP


def test_app_is_self_contained():
    assert "from src." not in APP
    assert "import src" not in APP
