import pathlib, statistics
from src.scripts.run_pipeline import run_on_video

BASE = pathlib.Path(__file__).parent / "sample_videos"

def test_depth_detects_shallow():
    good = run_on_video(BASE / "squat_good.mp4", max_frames=150)
    bad  = run_on_video(BASE / "squat_shallow.mp4", max_frames=150)

    assert statistics.mean(good) < 100          # deep knee flex
    assert statistics.mean(bad)  > 120          # shallow

