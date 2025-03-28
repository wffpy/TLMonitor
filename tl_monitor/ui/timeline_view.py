"""
Timeline view for displaying GPU kernel execution timeline.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QPushButton,
    QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsItem,
    QGraphicsItemGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor,
    QKeyEvent
)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class CustomGraphicsView(QGraphicsView):
    # Define signal at class level
    kernels_selected = pyqtSignal(list)

    def __init__(self, sence):
        super().__init__(sence)

    def mouseReleaseEvent(self, event):
        if self.dragMode() == QGraphicsView.DragMode.RubberBandDrag:
            print("call mouseReleaseEvent!!!!!!!!!!")
            # Get the rubber band rectangle
            rubber_band_rect = self.rubberBandRect()
            # Convert rubber band rectangle to scene coordinates
            scene_rect = self.mapToScene(rubber_band_rect).boundingRect()
            
            # Get all items in the rubber band area
            items_in_rubber_band = self.scene().items(scene_rect)
            
            # Filter for kernel events (QGraphicsRectItem with data)
            selected_items = []
            for item in items_in_rubber_band:
                if (isinstance(item, QGraphicsRectItem) and 
                    item.data(0) is not None):  # Check if it's a kernel event
                    
                    # Get kernel rectangle
                    kernel_rect = item.rect()
                    
                    # Check if kernel is fully within selection rectangle
                    # Both start and end points of the kernel must be within the selection area
                    kernel_start = kernel_rect.x()
                    kernel_end = kernel_rect.x() + kernel_rect.width()
                    selection_start = scene_rect.x()
                    selection_end = scene_rect.x() + scene_rect.width()
                    
                    if (kernel_start >= selection_start and 
                        kernel_end <= selection_end):
                        selected_items.append(item)
            
            # Get kernel information from selected items
            selected_kernels = []
            for item in selected_items:
                kernel_info = item.data(0)
                if kernel_info:
                    selected_kernels.append(kernel_info)
            
            # Emit selected kernels information
            if selected_kernels:
                self.kernels_selected.emit(selected_kernels)
                print("Selected kernels:", selected_kernels)
                
        super().mouseReleaseEvent(event)


class TimelineView(QWidget):
    """Timeline view widget for displaying GPU kernel execution timeline."""
    
    # Signal emitted when a kernel is selected
    kernel_selected = pyqtSignal(dict)
    # Signal emitted when multiple kernels are selected
    kernels_selected = pyqtSignal(list)
    
    def __init__(self):
        """Initialize the timeline view."""
        super().__init__()
        
        # Initialize data
        self.timeline_data = None
        self.start_time = None
        self.end_time = None
        self.time_range = 0
        self.zoom_factor = 1.0
        self.base_width = 1000
        self.selected_kernel = None
        
        # Fixed dimensions
        self.left_margin = 250  # Fixed width for process/thread names
        self.row_height = 30
        self.process_header_height = 40
        self.kernel_height = 20
        self.kernel_y_offset = 5
        self.time_axis_height = 40
        
        # Selection variables
        self.rubber_band = None
        self.selection_start = None
        self.is_selecting = False
        self.selected_kernels = []  # Store selected kernels during rubber band selection
        self.selected_items = []    # Store selected items during rubber band selection
        
        # Create UI
        self._create_ui()
        
        # Set focus policy to receive keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Navigation settings
        self.pan_step = 50  # Pixels to move per key press
        
        # Store groups for separate scaling
        self.data_group = None
        self.axis_group = None
        self.sidebar_group = None
        
        # Store the last known size for resize handling
        self.last_size = self.size()
        
    def _create_ui(self):
        """Create the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Create graphics view
        self.scene = QGraphicsScene()
        # self.view = QGraphicsView(self.scene)
        self.view = CustomGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Enable rubber band selection mode
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Connect the kernels_selected signal
        self.view.kernels_selected.connect(self.kernels_selected.emit)
        
        # Create sidebar view
        self.sidebar_scene = QGraphicsScene()
        self.sidebar_view = QGraphicsView(self.sidebar_scene)
        self.sidebar_view.setFixedWidth(self.left_margin)
        self.sidebar_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create viewport layout
        viewport_widget = QWidget()
        viewport_layout = QHBoxLayout(viewport_widget)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        viewport_layout.addWidget(self.sidebar_view)
        viewport_layout.addWidget(self.view)
        
        layout.addWidget(viewport_widget)
        
        # Add zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setContentsMargins(5, 0, 5, 5)
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        reset_zoom_btn = QPushButton("Reset Zoom")
        reset_zoom_btn.clicked.connect(self._reset_zoom)
        zoom_layout.addWidget(reset_zoom_btn)
        
        zoom_layout.addStretch()
        layout.addLayout(zoom_layout)
        
    def set_data(self, data):
        """Set the data to display.
        
        Args:
            data (dict): Processed data from DataLoader
        """
        self.timeline_data = data['timeline']
        self._update_display()
        
    def _truncate_kernel_name(self, name, max_length=25):
        """Truncate kernel name if it's too long.
        
        Args:
            name (str): Original kernel name
            max_length (int): Maximum length before truncation
            
        Returns:
            str: Truncated name with ellipsis if necessary
        """
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
        
    def _update_display(self):
        """Update the display with current data."""
        # Clean up any existing rubber band before clearing the scene
        if self.rubber_band is not None:
            try:
                if self.rubber_band.scene() == self.scene:
                    self.scene.removeItem(self.rubber_band)
            except:
                pass  # Ignore any errors during cleanup
            self.rubber_band = None
            
        if self.timeline_data is None or self.timeline_data.empty:  # Use DataFrame's empty property
            return
            
        # Clear scenes
        self.scene.clear()
        self.sidebar_scene.clear()
        
        # Create groups
        self.data_group = QGraphicsItemGroup()
        self.axis_group = QGraphicsItemGroup()
        self.scene.addItem(self.data_group)
        self.scene.addItem(self.axis_group)
        
        # Get timeline data and calculate dimensions
        timeline_data = self.timeline_data
        self.start_time = timeline_data['timestamp'].min()
        self.end_time = timeline_data['end_time'].max()
        self.time_range = (self.end_time - self.start_time).total_seconds() * 1000
        
        # Calculate dimensions
        view_width = self.view.viewport().width()
        view_height = self.view.viewport().height()
        self.base_width = max(view_width, self.time_range * 0.2)
        
        # Create color map
        kernel_types = timeline_data['name'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(kernel_types)))
        color_map = dict(zip(kernel_types, colors))
        
        # Add navigation hint
        nav_hint = QGraphicsTextItem("Navigation: W/S - Up/Down, A/D - Left/Right")
        nav_hint.setDefaultTextColor(QColor(100, 100, 100))
        nav_hint.setPos(10, 5)
        self.axis_group.addToGroup(nav_hint)
        
        # Group data by pid and tid
        process_groups = {}
        for pid in timeline_data['pid'].unique():
            process_data = timeline_data[timeline_data['pid'] == pid]
            thread_groups = {}
            for tid in process_data['tid'].unique():
                thread_data = process_data[process_data['tid'] == tid]
                thread_groups[tid] = thread_data
            process_groups[pid] = thread_groups
            
        # Calculate total height
        total_threads = sum(len(threads) for threads in process_groups.values())
        total_processes = len(process_groups)
        scene_height = max(
            view_height,
            self.time_axis_height +  # Time axis area
            total_threads * self.row_height +  # Thread rows
            total_processes * self.process_header_height  # Process headers
        )
        
        # Set scene sizes
        current_width = self.base_width * self.zoom_factor
        self.scene.setSceneRect(0, 0, current_width, scene_height)
        self.sidebar_scene.setSceneRect(0, 0, self.left_margin, scene_height)
        
        # Store kernel labels
        self.kernel_labels = {}
        
        # Draw process and thread groups
        y_offset = self.time_axis_height
        for pid, thread_groups in process_groups.items():
            # Draw process header in sidebar
            process_rect = QGraphicsRectItem(0, y_offset, self.left_margin - 10, self.process_header_height)
            process_rect.setBrush(QBrush(QColor(200, 200, 200)))
            process_rect.setPen(QPen(Qt.GlobalColor.darkGray))
            self.sidebar_scene.addItem(process_rect)
            
            process_text = QGraphicsTextItem(f"Process {pid}")
            process_text.setPos(10, y_offset + 3)
            process_text.setDefaultTextColor(Qt.GlobalColor.black)
            self.sidebar_scene.addItem(process_text)
            
            y_offset += self.process_header_height
            
            for tid, thread_data in thread_groups.items():
                # Draw thread header in sidebar
                thread_rect = QGraphicsRectItem(20, y_offset, self.left_margin - 30, self.row_height)
                thread_rect.setBrush(QBrush(QColor(240, 240, 240)))
                thread_rect.setPen(QPen(Qt.GlobalColor.lightGray))
                self.sidebar_scene.addItem(thread_rect)
                
                thread_text = QGraphicsTextItem(f"Thread {tid}")
                thread_text.setPos(30, y_offset + self.kernel_y_offset + 3)
                thread_text.setDefaultTextColor(Qt.GlobalColor.black)
                self.sidebar_scene.addItem(thread_text)
                
                # Draw kernel events in main view
                for _, event in thread_data.iterrows():
                    rect = self._draw_kernel_event(event, y_offset, color_map, pid, tid)
                    self.data_group.addToGroup(rect)
                
                y_offset += self.row_height
            
            y_offset += 10  # Extra space between processes
            
        # Update grid and time axis
        self._draw_grid(current_width, scene_height)
        self._draw_time_axis(current_width, scene_height)
        
        # Synchronize scroll bars
        self.view.verticalScrollBar().valueChanged.connect(
            self.sidebar_view.verticalScrollBar().setValue
        )
        self.sidebar_view.verticalScrollBar().valueChanged.connect(
            self.view.verticalScrollBar().setValue
        )
        
        # Ensure views show the entire height
        self.view.ensureVisible(0, 0, 1, scene_height)
        self.sidebar_view.ensureVisible(0, 0, 1, scene_height)
        
    def _format_time_value(self, time_value_ns):
        """Format time value to appropriate unit.
        
        Args:
            time_value_ns (float): Time value in nanoseconds
            
        Returns:
            tuple: (formatted string, unit string)
        """
        if time_value_ns < 1000:  # < 1μs
            return f"{time_value_ns:.0f}", "ns"
        elif time_value_ns < 1000000:  # < 1ms
            return f"{time_value_ns/1000:.1f}", "μs"
        elif time_value_ns < 60000000:  # < 1min
            return f"{time_value_ns/1000000:.1f}", "ms"
        else:  # >= 1min
            return f"{time_value_ns/60000000000:.1f}", "min"

    def _draw_kernel_event(self, event, y_offset, color_map, pid, tid):
        """Draw a single kernel event."""
        # Calculate x position and width based on time and zoom
        time_to_x = self.base_width / self.time_range  # Pixels per millisecond at base zoom
        
        # Calculate start and end positions relative to viewport
        x_start = ((event['timestamp'] - self.start_time).total_seconds() * 1000) * time_to_x
        x_end = ((event['end_time'] - self.start_time).total_seconds() * 1000) * time_to_x
        width = max(2, x_end - x_start)
        
        # Create kernel rectangle with scaled x position and width only
        rect = QGraphicsRectItem(
            x_start * self.zoom_factor,  # Scale x position
            y_offset + self.kernel_y_offset,  # Fixed y position
            width * self.zoom_factor,  # Scale width only
            self.kernel_height  # Fixed height, no scaling
        )
        
        # Set appearance
        color = color_map[event['name']]
        base_brush = QBrush(QColor(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255),
            200
        ))
        rect.setBrush(base_brush)
        rect.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        rect.setData(2, base_brush)  # Store original brush for reset
        
        # Format duration for tooltip
        duration_ns = event['dur'] * 1000000  # Convert ms to ns
        duration_str, duration_unit = self._format_time_value(duration_ns)
        
        # Add tooltip and make selectable
        rect.setToolTip(
            f"Name: {event['name']}\n"
            f"Duration: {duration_str} {duration_unit}\n"
            f"Start: {event['timestamp'].strftime('%H:%M:%S.%f')[:-3]}\n"
            f"End: {event['end_time'].strftime('%H:%M:%S.%f')[:-3]}\n"
            f"Process: {pid}, Thread: {tid}"
        )
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        rect.setData(0, event.to_dict())
        rect.setData(1, event['name'])
        
        return rect

    def _draw_grid(self, width, height):
        """Draw background grid."""
        pen = QPen(QColor(230, 230, 230))
        
        # Draw vertical lines with scaled spacing
        grid_spacing = 100 * self.zoom_factor
        for x in range(0, int(width), int(grid_spacing)):
            line = QGraphicsLineItem(x, 0, x, height)
            line.setPen(pen)
            self.data_group.addToGroup(line)
            
        # Draw horizontal lines (unscaled)
        for y in range(0, int(height), self.row_height):
            line = QGraphicsLineItem(0, y, width, y)
            line.setPen(pen)
            self.data_group.addToGroup(line)

    def _draw_time_axis(self, width, height):
        """Draw time axis with markers."""
        # Draw main axis line
        axis_pen = QPen(Qt.GlobalColor.black, 2)
        time_axis = QGraphicsLineItem(0, 40, width, 40)
        time_axis.setPen(axis_pen)
        self.axis_group.addToGroup(time_axis)
        
        # Calculate number of markers and time interval
        base_markers = 20
        num_markers = int(base_markers * min(self.zoom_factor, 10))  # Limit max markers
        marker_pen = QPen(Qt.GlobalColor.black, 1)
        
        # Calculate time interval between markers in nanoseconds
        time_per_marker = (self.time_range * 1000000) / num_markers  # Convert ms to ns
        
        # Determine appropriate time unit based on zoom factor
        if self.zoom_factor >= 8:  # High zoom level - show nanoseconds
            unit_divisor = 1
            unit = "ns"
        elif self.zoom_factor >= 4:  # Medium zoom level - show microseconds
            unit_divisor = 1000
            unit = "μs"
        else:  # Low zoom level - show milliseconds
            unit_divisor = 1000000
            unit = "ms"
        
        # Add unit label with fixed font size
        unit_text = QGraphicsTextItem(f"Time ({unit})")
        unit_text.setPos(10, 5)
        unit_text.setDefaultTextColor(Qt.GlobalColor.black)
        font = unit_text.font()
        font.setPointSize(10)
        unit_text.setFont(font)
        self.axis_group.addToGroup(unit_text)
        
        # Draw time markers
        time_to_x = self.base_width / self.time_range  # Pixels per millisecond at base zoom
        for i in range(num_markers + 1):
            # Calculate x position based on time
            time_ms = (i / num_markers) * self.time_range
            x = time_ms * time_to_x * self.zoom_factor
            time_ns = time_ms * 1000000  # Convert ms to ns
            
            # Draw marker line
            marker = QGraphicsLineItem(x, 35, x, 45)
            marker.setPen(marker_pen)
            self.axis_group.addToGroup(marker)
            
            # Format time value based on current unit
            time_value = time_ns / unit_divisor
            if unit == "ns":
                time_str = f"{time_value:.0f}"
            else:
                time_str = f"{time_value:.1f}"
            
            # Add time label with fixed font size
            time_text = QGraphicsTextItem(time_str)
            text_width = len(time_str) * 6  # Approximate width of text
            time_text.setPos(x - text_width/2, 15)
            time_text.setDefaultTextColor(Qt.GlobalColor.black)
            font = time_text.font()
            font.setPointSize(10)
            time_text.setFont(font)
            if self.zoom_factor > 2.0:
                time_text.setRotation(-45)
            self.axis_group.addToGroup(time_text)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        if event.key() == Qt.Key.Key_W:  # Up
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - self.pan_step
            )
        elif event.key() == Qt.Key.Key_S:  # Down
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() + self.pan_step
            )
        elif event.key() == Qt.Key.Key_A:  # Left
            self.view.horizontalScrollBar().setValue(
                self.view.horizontalScrollBar().value() - self.pan_step
            )
        elif event.key() == Qt.Key.Key_D:  # Right
            self.view.horizontalScrollBar().setValue(
                self.view.horizontalScrollBar().value() + self.pan_step
            )
        else:
            super().keyPressEvent(event)
            
    def _zoom_in(self):
        """Zoom in the view."""
        self.zoom_factor *= 1.2
        self._apply_zoom()
        
    def _zoom_out(self):
        """Zoom out the view."""
        self.zoom_factor = max(0.1, self.zoom_factor / 1.2)  # Prevent too small zoom
        self._apply_zoom()
        
    def _reset_zoom(self):
        """Reset the zoom level."""
        self.zoom_factor = 1.0
        self._apply_zoom()
        
    def _apply_zoom(self):
        """Apply the current zoom factor."""
        if not self.data_group or not self.axis_group:
            return
            
        # Calculate new scene width based on zoom
        new_width = max(self.view.viewport().width(), self.base_width * self.zoom_factor)
        current_height = self.scene.height()
        
        # Clear main scene
        self.scene.clear()
        
        # Recreate groups
        self.data_group = QGraphicsItemGroup()
        self.axis_group = QGraphicsItemGroup()
        self.scene.addItem(self.data_group)
        self.scene.addItem(self.axis_group)
        
        # Update scene size (only width changes)
        self.scene.setSceneRect(0, 0, new_width, current_height)
        
        # Redraw the display with new horizontal scaling
        self._update_display()
        
        # Always reset to leftmost position after zoom
        self.view.horizontalScrollBar().setValue(0)
        
        # Update the view
        self.view.update()

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Get the scene point under the mouse before zoom
            mouse_pos = event.position()
            scene_pos = self.view.mapToScene(int(mouse_pos.x()), int(mouse_pos.y()))
            
            # Determine zoom direction
            if event.angleDelta().y() > 0:
                self.zoom_factor *= 1.2
            else:
                self.zoom_factor = max(0.1, self.zoom_factor / 1.2)
            
            # Apply zoom
            self._apply_zoom()
            
            # Prevent event from being handled further
            event.accept()
        else:
            # Handle normal scrolling
            super().wheelEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            print("call mousePressEvent!!!!!!!!!!")
            # Convert mouse position to scene coordinates
            scene_pos = self.view.mapToScene(self.view.mapFromParent(event.pos()))
            
            # Check if we're in the main view area (not in sidebar)
            if event.pos().x() > self.left_margin:
                # First check if we clicked directly on a kernel
                item = self.scene.itemAt(scene_pos, self.view.transform())
                if isinstance(item, QGraphicsRectItem) and item != self.rubber_band:
                    # Get kernel info
                    kernel_info = item.data(0)
                    if kernel_info:
                        # Update selection
                        if self.selected_kernel is not None:
                            try:
                                if self.selected_kernel.scene() is not None:  # Check if item still exists
                                    self.selected_kernel.setBrush(self.selected_kernel.brush())  # Reset color
                            except:
                                pass  # Ignore any errors during cleanup
                        item.setBrush(QBrush(QColor(255, 165, 0, 200)))  # Highlight selected kernel
                        self.selected_kernel = item
                        
                        # Emit single kernel selection signal
                        self.kernel_selected.emit(kernel_info)
                        return
                
                # If we didn't click on a kernel, start rubber band selection
                # Clean up any existing rubber band
                if self.rubber_band is not None:
                    try:
                        if self.rubber_band.scene() == self.scene:
                            self.scene.removeItem(self.rubber_band)
                    except:
                        pass  # Ignore any errors during cleanup
                self.rubber_band = None
                
                # Clear previous selection
                if self.selected_kernel is not None:
                    try:
                        if self.selected_kernel.scene() is not None:  # Check if item still exists
                            self.selected_kernel.setBrush(self.selected_kernel.brush())  # Reset color
                    except:
                        pass  # Ignore any errors during cleanup
                    self.selected_kernel = None
                
                # Start rubber band selection
                self.selection_start = scene_pos
                self.is_selecting = True
                
                # Create new rubber band
                self.rubber_band = QGraphicsRectItem()
                self.rubber_band.setPen(QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine))
                self.rubber_band.setBrush(QBrush(QColor(0, 0, 255, 50)))
                self.scene.addItem(self.rubber_band)
                
                # Set initial rectangle
                self.rubber_band.setRect(QRectF(
                    self.selection_start.x(),
                    0,  # Always start from top
                    0,  # Will be updated in mouseMoveEvent
                    self.scene.height()  # Full height selection
                ))
                
                # Force update the view
                self.view.viewport().update()
        
        # Don't call super().mousePressEvent(event) to prevent default behavior
        event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        print("call mouseMoveEvent!!!!!!!!!!")
        if self.is_selecting and self.rubber_band is not None:
            # Convert current mouse position to scene coordinates
            scene_pos = self.view.mapToScene(self.view.mapFromParent(event.pos()))
            print("move event scene_pos: {}".format(scene_pos))
            
            # Update rubber band rectangle
            selection_rect = QRectF(
                self.selection_start.x(),
                0,  # Always start from top
                scene_pos.x() - self.selection_start.x(),
                self.scene.height()  # Full height selection
            )
            self.rubber_band.setRect(selection_rect)
            
            # Reset previous selections
            if self.selected_kernel is not None:
                try:
                    if self.selected_kernel.scene() is not None:
                        self.selected_kernel.setBrush(self.selected_kernel.brush())  # Reset color
                except:
                    pass
                self.selected_kernel = None
            
            # Clear previous selection lists
            self.selected_kernels = []
            self.selected_items = []
            
            # Get all items in the scene
            for item in self.scene.items():
                if (isinstance(item, QGraphicsRectItem) and 
                    item != self.rubber_band and
                    item.data(0) is not None):  # Check if it's a kernel event
                    print("item: {}".format(iterm))
                    
                    # Get kernel rectangle
                    kernel_rect = item.rect()
                    
                    # Check if kernel is within selection rectangle
                    if (kernel_rect.x() + kernel_rect.width() >= selection_rect.x() and
                        kernel_rect.x() <= selection_rect.x() + selection_rect.width()):
                        
                        kernel_info = item.data(0)
                        if kernel_info:
                            self.selected_kernels.append(kernel_info)
                            self.selected_items.append(item)
            
            # Highlight selected kernels
            for item in self.selected_items:
                try:
                    if item.scene() is not None:  # Check if item still exists
                        # Store original brush if not already stored
                        if item.data(2) is None:
                            item.setData(2, item.brush())
                        # Set highlight color
                        item.setBrush(QBrush(QColor(255, 165, 0, 200)))
                except:
                    continue
            
            # Emit selected kernels information to update right panel
            if self.selected_kernels:
                self.kernels_selected.emit(self.selected_kernels)
            
            # Force update the view
            self.view.viewport().update()
        
        # Don't call super().mouseMoveEvent(event) to prevent default behavior
        event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            
            if self.rubber_band is not None:
                try:
                    # Use the selected kernels and items from mouseMoveEvent
                    if self.selected_kernels:
                        # Emit selected kernels information
                        self.kernels_selected.emit(self.selected_kernels)
                        # Store the first selected kernel as the current selection
                        if self.selected_items:
                            self.selected_kernel = self.selected_items[0]
                finally:
                    # Always clean up the rubber band
                    try:
                        if self.rubber_band.scene() == self.scene:
                            self.scene.removeItem(self.rubber_band)
                    except:
                        pass  # Ignore any errors during cleanup
                    self.rubber_band = None
                    
                    # Force update the view
                    self.view.viewport().update()
        
        # Don't call super().mouseReleaseEvent(event) to prevent default behavior
        event.accept()

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        
        # Store current size for next resize
        self.last_size = event.size()
        
        # Update the display if we have data
        if self.timeline_data is not None and not self.timeline_data.empty:  # Use DataFrame's empty property
            self._update_display()
            
            # Ensure view shows the entire height without scaling
            self.view.ensureVisible(0, 0, 1, self.scene.height())
            self.sidebar_view.ensureVisible(0, 0, 1, self.sidebar_scene.height()) 