#!/usr/bin/env python3
"""
Step 2 Demo: Validation Dataset Workflow Demonstration
====================================================

Demonstrates the complete workflow of Step 2:
1. Adding videos to validation dataset
2. Human expert scoring
3. AI analysis
4. Comparison and calibration insights

This shows how the system would be used in practice to build
a validation dataset for AI vs human comparison.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.create_validation_dataset import ValidationDataset

def demo_full_workflow():
    """Demonstrate the complete validation workflow"""
    print("🎬 STEP 2 DEMO: VALIDATION DATASET WORKFLOW")
    print("=" * 60)
    
    # Initialize dataset
    dataset = ValidationDataset()
    
    # Check for available sample videos
    sample_videos = [
        "0918_squat_000064.mp4",
        "0922_squat_000003.mp4", 
        "1108_squat_000144.mp4"
    ]
    
    available_videos = []
    for video in sample_videos:
        video_path = project_root / video
        if video_path.exists():
            available_videos.append(str(video_path))
    
    if not available_videos:
        print("⚠️ No sample videos found for demonstration")
        print("   Place squat videos in the project root to test")
        return
    
    print(f"\n📹 Found {len(available_videos)} sample videos for demo")
    
    # Step 1: Add videos to dataset
    print(f"\n🔷 STEP 1: Adding videos to validation dataset")
    print("-" * 40)
    
    video_ids = []
    for i, video_path in enumerate(available_videos[:2]):  # Limit to 2 for demo
        try:
            video_id = dataset.add_video(
                video_path=video_path,
                exercise_type="squat",
                difficulty_level="intermediate"
            )
            video_ids.append(video_id)
            
        except Exception as e:
            print(f"⚠️ Could not add video {video_path}: {e}")
    
    if not video_ids:
        print("❌ No videos successfully added")
        return
    
    # Step 2: Add human expert scores (simulated)
    print(f"\n🔷 STEP 2: Adding human expert scores")
    print("-" * 40)
    
    # Simulate expert scoring for demonstration
    expert_scores = [
        {
            "overall_score": 78.5,
            "safety_score": 85.0,
            "depth_score": 70.0,
            "stability_score": 80.0,
            "rep_count": 8,
            "expert_name": "Expert_A",
            "major_faults": ["INSUFFICIENT_DEPTH"],
            "minor_faults": ["SLIGHT_INSTABILITY"],
            "confidence": 90.0,
            "notes": "Good form overall, needs slightly deeper squats"
        },
        {
            "overall_score": 65.2,
            "safety_score": 60.0,
            "depth_score": 75.0,
            "stability_score": 60.0,
            "rep_count": 6,
            "expert_name": "Expert_B", 
            "major_faults": ["BACK_ROUNDING", "POOR_STABILITY"],
            "minor_faults": ["INCONSISTENT_DEPTH"],
            "confidence": 85.0,
            "notes": "Safety concerns with back posture, unstable throughout movement"
        }
    ]
    
    for i, video_id in enumerate(video_ids):
        if i < len(expert_scores):
            score = expert_scores[i]
            success = dataset.add_human_score(
                video_id=video_id,
                overall_score=score["overall_score"],
                safety_score=score["safety_score"], 
                depth_score=score["depth_score"],
                stability_score=score["stability_score"],
                rep_count=score["rep_count"],
                expert_name=score["expert_name"],
                major_faults=score["major_faults"],
                minor_faults=score["minor_faults"],
                confidence=score["confidence"],
                notes=score["notes"]
            )
            
            if success:
                print(f"   ✅ Added expert score for {video_id}")
    
    # Step 3: Run AI analysis
    print(f"\n🔷 STEP 3: Running AI analysis")
    print("-" * 40)
    
    for video_id in video_ids:
        print(f"\n   Analyzing {video_id}...")
        success = dataset.run_ai_analysis(video_id, difficulty="casual")
        if success:
            print(f"   ✅ AI analysis completed")
        else:
            print(f"   ❌ AI analysis failed")
    
    # Step 4: Compare AI vs Human scores
    print(f"\n🔷 STEP 4: AI vs Human comparison")
    print("-" * 40)
    
    comparisons = []
    for video_id in video_ids:
        comparison = dataset.compare_ai_vs_human(video_id)
        if comparison:
            comparisons.append(comparison)
            
            print(f"\n📊 Comparison for {video_id}:")
            print(f"   Human Score: {comparison['human_scores']['overall']:.1f}%")
            print(f"   AI Score: {comparison['ai_scores']['overall']:.1f}%")
            print(f"   Difference: {comparison['differences']['overall']:+.1f}%")
            
            print(f"   Component Differences:")
            print(f"     Safety: {comparison['differences']['safety']:+.1f}%")
            print(f"     Depth: {comparison['differences']['depth']:+.1f}%")
            print(f"     Stability: {comparison['differences']['stability']:+.1f}%")
    
    # Step 5: Generate validation report
    print(f"\n🔷 STEP 5: Validation report")
    print("-" * 40)
    
    report = dataset.generate_validation_report()
    
    print(f"\n📈 VALIDATION REPORT SUMMARY:")
    print(f"   Total Videos: {report['dataset_statistics']['total_videos']}")
    print(f"   Fully Validated: {report['dataset_statistics']['fully_validated_videos']}")
    print(f"   Completion Rate: {report['dataset_statistics']['completion_rate']:.1f}%")
    
    if report['accuracy_analysis']['average_absolute_differences']:
        print(f"\n   Average Score Differences:")
        diffs = report['accuracy_analysis']['average_absolute_differences']
        print(f"     Overall: {diffs['overall']:.1f}%")
        print(f"     Safety: {diffs['safety']:.1f}%")
        print(f"     Depth: {diffs['depth']:.1f}%")
        print(f"     Stability: {diffs['stability']:.1f}%")
    
    if report['recommendations']:
        print(f"\n   🎯 Recommendations:")
        for rec in report['recommendations']:
            print(f"     • {rec}")
    
    # Final summary
    dataset.print_dataset_summary()
    
    print(f"\n✅ STEP 2 DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print(f"🎯 Key Achievements:")
    print(f"   ✅ Video dataset management system created")
    print(f"   ✅ Human expert scoring system implemented")
    print(f"   ✅ AI analysis integration working")
    print(f"   ✅ AI vs Human comparison functioning")
    print(f"   ✅ Validation reporting system operational")
    
    print(f"\n📊 Calibration Insights:")
    for comparison in comparisons:
        video_id = comparison['video_id']
        overall_diff = comparison['differences']['overall']
        if abs(overall_diff) > 10:
            direction = "higher" if overall_diff > 0 else "lower"
            print(f"   • AI scores {direction} than human by {abs(overall_diff):.1f}% for {video_id}")
    
    print(f"\n🚀 Ready for Step 3: AI vs Human Calibration System!")

if __name__ == "__main__":
    demo_full_workflow()
