"""
Data loader for GPU profiling information.
"""

import json
from PyQt6.QtCore import QObject, pyqtSignal
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataLoader(QObject):
    """Data loader for GPU profiling information."""
    
    # Signals
    data_loaded = pyqtSignal(dict)  # Emitted when data is successfully loaded
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    
    def __init__(self):
        """Initialize the data loader."""
        super().__init__()
        self.data = None
        
    def load_data(self, file_path):
        """Load data from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file to load
        """
        try:
            # Read JSON file
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            # Process the data
            processed_data = self._process_data(raw_data)
            
            # Store the processed data
            self.data = processed_data
            
            # Emit signal with the processed data
            self.data_loaded.emit(processed_data)
            
        except json.JSONDecodeError:
            self.error_occurred.emit("Invalid JSON file format")
        except Exception as e:
            self.error_occurred.emit(f"Error loading data: {str(e)}")
            
    def _process_data(self, raw_data):
        """Process raw JSON data into a structured format.
        
        Args:
            raw_data (list): List of raw JSON events
            
        Returns:
            dict: Processed data with the following structure:
                {
                    'events': list of event dictionaries,
                    'kernels': list of kernel dictionaries,
                    'timeline': pandas DataFrame with timeline data,
                    'statistics': dict with various statistics
                }
        """
        try:
            # Convert events to DataFrame for easier processing
            events_df = pd.DataFrame(raw_data)
            logger.info(f"Created DataFrame with columns: {events_df.columns.tolist()}")
            
            # Print first few rows for debugging
            logger.info(f"First few rows of data:\n{events_df.head()}")
            
            # Extract kernel events
            kernel_events = events_df[
                events_df['name'].str.contains('_Z14kl3_|all_gather|reduce_scatter', na=False)
            ].copy()
            
            logger.info(f"Found {len(kernel_events)} kernel events")
            
            if kernel_events.empty:
                logger.warning("No kernel events found in the data")
                return {
                    'events': raw_data,
                    'kernels': [],
                    'timeline': pd.DataFrame(),
                    'statistics': {
                        'total_kernels': 0,
                        'unique_kernels': 0,
                        'total_time': 0,
                        'avg_duration': 0,
                        'min_duration': 0,
                        'max_duration': 0,
                        'kernel_types': {}
                    }
                }
            
            # Convert timestamps to datetime
            # First convert ts to numeric if it's not already
            kernel_events['ts'] = pd.to_numeric(kernel_events['ts'])
            kernel_events['timestamp'] = pd.to_datetime(kernel_events['ts'], unit='ns')
            
            # Convert duration to numeric if it's not already
            kernel_events['dur'] = pd.to_numeric(kernel_events['dur'])
            
            # Calculate end times
            kernel_events['end_time'] = kernel_events['timestamp'] + pd.to_timedelta(kernel_events['dur'], unit='ns')
            
            # Sort by timestamp
            kernel_events = kernel_events.sort_values('timestamp')
            
            # Calculate statistics
            stats = {
                'total_kernels': len(kernel_events),
                'unique_kernels': kernel_events['name'].nunique(),
                'total_time': kernel_events['dur'].sum() / 1e6,  # Convert to ms
                'avg_duration': kernel_events['dur'].mean() / 1e6,  # Convert to ms
                'min_duration': kernel_events['dur'].min() / 1e6,  # Convert to ms
                'max_duration': kernel_events['dur'].max() / 1e6,  # Convert to ms
                'kernel_types': kernel_events['name'].value_counts().to_dict(),
            }
            
            logger.info(f"Calculated statistics: {stats}")
            
            # Create timeline data with available columns
            available_columns = ['name', 'timestamp', 'end_time', 'dur']
            if 'args' in kernel_events.columns:
                available_columns.append('args')
            if 'cat' in kernel_events.columns:
                available_columns.append('cat')
            if 'pid' in kernel_events.columns:
                available_columns.append('pid')
            if 'tid' in kernel_events.columns:
                available_columns.append('tid')
                
            timeline_data = kernel_events[available_columns].copy()
            
            # Convert durations to milliseconds
            timeline_data['dur'] = timeline_data['dur'] / 1e6
            
            return {
                'events': raw_data,
                'kernels': kernel_events.to_dict('records'),
                'timeline': timeline_data,
                'statistics': stats
            }
            
        except Exception as e:
            error_msg = f"Error processing data: {str(e)}"
            logger.error(error_msg)
            raise 