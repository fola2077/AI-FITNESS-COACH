import sys
import os
from PySide6.QtWidgets import QApplication

# Add the project's root directory to the Python path
# This allows for absolute imports from the 'src' directory
# (e.g., 'from src.gui.main_window import MainWindow')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import MainWindow after the path has been adjusted
from src.gui.main_window import MainWindow # noqa: E402

def run_application():
    """
    Initializes and runs the main Qt application.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    run_application()