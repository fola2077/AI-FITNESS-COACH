#!/usr/bin/env python3
"""
Creates a simple dummy video to test AI Fitness Coach pose detection
"""
import cv2
import numpy as np
import os
from pathlib import Path

def create_dummy_video(output_path, duration=10, fps=30, resolution=(640, 480)):
    """Create a simple dummy video with a moving circle to simulate movement"""
    width, height = resolution
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 codec
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)
    
    if not out.isOpened():
        print(f"❌ Error: Couldn't create video at {output_path}")
        return False
    
    print(f"✅ Creating test video: {output_path}")
    print(f"   - Duration: {duration} seconds")
    print(f"   - FPS: {fps}")
    print(f"   - Resolution: {width}x{height}")
    
    total_frames = duration * fps
    
    # Create frames
    for i in range(total_frames):
        # Create a blank frame with light gray background (more contrast for pose detection)
        frame = np.ones((height, width, 3), dtype=np.uint8) * 200  # Light gray background
        
        # Calculate progress (0 to 1)
        progress = i / total_frames
        
        # Draw a moving stick figure to simulate a person
        center_x = int(width * (0.5 + 0.2 * np.sin(progress * 2 * np.pi)))
        center_y = int(height * (0.5 + 0.1 * np.cos(progress * 2 * np.pi)))
        
        # Head - much larger than before
        head_size = int(min(width, height) * 0.1)  # 10% of smaller dimension
        cv2.circle(frame, (center_x, center_y - head_size), head_size, (50, 50, 180), -1)  # Dark red
        
        # Body - thicker
        body_length = int(height * 0.3)  # 30% of height
        cv2.line(frame, 
                (center_x, center_y), 
                (center_x, center_y + body_length), 
                (50, 50, 180), 
                max(5, int(min(width, height) * 0.02)))  # Thicker line
        
        # Arms
        arm_angle = np.sin(progress * 4 * np.pi) * 0.4  # More movement
        arm_length = int(width * 0.2)  # 20% of width
        
        left_arm_x = int(center_x - arm_length * np.cos(arm_angle))
        left_arm_y = int(center_y + arm_length * np.sin(arm_angle) * 0.5)
        
        right_arm_x = int(center_x + arm_length * np.cos(arm_angle))
        right_arm_y = int(center_y + arm_length * np.sin(arm_angle) * 0.5)
        
        # Thicker arms
        arm_thickness = max(5, int(min(width, height) * 0.015))
        cv2.line(frame, (center_x, center_y + int(body_length * 0.2)), 
                (left_arm_x, left_arm_y), (50, 50, 180), arm_thickness)
        cv2.line(frame, (center_x, center_y + int(body_length * 0.2)), 
                (right_arm_x, right_arm_y), (50, 50, 180), arm_thickness)
        
        # Legs
        leg_angle = np.sin(progress * 3 * np.pi) * 0.3  # More movement
        leg_length = int(height * 0.3)  # 30% of height
        
        left_leg_x = int(center_x - leg_length * np.sin(leg_angle) * 0.5)
        left_leg_y = int(center_y + body_length + leg_length * np.cos(leg_angle))
        
        right_leg_x = int(center_x + leg_length * np.sin(leg_angle) * 0.5)
        right_leg_y = int(center_y + body_length + leg_length * np.cos(leg_angle))
        
        # Thicker legs
        leg_thickness = max(5, int(min(width, height) * 0.015))
        cv2.line(frame, (center_x, center_y + body_length), 
                (left_leg_x, left_leg_y), (50, 50, 180), leg_thickness)
        cv2.line(frame, (center_x, center_y + body_length), 
                (right_leg_x, right_leg_y), (50, 50, 180), leg_thickness)
        
        # Draw circles at joints to help with pose detection
        joint_color = (20, 20, 150)  # Darker red
        joint_size = max(4, int(min(width, height) * 0.012))
        
        # Head
        cv2.circle(frame, (center_x, center_y - head_size), joint_size, joint_color, -1)
        
        # Shoulders
        cv2.circle(frame, (center_x, center_y), joint_size * 2, joint_color, -1)
        
        # Elbows
        elbow_left_x = int(center_x - arm_length * np.cos(arm_angle) * 0.5)
        elbow_left_y = int(center_y + arm_length * np.sin(arm_angle) * 0.25)
        elbow_right_x = int(center_x + arm_length * np.cos(arm_angle) * 0.5)
        elbow_right_y = int(center_y + arm_length * np.sin(arm_angle) * 0.25)
        
        cv2.circle(frame, (elbow_left_x, elbow_left_y), joint_size, joint_color, -1)
        cv2.circle(frame, (elbow_right_x, elbow_right_y), joint_size, joint_color, -1)
        
        # Wrists
        cv2.circle(frame, (left_arm_x, left_arm_y), joint_size, joint_color, -1)
        cv2.circle(frame, (right_arm_x, right_arm_y), joint_size, joint_color, -1)
        
        # Hips
        cv2.circle(frame, (center_x, center_y + body_length), joint_size * 2, joint_color, -1)
        
        # Knees
        knee_left_x = int(center_x - leg_length * np.sin(leg_angle) * 0.25)
        knee_left_y = int(center_y + body_length + leg_length * np.cos(leg_angle) * 0.5)
        knee_right_x = int(center_x + leg_length * np.sin(leg_angle) * 0.25)
        knee_right_y = int(center_y + body_length + leg_length * np.cos(leg_angle) * 0.5)
        
        cv2.circle(frame, (knee_left_x, knee_left_y), joint_size, joint_color, -1)
        cv2.circle(frame, (knee_right_x, knee_right_y), joint_size, joint_color, -1)
        
        # Ankles
        cv2.circle(frame, (left_leg_x, left_leg_y), joint_size, joint_color, -1)
        cv2.circle(frame, (right_leg_x, right_leg_y), joint_size, joint_color, -1)
        
        # Add frame number and progress
        cv2.putText(frame, f"Frame: {i+1}/{total_frames}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        cv2.putText(frame, f"Time: {i/fps:.2f}s / {duration}s", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        cv2.putText(frame, "TEST VIDEO FOR POSE DETECTION", (width - 350, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Write frame
        out.write(frame)
        
        # Show progress
        if i % int(fps) == 0:  # Update every second
            print(f"   Progress: {i/total_frames*100:.1f}% ({i+1}/{total_frames} frames)")
    
    # Release resources
    out.release()
    
    print(f"✅ Test video created successfully: {output_path}")
    print(f"   File size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    
    return True

if __name__ == "__main__":
    # Determine project root and create output path
    project_root = Path(__file__).parent.absolute()
    test_dir = project_root / "tests" / "fixtures" / "sample_videos"
    
    # Create directory if it doesn't exist
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy video
    video_path = test_dir / "test_movement.mp4"
    create_dummy_video(str(video_path), duration=5, fps=30, resolution=(640, 480))
    
    print("\n💡 To test with this video:")
    print(f"   1. Run the app: python run_app.py")
    print(f"   2. Click 'Load Video' and select: {video_path}")
