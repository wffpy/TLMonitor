"""
Main window implementation for the GPU Monitor application.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSplitter,
    QMenuBar, QMenu, QStatusBar, QDockWidget,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from gpu_monitor.ui.timeline_view import TimelineView
from gpu_monitor.ui.stats_panel import StatsPanel
from gpu_monitor.ui.details_panel import DetailsPanel
from gpu_monitor.core.data_loader import DataLoader

class MainWindow(QMainWindow):
    """Main window of the GPU Monitor application."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("GPU Monitor")
        self.setMinimumSize(1200, 800)
        
        # Initialize data loader
        self.data_loader = DataLoader()
        
        # Create UI components
        self._create_menubar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_statusbar()
        
        # Connect signals
        self._connect_signals()
        
    def _create_menubar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        show_stats_action = QAction("Show Statistics", self)
        show_stats_action.setCheckable(True)
        show_stats_action.setChecked(True)
        show_stats_action.triggered.connect(self._toggle_stats_panel)
        view_menu.addAction(show_stats_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _create_toolbar(self):
        """Create the toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add toolbar actions
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        toolbar.addAction(open_action)
        
    def _create_central_widget(self):
        """Create the central widget."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QHBoxLayout(central_widget)
        
        # Create left panel (timeline view)
        left_panel = QVBoxLayout()
        self.timeline_view = TimelineView()
        left_panel.addWidget(self.timeline_view)
        
        # Create right panel (stats and details)
        right_panel = QVBoxLayout()
        
        # Add stats panel
        self.stats_panel = StatsPanel()
        right_panel.addWidget(self.stats_panel)
        
        # Add details panel
        self.details_panel = DetailsPanel()
        right_panel.addWidget(self.details_panel)
        
        # Add panels to main layout
        layout.addLayout(left_panel, stretch=2)
        layout.addLayout(right_panel, stretch=1)
        
    def _create_statusbar(self):
        """Create the status bar."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # Add status message
        self.status_label = QLabel("Ready")
        statusbar.addWidget(self.status_label)
        
    def _connect_signals(self):
        """Connect signals and slots."""
        # Connect data loader signals
        self.data_loader.data_loaded.connect(self._on_data_loaded)
        self.data_loader.error_occurred.connect(self._on_error)
        
        # Connect timeline view signals
        self.timeline_view.kernel_selected.connect(self._on_kernel_selected)
        self.timeline_view.kernels_selected.connect(self._on_kernels_selected)
        
    def _open_file(self):
        """Open a file dialog to select a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open GPU Profiling Data",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            self.status_label.setText(f"Loading {os.path.basename(file_path)}...")
            self.data_loader.load_data(file_path)
            
    def _on_data_loaded(self, data):
        """Handle data loaded event."""
        self.timeline_view.set_data(data)
        self.stats_panel.set_data(data)
        self.status_label.setText("Data loaded successfully")
        
    def _on_error(self, error_message):
        """Handle error event."""
        self.status_label.setText(f"Error: {error_message}")
        
    def _on_kernel_selected(self, kernel_info):
        """Handle kernel selection event."""
        self.stats_panel.show_kernel_details(kernel_info)
        
    def _on_kernels_selected(self, kernel_infos):
        """Handle multiple kernel selection event."""
        self.stats_panel.show_kernels_details(kernel_infos)
        
    def _toggle_stats_panel(self, checked):
        """Toggle the visibility of the stats panel."""
        self.stats_panel.setVisible(checked)
        
    def _show_about(self):
        """Show the about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "About GPU Monitor",
            "GPU Monitor v0.1.0\n\n"
            "A tool for analyzing GPU kernel profiling information.\n\n"
            "Copyright © 2024"
        ) 