#!/usr/bin/env python3
"""Quick test for tempo analysis"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.grading.advanced_form_grader import IntelligentFormGrader, BiomechanicalMetrics
import numpy as np

def create_fast_rep():
    metrics = []
    for i in range(20):  # < 1 second - too fast
        knee_angle = 180 - (i/20) * 90 if i < 10 else 90 + (i-10)/10 * 90
        metric = BiomechanicalMetrics(
            knee_angle_left=knee_angle,
            knee_angle_right=knee_angle,
            back_angle=150,
            center_of_mass_x=0.5,
            center_of_mass_y=0.5,
            landmark_visibility=0.9
        )
        metrics.append(metric)
    return metrics

grader = IntelligentFormGrader(difficulty='casual')
result = grader.grade_repetition(create_fast_rep())
print(f'Score: {result["score"]}, Faults: {result["faults"]}')
print(f'Analyzers: {list(result.get("analysis_details", {}).keys())}')
print(f'Duration: {len(create_fast_rep())/30.0:.2f}s')
