from pathlib import Path
from robot_validator import validate_episode

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_episodes"


def test_valid_episode_passes():
    errors = validate_episode(SAMPLE_DIR / "episode_001_valid.json")
    assert errors == []


def test_defective_episode_catches_camera_battery_and_label_issues():
    errors = validate_episode(SAMPLE_DIR / "episode_002_defective.json")
    joined = "\n".join(errors)
    assert "head_rgb" in joined
    assert "pin robot yếu" in joined
    assert "human_verified=False" in joined
    assert "chồng lấp thời gian" in joined
    assert "quá ngắn" in joined
