"""
Details panel implementation for displaying kernel information.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt

class DetailsPanel(QWidget):
    """Panel for displaying detailed kernel information."""
    
    def __init__(self):
        """Initialize the details panel."""
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create group box
        group_box = QGroupBox("Kernel Details")
        group_layout = QVBoxLayout(group_box)
        
        # Create table for kernel details
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        group_layout.addWidget(self.table)
        
        layout.addWidget(group_box)
        
        # Set minimum width
        self.setMinimumWidth(300)
        
    def show_kernel_details(self, kernel_info):
        """Display details for a single kernel."""
        if not kernel_info:
            self.table.setRowCount(0)
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
        self.table.setRowCount(len(properties))
        for row, (prop, value) in enumerate(properties):
            self.table.setItem(row, 0, QTableWidgetItem(prop))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))
            
    def show_kernels_details(self, kernel_infos):
        """Display details for multiple kernels."""
        if not kernel_infos:
            self.table.setRowCount(0)
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
        self.table.setRowCount(len(properties))
        for row, (prop, value) in enumerate(properties):
            self.table.setItem(row, 0, QTableWidgetItem(prop))
            self.table.setItem(row, 1, QTableWidgetItem(str(value))) 