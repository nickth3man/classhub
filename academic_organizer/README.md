# Academic Organizer

A comprehensive desktop application designed to help students organize their educational materials, track assignments, manage courses, and provide AI-powered study assistance.

## Features

- **Material Organization**: Import and organize class materials, schedules, and other information
- **Assignment Tracking**: Automatically track assignments, deadlines, and workload
- **Study Enhancement**: Intelligent tools to help study more effectively
- **Personalized Dashboard**: Customizable dashboard showing important academic information

## Technology Stack

- **Python 3.8+**: Primary programming language
- **PyQt6**: GUI framework for desktop application
- **SQLite**: Embedded database system
- **OpenRouter API**: AI capabilities for content analysis and study assistance

## Project Structure

```
academic_organizer/
├── src/                  # Source code
│   ├── core/             # Core application functionality
│   ├── gui/              # User interface components
│   ├── modules/          # Functional modules
│   ├── database/         # Database operations
│   └── utils/            # Utility functions and helpers
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/academic_organizer.git
   cd academic_organizer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```
   pip install -e .
   ```

## Usage

Run the application:
```
academic-organizer
```

## Development

### Setting up the development environment

1. Install development dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run tests:
   ```
   pytest
   ```

## License

MIT License