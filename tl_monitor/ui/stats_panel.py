"""
Statistics panel implementation for displaying kernel statistics.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt

class StatsPanel(QWidget):
    """Panel for displaying kernel statistics."""
    
    def __init__(self):
        """Initialize the stats panel."""
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create group box for overall statistics
        stats_group = QGroupBox("Overall Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        # Create table for overall statistics
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        stats_layout.addWidget(self.stats_table)
        
        layout.addWidget(stats_group)
        
        # Set minimum width
        self.setMinimumWidth(300)
        
    def set_data(self, data):
        """Set the data to display."""
        if not data or 'timeline' not in data:
            self.stats_table.setRowCount(0)
            return
            
        timeline = data['timeline']
        if timeline.empty:  # Use DataFrame's empty property
            self.stats_table.setRowCount(0)
            return
            
        # Calculate statistics
        total_kernels = len(timeline)
        total_duration = timeline['dur'].sum()  # Use DataFrame's sum method
        avg_duration = total_duration / total_kernels if total_kernels > 0 else 0
        unique_kernels = timeline['name'].nunique()  # Use DataFrame's nunique method
        
        # Define properties to display
        properties = [
            ("Total Kernels", str(total_kernels)),
            ("Total Duration", f"{total_duration:.3f} ms"),
            ("Average Duration", f"{avg_duration:.3f} ms"),
            ("Unique Kernels", str(unique_kernels))
        ]
        
        # Update table
        self.stats_table.setRowCount(len(properties))
        for row, (prop, value) in enumerate(properties):
            self.stats_table.setItem(row, 0, QTableWidgetItem(prop))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
    def show_kernel_details(self, kernel_info):
        """Display details for a single kernel."""
        if not kernel_info:
            self.stats_table.setRowCount(0)
            return
            
        # Define properties to display
        properties = [
            ("Name", kernel_info.get('name', '')),
            ("Start Time", kernel_info.get('timestamp', '').strftime('%H:%M:%S.%f')[:-3]),
            ("End Time", kernel_info.get('end_time', '').strftime('%H:%M:%S.%f')[:-3]),
            ("Duration", f"{kernel_info.get('dur', 0):.3f} ms"),
            ("Process ID", str(kernel_info.get('pid', ''))),
            ("Thread ID", str(kernel_info.get('tid', '')))
        ]
        
        # Update table
        self.stats_table.setRowCount(len(properties))
        for row, (prop, value) in enumerate(properties):
            self.stats_table.setItem(row, 0, QTableWidgetItem(prop))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
    def show_kernels_details(self, kernel_infos):
        """Display details for multiple kernels."""
        if not kernel_infos:
            self.stats_table.setRowCount(0)
            return
            
        # Calculate statistics
        total_duration = sum(k.get('dur', 0) for k in kernel_infos)
        avg_duration = total_duration / len(kernel_infos) if kernel_infos else 0
        kernel_names = set(k.get('name', '') for k in kernel_infos)
        
        # Define properties to display
        properties = [
            ("Number of Kernels", str(len(kernel_infos))),
            ("Total Duration", f"{total_duration:.3f} ms"),
            ("Average Duration", f"{avg_duration:.3f} ms"),
            ("Unique Kernel Names", ", ".join(sorted(kernel_names))),
            ("Process IDs", ", ".join(sorted(set(str(k.get('pid', '')) for k in kernel_infos)))),
            ("Thread IDs", ", ".join(sorted(set(str(k.get('tid', '')) for k in kernel_infos))))
        ]
        
        # Update table
        self.stats_table.setRowCount(len(properties))
        for row, (prop, value) in enumerate(properties):
            self.stats_table.setItem(row, 0, QTableWidgetItem(prop))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value))) 