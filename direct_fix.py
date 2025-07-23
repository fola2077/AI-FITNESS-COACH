# Path to the file
file_path = r'c:\Users\KAMI\Downloads\AI-FITNESS-COACH\src\gui\main_window.py'

# Read the file content
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# First replace the first occurrence (around line 459)
correct_method = '''    def update_ui(self, live_metrics: dict):
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
        self.status_bar.showMessage(status_msg)
'''

# Find the first update_ui method
first_update_ui_line = -1
for i, line in enumerate(lines):
    if "def update_ui(self, live_metrics: dict):" in line:
        first_update_ui_line = i
        break

if first_update_ui_line != -1:
    # Find the next method (where update_ui ends)
    next_method_line = -1
    for i in range(first_update_ui_line + 1, len(lines)):
        if "def " in lines[i] and lines[i].strip().startswith("def "):
            next_method_line = i
            break

    if next_method_line != -1:
        # Replace the lines
        lines[first_update_ui_line:next_method_line] = [correct_method]

# Find the second update_ui method
second_update_ui_line = -1
for i in range(first_update_ui_line + 1, len(lines)):
    if "def update_ui(self, live_metrics: dict):" in line:
        second_update_ui_line = i
        break

if second_update_ui_line != -1:
    # Find the next method (where update_ui ends)
    next_method_line = -1
    for i in range(second_update_ui_line + 1, len(lines)):
        if "def " in lines[i] and lines[i].strip().startswith("def "):
            next_method_line = i
            break

    if next_method_line != -1:
        # Replace the lines
        lines[second_update_ui_line:next_method_line] = [correct_method]

# Write back to the file
with open(file_path, 'w', encoding='utf-8') as file:
    file.writelines(lines)

print("File updated successfully!")
