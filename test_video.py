import cv2
from src.processing.pose_processor import PoseProcessor

def analyze_video(video_path):
    """
    Analyzes a video file without the GUI, printing the results to the console.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return

    processor = PoseProcessor()
    frame_count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        processed_frame, results = processor.process_frame(frame)

        # Print results to the console for testing
        if results:
            print(f"Frame {frame_count}: Phase={results.get('phase', 'N/A')}, Knee Angle={int(results.get('knee_angle', 0))}")

        # Optionally, display the video with overlays
        cv2.imshow("Video Analysis", processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("Video analysis complete.")

if __name__ == '__main__':
    # Replace with the path to your test video
    video_to_test = "path/to/your/test_video.mp4" 
    analyze_video(video_to_test)