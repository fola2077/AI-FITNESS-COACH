from PySide6.QtCore import QObject, Signal, Slot, QThread

class FormGraderWorker(QObject):
    grading_finished = Signal(dict)  # Emitted when grading is done
    grading_failed = Signal(str)     # Emitted on error

    def __init__(self, form_grader, frame_metrics):
        super().__init__()
        self.form_grader = form_grader
        self.frame_metrics = frame_metrics

    @Slot()
    def run(self):
        try:
            result = self.form_grader.grade_repetition_weighted(self.frame_metrics)
            self.grading_finished.emit(result)
        except Exception as e:
            self.grading_failed.emit(str(e))
