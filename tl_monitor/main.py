"""
Main entry point for the GPU Monitor application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from gpu_monitor.ui.main_window import MainWindow

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec()) 