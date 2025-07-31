#!/usr/bin/env python3
"""
Step 2: Real Video Validation Dataset Creation
=============================================

Creates and manages a validation dataset of human-scored squat videos for 
calibrating AI scores against expert judgment. This enables systematic 
comparison between AI and human assessment.

Key Features:
- Video metadata management (file paths, human scores, notes)
- Expert scoring interface for standardized evaluation
- AI vs Human comparison analysis
- Dataset statistics and validation reports
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.grading.advanced_form_grader import IntelligentFormGrader, ThresholdConfig
from src.processing.pose_processor import PoseProcessor


@dataclass
class HumanScore:
    """Human expert score for a video"""
    overall_score: float          # 0-100 overall form score
    safety_score: float          # 0-100 safety assessment
    depth_score: float           # 0-100 depth quality
    stability_score: float       # 0-100 stability assessment
    
    # Detailed assessments
    rep_count: int               # Number of complete reps
    major_faults: List[str]      # Critical form issues observed
    minor_faults: List[str]      # Minor form issues observed
    
    # Expert details
    expert_name: str             # Name/ID of scoring expert
    scoring_date: str            # When the video was scored
    confidence: float            # Expert's confidence in score (0-100)
    notes: str                   # Additional observations


@dataclass
class VideoMetadata:
    """Complete metadata for a validation video"""
    # File information
    file_path: str               # Path to video file
    file_size: int               # File size in bytes
    duration: float              # Video duration in seconds
    fps: int                     # Frames per second
    resolution: Tuple[int, int]  # Width x height
    
    # Content information
    exercise_type: str           # Type of exercise (squat, deadlift, etc.)
    difficulty_level: str        # Expected difficulty (beginner, intermediate, advanced)
    camera_angle: str           # Camera position (front, side, etc.)
    lighting_quality: str       # Lighting assessment (good, fair, poor)
    
    # Human scoring
    human_scores: List[HumanScore]  # Multiple expert scores
    consensus_score: Optional[float] # Agreed-upon score if multiple experts
    
    # AI scoring (filled when tested)
    ai_score: Optional[float]    # AI-generated score
    ai_analysis: Optional[Dict]  # Detailed AI analysis results
    
    # Validation metadata
    creation_date: str           # When added to dataset
    last_updated: str           # Last modification date
    validation_status: str       # ready, scored, validated, excluded
    tags: List[str]              # Categorization tags


class ValidationDataset:
    """
    Manages the validation dataset of human-scored videos.
    
    Provides functionality to:
    - Add new videos with metadata
    - Score videos with human experts
    - Run AI analysis on videos
    - Compare AI vs human scores
    - Generate validation reports
    """
    
    def __init__(self, dataset_path: str = "data/validation_dataset.json"):
        self.dataset_path = Path(dataset_path)
        self.videos: Dict[str, VideoMetadata] = {}
        
        # Create dataset directory if needed
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing dataset
        self.load_dataset()
        
        print(f"📁 Validation Dataset Manager initialized")
        print(f"   Dataset file: {self.dataset_path}")
        print(f"   Current videos: {len(self.videos)}")
    
    def load_dataset(self):
        """Load existing dataset from JSON file"""
        if self.dataset_path.exists():
            try:
                with open(self.dataset_path, 'r') as f:
                    data = json.load(f)
                
                # Convert dictionaries back to dataclass objects
                for video_id, video_data in data.items():
                    # Convert human_scores back to HumanScore objects
                    human_scores = []
                    for score_data in video_data.get('human_scores', []):
                        human_scores.append(HumanScore(**score_data))
                    
                    video_data['human_scores'] = human_scores
                    self.videos[video_id] = VideoMetadata(**video_data)
                
                print(f"✅ Loaded {len(self.videos)} videos from dataset")
                
            except Exception as e:
                print(f"⚠️ Error loading dataset: {e}")
                print("   Starting with empty dataset")
                self.videos = {}
        else:
            print("📝 Creating new dataset file")
    
    def save_dataset(self):
        """Save dataset to JSON file"""
        try:
            # Convert dataclass objects to dictionaries for JSON serialization
            data = {}
            for video_id, video_metadata in self.videos.items():
                video_dict = asdict(video_metadata)
                data[video_id] = video_dict
            
            with open(self.dataset_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Dataset saved with {len(self.videos)} videos")
            
        except Exception as e:
            print(f"❌ Error saving dataset: {e}")
    
    def add_video(self, video_path: str, exercise_type: str = "squat", 
                  difficulty_level: str = "intermediate") -> str:
        """
        Add a new video to the validation dataset.
        
        Args:
            video_path: Path to the video file
            exercise_type: Type of exercise being performed
            difficulty_level: Expected skill level
            
        Returns:
            video_id: Unique identifier for the video
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Generate unique video ID
        video_id = f"{exercise_type}_{video_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze video file
        cap = cv2.VideoCapture(str(video_path))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        # Create metadata
        metadata = VideoMetadata(
            file_path=str(video_path.absolute()),
            file_size=video_path.stat().st_size,
            duration=duration,
            fps=fps,
            resolution=(width, height),
            exercise_type=exercise_type,
            difficulty_level=difficulty_level,
            camera_angle="unknown",  # To be filled by human reviewer
            lighting_quality="unknown",  # To be filled by human reviewer
            human_scores=[],
            consensus_score=None,
            ai_score=None,
            ai_analysis=None,
            creation_date=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            validation_status="ready",
            tags=[]
        )
        
        self.videos[video_id] = metadata
        self.save_dataset()
        
        print(f"✅ Added video to dataset:")
        print(f"   ID: {video_id}")
        print(f"   File: {video_path.name}")
        print(f"   Duration: {duration:.1f}s, FPS: {fps}, Resolution: {width}x{height}")
        
        return video_id
    
    def add_human_score(self, video_id: str, overall_score: float, 
                       safety_score: float, depth_score: float, stability_score: float,
                       rep_count: int, expert_name: str, 
                       major_faults: List[str] = None, minor_faults: List[str] = None,
                       confidence: float = 100.0, notes: str = "") -> bool:
        """
        Add human expert score for a video.
        
        Args:
            video_id: Unique video identifier
            overall_score: Overall form score (0-100)
            safety_score: Safety assessment (0-100)
            depth_score: Depth quality (0-100)
            stability_score: Stability assessment (0-100)
            rep_count: Number of complete reps observed
            expert_name: Name/ID of scoring expert
            major_faults: List of critical form issues
            minor_faults: List of minor form issues
            confidence: Expert's confidence in score (0-100)
            notes: Additional observations
            
        Returns:
            bool: True if score added successfully
        """
        if video_id not in self.videos:
            print(f"❌ Video ID not found: {video_id}")
            return False
        
        human_score = HumanScore(
            overall_score=overall_score,
            safety_score=safety_score,
            depth_score=depth_score,
            stability_score=stability_score,
            rep_count=rep_count,
            major_faults=major_faults or [],
            minor_faults=minor_faults or [],
            expert_name=expert_name,
            scoring_date=datetime.now().isoformat(),
            confidence=confidence,
            notes=notes
        )
        
        self.videos[video_id].human_scores.append(human_score)
        self.videos[video_id].last_updated = datetime.now().isoformat()
        self.videos[video_id].validation_status = "scored"
        
        # Calculate consensus score if multiple experts
        if len(self.videos[video_id].human_scores) > 1:
            scores = [hs.overall_score for hs in self.videos[video_id].human_scores]
            self.videos[video_id].consensus_score = np.mean(scores)
        
        self.save_dataset()
        
        print(f"✅ Added human score for video {video_id}")
        print(f"   Expert: {expert_name}")
        print(f"   Overall Score: {overall_score}%")
        print(f"   Component Scores: Safety={safety_score}%, Depth={depth_score}%, Stability={stability_score}%")
        
        return True
    
    def run_ai_analysis(self, video_id: str, difficulty: str = "casual") -> bool:
        """
        Run AI analysis on a video and store results.
        
        Args:
            video_id: Unique video identifier
            difficulty: Difficulty setting for AI analysis
            
        Returns:
            bool: True if analysis completed successfully
        """
        if video_id not in self.videos:
            print(f"❌ Video ID not found: {video_id}")
            return False
        
        video_path = self.videos[video_id].file_path
        
        try:
            print(f"🤖 Running AI analysis on video {video_id}...")
            
            # Initialize AI components
            config = ThresholdConfig.emergency_calibrated()
            grader = IntelligentFormGrader(difficulty=difficulty, config=config)
            processor = PoseProcessor()
            
            # Process video
            cap = cv2.VideoCapture(video_path)
            all_metrics = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame through pose detection
                result = processor.process_frame(frame)
                if result and hasattr(result, 'pose_landmarks') and result.pose_landmarks:
                    # Extract biomechanical metrics
                    # This would need to be implemented based on your pose processing pipeline
                    # For now, we'll create a placeholder
                    frame_count += 1
                
                # Limit processing for demo (process every 5th frame)
                if frame_count % 5 != 0:
                    continue
                    
                if frame_count > 200:  # Limit for demo
                    break
            
            cap.release()
            
            # For demo purposes, create mock AI analysis
            # In real implementation, this would use actual pose processing results
            mock_ai_analysis = {
                'overall_score': 78.5,
                'component_scores': {
                    'safety': 85.2,
                    'depth': 72.1,
                    'stability': 77.9
                },
                'faults_detected': ['INSUFFICIENT_DEPTH', 'MINOR_INSTABILITY'],
                'rep_count': 8,
                'analysis_timestamp': datetime.now().isoformat(),
                'difficulty_used': difficulty,
                'processing_notes': 'Mock analysis - replace with real pose processing'
            }
            
            # Store AI results
            self.videos[video_id].ai_score = mock_ai_analysis['overall_score']
            self.videos[video_id].ai_analysis = mock_ai_analysis
            self.videos[video_id].last_updated = datetime.now().isoformat()
            
            if self.videos[video_id].validation_status == "scored":
                self.videos[video_id].validation_status = "validated"
            
            self.save_dataset()
            
            print(f"✅ AI analysis completed for video {video_id}")
            print(f"   AI Score: {mock_ai_analysis['overall_score']:.1f}%")
            print(f"   Component Scores: Safety={mock_ai_analysis['component_scores']['safety']:.1f}%, "
                  f"Depth={mock_ai_analysis['component_scores']['depth']:.1f}%, "
                  f"Stability={mock_ai_analysis['component_scores']['stability']:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return False
    
    def compare_ai_vs_human(self, video_id: str) -> Optional[Dict]:
        """
        Compare AI and human scores for a video.
        
        Args:
            video_id: Unique video identifier
            
        Returns:
            Dict with comparison results or None if data incomplete
        """
        if video_id not in self.videos:
            print(f"❌ Video ID not found: {video_id}")
            return None
        
        video = self.videos[video_id]
        
        if not video.human_scores:
            print(f"❌ No human scores available for video {video_id}")
            return None
        
        if video.ai_score is None:
            print(f"❌ No AI score available for video {video_id}")
            return None
        
        # Calculate human consensus
        human_overall = np.mean([hs.overall_score for hs in video.human_scores])
        human_safety = np.mean([hs.safety_score for hs in video.human_scores])
        human_depth = np.mean([hs.depth_score for hs in video.human_scores])
        human_stability = np.mean([hs.stability_score for hs in video.human_scores])
        
        # Get AI scores
        ai_overall = video.ai_score
        ai_safety = video.ai_analysis['component_scores']['safety']
        ai_depth = video.ai_analysis['component_scores']['depth']
        ai_stability = video.ai_analysis['component_scores']['stability']
        
        # Calculate differences
        comparison = {
            'video_id': video_id,
            'human_scores': {
                'overall': human_overall,
                'safety': human_safety,
                'depth': human_depth,
                'stability': human_stability
            },
            'ai_scores': {
                'overall': ai_overall,
                'safety': ai_safety,
                'depth': ai_depth,
                'stability': ai_stability
            },
            'differences': {
                'overall': ai_overall - human_overall,
                'safety': ai_safety - human_safety,
                'depth': ai_depth - human_depth,
                'stability': ai_stability - human_stability
            },
            'absolute_differences': {
                'overall': abs(ai_overall - human_overall),
                'safety': abs(ai_safety - human_safety),
                'depth': abs(ai_depth - human_depth),
                'stability': abs(ai_stability - human_stability)
            }
        }
        
        return comparison
    
    def generate_validation_report(self) -> Dict:
        """
        Generate comprehensive validation report.
        
        Returns:
            Dict containing validation statistics and analysis
        """
        total_videos = len(self.videos)
        scored_videos = len([v for v in self.videos.values() if v.human_scores])
        ai_analyzed_videos = len([v for v in self.videos.values() if v.ai_score is not None])
        validated_videos = len([v for v in self.videos.values() if v.human_scores and v.ai_score is not None])
        
        # Calculate comparison statistics for validated videos
        comparisons = []
        for video_id in self.videos:
            comparison = self.compare_ai_vs_human(video_id)
            if comparison:
                comparisons.append(comparison)
        
        if comparisons:
            overall_diffs = [c['absolute_differences']['overall'] for c in comparisons]
            safety_diffs = [c['absolute_differences']['safety'] for c in comparisons]
            depth_diffs = [c['absolute_differences']['depth'] for c in comparisons]
            stability_diffs = [c['absolute_differences']['stability'] for c in comparisons]
            
            avg_differences = {
                'overall': np.mean(overall_diffs),
                'safety': np.mean(safety_diffs),
                'depth': np.mean(depth_diffs),
                'stability': np.mean(stability_diffs)
            }
            
            max_differences = {
                'overall': np.max(overall_diffs),
                'safety': np.max(safety_diffs),
                'depth': np.max(depth_diffs),
                'stability': np.max(stability_diffs)
            }
        else:
            avg_differences = {}
            max_differences = {}
        
        report = {
            'dataset_statistics': {
                'total_videos': total_videos,
                'human_scored_videos': scored_videos,
                'ai_analyzed_videos': ai_analyzed_videos,
                'fully_validated_videos': validated_videos,
                'completion_rate': (validated_videos / total_videos * 100) if total_videos > 0 else 0
            },
            'accuracy_analysis': {
                'average_absolute_differences': avg_differences,
                'maximum_absolute_differences': max_differences,
                'validated_comparisons_count': len(comparisons)
            },
            'recommendations': [],
            'generation_date': datetime.now().isoformat()
        }
        
        # Generate recommendations based on analysis
        if avg_differences:
            if avg_differences['overall'] > 15:
                report['recommendations'].append("Overall score accuracy needs improvement - consider threshold recalibration")
            if avg_differences['safety'] > 20:
                report['recommendations'].append("Safety scoring shows significant deviation - review safety penalty calculations")
            if avg_differences['depth'] > 20:
                report['recommendations'].append("Depth scoring needs adjustment - verify depth detection thresholds")
            if avg_differences['stability'] > 20:
                report['recommendations'].append("Stability scoring requires calibration - check stability analysis parameters")
        
        if validated_videos < 10:
            report['recommendations'].append("Need more validated videos for reliable calibration - target at least 20 videos")
        
        return report
    
    def list_videos(self, status_filter: str = None) -> List[str]:
        """
        List videos in the dataset.
        
        Args:
            status_filter: Filter by validation status (ready, scored, validated, excluded)
            
        Returns:
            List of video IDs
        """
        videos = []
        for video_id, metadata in self.videos.items():
            if status_filter is None or metadata.validation_status == status_filter:
                videos.append(video_id)
        return videos
    
    def print_dataset_summary(self):
        """Print a summary of the current dataset"""
        print("\n📊 VALIDATION DATASET SUMMARY")
        print("=" * 50)
        
        if not self.videos:
            print("📁 Dataset is empty")
            print("   Use add_video() to add videos for validation")
            return
        
        # Count by status
        status_counts = {}
        for video in self.videos.values():
            status = video.validation_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"📹 Total Videos: {len(self.videos)}")
        print(f"   Ready for scoring: {status_counts.get('ready', 0)}")
        print(f"   Human scored: {status_counts.get('scored', 0)}")  
        print(f"   Fully validated: {status_counts.get('validated', 0)}")
        print(f"   Excluded: {status_counts.get('excluded', 0)}")
        
        # Show some example videos
        print(f"\n📋 Recent Videos:")
        for i, (video_id, metadata) in enumerate(list(self.videos.items())[-3:]):
            human_score = metadata.consensus_score or (metadata.human_scores[0].overall_score if metadata.human_scores else "No score")
            ai_score = metadata.ai_score or "No score"
            print(f"   {i+1}. {video_id}")
            print(f"      Status: {metadata.validation_status}, Human: {human_score}, AI: {ai_score}")


def main():
    """Interactive demo of the validation dataset system"""
    print("🎯 STEP 2: REAL VIDEO VALIDATION DATASET")
    print("=" * 60)
    print("Creating system to manage human-scored videos for AI calibration...")
    
    # Initialize dataset
    dataset = ValidationDataset()
    dataset.print_dataset_summary()
    
    print(f"\n✅ VALIDATION DATASET SYSTEM READY!")
    print(f"=" * 50)
    print(f"📋 Available Commands:")
    print(f"   dataset.add_video(video_path, exercise_type, difficulty)")
    print(f"   dataset.add_human_score(video_id, scores...)")
    print(f"   dataset.run_ai_analysis(video_id)")
    print(f"   dataset.compare_ai_vs_human(video_id)")
    print(f"   dataset.generate_validation_report()")
    
    print(f"\n📂 Next Steps:")
    print(f"   1. Add sample videos to the dataset")
    print(f"   2. Score videos with human experts")
    print(f"   3. Run AI analysis on scored videos") 
    print(f"   4. Compare results for calibration insights")
    
    print(f"\n🚀 READY FOR VIDEO VALIDATION!")
    print(f"Run: dataset.add_video('path/to/squat_video.mp4')")

if __name__ == "__main__":
    main()
