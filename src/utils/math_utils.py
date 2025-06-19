# ai_fitness_coach/src/utils/math_utils.py
import math


def joint_angle(ax, ay, bx, by, cx, cy):
    """
    Returns the angle ABC (at point B) in degrees.
    Args are pixel coords (x,y).
    """
    # vectors BA and BC
    v1x, v1y = ax - bx, ay - by
    v2x, v2y = cx - bx, cy - by

    # dot product / norms → cosine
    dot = v1x * v2x + v1y * v2y
    norm = math.hypot(v1x, v1y) * math.hypot(v2x, v2y)
    if norm == 0:
        return 0.0

    cos_ang = max(-1.0, min(1.0, dot / norm))
    return math.degrees(math.acos(cos_ang))
