import cv2
import os
import time
from pathlib import Path
from src.processing.pose_processor import PoseProcessor

def analyze_video(video_path):
    """
    Analyzes a video file without the GUI, printing the results to the console.
    """
    print("\n" + "="*50)
    print(f"Starting video analysis: {video_path}")
    print("="*50)
    
    # Verify the video file exists
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file does not exist at {video_path}")
        return
        
    # Create video capture
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file at {video_path}")
        return
    
    # Get video info
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video Info:")
    print(f"   - Resolution: {frame_width}x{frame_height}")
    print(f"   - FPS: {fps}")
    print(f"   - Total frames: {frame_count_total}")
    print(f"   - Duration: {frame_count_total/fps:.1f} seconds")

    # Initialize processor with debug mode
    processor = PoseProcessor()
    processor.pose_detector.debug_mode = True  # Enable debug output
    frame_count = 0
    landmarks_found_count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        
        # Handle the updated format from process_frame which now returns a dictionary
        results = processor.process_frame(frame)
        
        # Get landmarks detected status
        landmarks_detected = results.get('landmarks_detected', False)
        
        # Process frame with overlays based on results
        processed_frame = processor.draw_overlays_improved(frame.copy(), results, results.get('faults', []))

        # Print comprehensive results to the console for testing
        phase = results.get('phase', 'N/A')
        reps = results.get('reps', 0)
        form_score = results.get('form_score', 0)
        
        # Track landmark detection stats
        if results.get('landmarks_detected', False):
            landmarks_found_count += 1
            landmark_status = "✅"
        else:
            landmark_status = "❌"
            
        print(f"Frame {frame_count}: {landmark_status} Pose detected: {results.get('landmarks_detected', False)}, Phase={phase}, Reps={reps}, Score={form_score}")

        # Optionally, display the video with overlays
        cv2.imshow("Video Analysis", processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    
    # Print summary statistics
    print("\n" + "="*50)
    print("Video analysis complete.")
    print(f"Total frames processed: {frame_count}")
    print(f"Frames with pose detected: {landmarks_found_count} ({landmarks_found_count/frame_count*100:.1f}%)")
    print(f"Frames without pose: {frame_count - landmarks_found_count} ({(frame_count-landmarks_found_count)/frame_count*100:.1f}%)")
    print("="*50)

if __name__ == '__main__':
    import os
    from pathlib import Path
    
    # First try to use our test video if it exists
    project_root = Path(__file__).parent.absolute()
    test_video_path = project_root / "tests" / "fixtures" / "sample_videos" / "test_movement.mp4"
    
    # If test video doesn't exist, create it
    if not test_video_path.exists():
        print(f"Test video not found at {test_video_path}")
        print("Creating test video first...")
        try:
            from create_test_video import create_dummy_video
            test_video_dir = test_video_path.parent
            test_video_dir.mkdir(parents=True, exist_ok=True)
            create_dummy_video(str(test_video_path), duration=5, fps=30, resolution=(640, 480))
            print(f"Created test video at {test_video_path}")
        except Exception as e:
            print(f"Failed to create test video: {e}")
            # Fall back to the original path
            test_video_path = "C:\\Users\\KAMI\\Downloads\\Video_Dataset\\Video_Dataset_mini\\good\\0922_squat_000058.mp4"
    
    # Use the appropriate video path
    if test_video_path.exists():
        video_to_test = str(test_video_path)
    else:
        # Fallback to the original path
        video_to_test = "C:\\Users\\KAMI\\Downloads\\Video_Dataset\\Video_Dataset_mini\\good\\0922_squat_000058.mp4"
    
    print(f"Using video: {video_to_test}")
    analyze_video(video_to_test)