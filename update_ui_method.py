import re

def update_ui_method():
    return '''    def update_ui(self, live_metrics: dict):
        """
        Updates the UI with live, real-time data.
        """
        # Update only the labels that change in real-time
        self.rep_label.setText(str(live_metrics.get('rep_count', 0)))
        self.phase_label.setText(live_metrics.get('phase', '...'))
        
        # Update advanced metrics if available in live data
        angles = live_metrics.get('angles', {})
        if angles:
            # Update depth (knee angle)
            knee_angle = angles.get('knee', angles.get('left_knee', 0))
            if knee_angle > 0:
                self.depth_label.setText(f"{knee_angle:.0f}°")
        
        # Update form score from current metrics
        current_score = live_metrics.get('form_score', 100)
        if current_score != 100:  # Only update if we have a real score
            self.form_score_label.setText(f"{current_score}%")
        
        # Update FPS display in status bar
        fps = live_metrics.get('fps', 0)
        session_state = live_metrics.get('session_state', 'UNKNOWN')
        landmarks_detected = live_metrics.get('landmarks_detected', False)
        status_msg = f"FPS: {fps:.0f} | State: {session_state} | Pose: {'✅' if landmarks_detected else '❌'}"
        self.status_bar.showMessage(status_msg)'''

# Path to the file
file_path = r'c:\Users\KAMI\Downloads\AI-FITNESS-COACH\src\gui\main_window.py'

# Read the file content
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Define the pattern for the update_ui method (using multiline search)
pattern = r'def update_ui\(self, live_metrics: dict\):[^}]*?# The form_score_label and feedback_display are now updated[^}]*?by display_rep_analysis after a rep is complete\.'

# Replace all occurrences with the new implementation
new_content = re.sub(pattern, update_ui_method(), content, flags=re.DOTALL)

# Write the updated content back to the file
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(new_content)

print("File updated successfully!")
