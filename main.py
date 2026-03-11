import sys
import os
import random
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Property, Signal, QAbstractListModel, Qt

# Senior Python Developer Note: We use a model-view approach.
# We have a dedicated backend class to manage data and screen state.

class KiroBackend(QObject):
    def __init__(self):
        super().__init__()
        self._current_screen = "WelcomeScreen.qml"
        self._total_files = 0
        self._time_saved = 0
        self._text_count = 0
        self._image_count = 0
        # Mock timeline data for the portfolio showcase
        self._timeline_data = [
            {"date": "2023-10-27", "files": 120},
            {"date": "2023-10-26", "files": 85},
            {"date": "2023-10-25", "files": 210},
            {"date": "2023-10-24", "files": 55},
            {"date": "2023-10-23", "files": 180},
            {"date": "2023-10-22", "files": 95},
            {"date": "2023-10-21", "files": 140},
        ]

    # --- Signals ---
    currentScreenChanged = Signal(str)
    statsUpdated = Signal()

    # --- Properties ---
    @Property(str, notify=currentScreenChanged)
    def currentScreen(self):
        return self._current_screen

    @currentScreen.setter
    def currentScreen(self, screen):
        if self._current_screen != screen:
            self._current_screen = screen
            self.currentScreenChanged.emit(screen)

    @Property(int, notify=statsUpdated)
    def totalFiles(self): return self._total_files

    @Property(int, notify=statsUpdated)
    def timeSaved(self): return self._time_saved

    @Property(int, notify=statsUpdated)
    def textCount(self): return self._text_count

    @Property(int, notify=statsUpdated)
    def imageCount(self): return self._image_count

    @Property(list, notify=statsUpdated)
    def timelineData(self): return self._timeline_data


    # --- Methods (Q_INVOKABLE) ---
    @Slot()
    def getStarted(self):
        # Move from Welcome to Configuration
        self.currentScreen = "ConfigurationScreen.qml"

    @Slot(list, bool, bool)
    def startOrganizing(self, directories, process_text, process_images):
        """Simulates the file organization process and updates analytics."""
        print(f"Starting organization for: {directories}. Text: {process_text}, Images: {process_images}")

        # In a real app, this would be a threaded operation using QThread or a worker.
        # Here we generate mock data to populate the dashboard.
        num_dirs = len(directories)
        if num_dirs == 0: return

        new_text = random.randint(100, 500) if process_text else 0
        new_image = random.randint(100, 500) if process_images else 0
        
        self._text_count += new_text
        self._image_count += new_image
        self._total_files = self._text_count + self._image_count
        # Simulate ~3 seconds per file saved
        self._time_saved = int(self._total_files * 3 / 60)
        
        # Add a new timeline entry
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        if self._timeline_data and self._timeline_data[0]["date"] == today:
             self._timeline_data[0]["files"] += (new_text + new_image)
        else:
             self._timeline_data.insert(0, {"date": today, "files": new_text + new_image})
             if len(self._timeline_data) > 7:
                 self._timeline_data.pop()

        self.statsUpdated.emit()
        # Navigate to Dashboard
        self.currentScreen = "AnalyticsDashboard.qml"


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon.fromTheme("system-file-manager"))
    app.setOrganizationName("KiroAI")
    app.setApplicationName("Kiro AI File Organizer")

    engine = QQmlApplicationEngine()
    
    # Instantiate the backend
    backend = KiroBackend()
    
    # Expose the backend to QML
    engine.rootContext().setContextProperty("kiroBackend", backend)
    
    # Load the main QML file
    qml_file = os.path.join(os.path.dirname(__file__), "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)
        
    sys.exit(app.exec())