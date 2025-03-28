# GPU Monitor

A Python-based GUI tool for analyzing GPU kernel profiling information from JSON files.

## Features

- Load and analyze GPU kernel profiling data from JSON files
- Interactive timeline visualization of kernel executions
- Detailed kernel statistics and metrics
- Performance bottleneck analysis
- Memory usage tracking
- Customizable views and filters

## Installation

```bash
# Clone the repository
git clone git@github.com:wffpy/TLMonitor.git 
cd tl_monitor

# Install the package
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Usage

Launch the application:
```bash
tl-monitor
```

Or run directly:
```bash
python -m tl_monitor
```

### Loading Data

1. Click "File" -> "Open" or press Ctrl+O
2. Select your GPU profiling JSON file
3. The data will be loaded and displayed in the main window

### Features

#### Timeline View
- Visual representation of kernel execution timeline
- Zoom and pan capabilities
- Click on kernels for detailed information

#### Statistics Panel
- Kernel execution statistics
- Memory usage metrics
- Performance bottlenecks

#### Filtering
- Filter kernels by name, duration, or other metrics
- Custom time range selection
- Search functionality

## Development

### Code Formatting

```bash
# Format code
python format_code.py
```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 