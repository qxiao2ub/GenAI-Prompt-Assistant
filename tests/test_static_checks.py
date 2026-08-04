from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
APP = APP_PATH.read_text(encoding="utf-8")


def test_required_files_exist():
    assert APP_PATH.exists()
    assert (ROOT / "requirements.txt").exists()
    assert (ROOT / "README.md").exists()
    assert (ROOT / "data" / "sample_user_history.csv").exists()
    assert (ROOT / ".streamlit" / "config.toml").exists()


def test_branding_and_credits():
    assert 'APP_NAME = "GenAI Prompt Assistant"' in APP
    assert 'AUTHOR_NAME = "Yashvi Mehta"' in APP
    assert 'MENTOR_NAME = "Dr. Qingyang Xiao"' in APP


def test_streamlit_entrypoint_is_self_contained():
    assert "from src." not in APP
    assert "import src" not in APP
    assert 'if __name__ == "__main__":' in APP


def test_lovable_design_is_integrated():
    assert "hero-card" in APP
    assert "score-ring" in APP
    assert "Saved Prompts" in APP
    assert "Teach GenAI Prompt" in APP
    assert (ROOT / "ui_reference" / "styles.css").exists()


def test_python_compiles():
    py_compile.compile(str(APP_PATH), doraise=True)
