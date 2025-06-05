# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Testing
- Run all tests: `pixi run tests`
- Single test file: `pixi run tests tests/path/to/test_file.py`
- With coverage: `pytest --cov=simstack tests/`
- Test specific function: `pytest tests/test_file.py::test_function_name`

### Linting and Code Quality
- Run linting: `pixi run lint`
- Pre-commit hooks: `pixi run pre-commit-run`
- Type checking: `pixi run mypy`

### Building and Running
- Run application: `pixi run simstack`
- Build conda package: `pixi run condabuild`
- Build Python package: `pixi run pythonbuild`

### Environment Management
- Default development environment: `pixi shell` (includes PySide6, development tools)
- Test environment: `pixi shell -e test` (includes pytest, pytest-qt, pytest-xvfb)
- Lint environment: `pixi shell -e lint` (includes ruff, pre-commit)

## Architecture Overview

**SimStack** is a Qt-based desktop workflow editor application built with PySide6. The application follows an MVC-like architecture with clear separation between UI components, business logic, and data models.

### Core Application Flow
1. **Entry Point**: `SimStackEntryPoint.py` initializes Qt application, loads settings, creates `WFEditorApplication`
2. **Main Application**: `WFEditorApplication` orchestrates the entire application, manages SSH connections, handles workflow operations
3. **View Management**: `WFViewManager` coordinates between UI components and application logic
4. **UI Components**: Modular Qt widgets organized in the `view/` directory

### Key Architectural Components

**Application Layer**:
- `WFEditorApplication`: Central application controller, manages SSH connections, workflow operations, and UI coordination
- `WaNoSettingsProvider`: Configuration management using YAML settings
- `SimStackPaths`: Path utilities for settings, temp files, and application directories

**UI Layer** (`view/` directory):
- `WFEditor`: Main workflow editor widget with drag-and-drop interface
- `WFEditorMainWindow`: Application main window with menus, toolbars, status bar
- `WFViewManager`: UI controller that bridges view components with application logic
- `WaNoViews.py`: Collection of specialized input widgets for workflow nodes (WaNos)
- `wf_editor_models.py`/`wf_editor_views.py`: Model-view components for workflow editing

**Remote Operations**:
- `SSHConnector`: Manages remote connections via SSH, handles file operations, job submission
- `WFRemoteFileSystem`: File browser interface for remote systems
- Integration with `SimStackServer` for cluster management and workflow execution

**Settings and Configuration**:
- Settings stored in YAML format in user-specific directories
- `QtClusterSettingsProvider`: Qt-specific cluster configuration
- `AbstractSettings`: Base configuration management with validation

### Workflow Node (WaNo) System
The application is built around "WaNos" (Workflow Nodes) - configurable computation units:
- Each WaNo has custom UI views defined in `WaNoViews.py`
- WaNo registry system for discovering available computational modules
- Dynamic form generation based on WaNo XML specifications
- Supports control flow elements: ForEach, If/Variable, Parallel, While

### Testing Architecture
- Extensive test suite with 445+ tests, focusing on unit testing of individual components
- Uses `pytest-qt` for Qt widget testing with `qtbot` fixtures
- Many complex UI tests are skipped due to mocking complexity
- Mock-heavy approach for testing UI components that require extensive Qt setup

### Dependencies and Integration
- **Qt Framework**: PySide6 for desktop UI (recently migrated from Qt5)
- **Remote Communication**: SSH via paramiko, ZMQ for messaging
- **Workflow Engine**: Integrates with `SimStackServer` package for job execution
- **Serialization**: YAML for settings, XML for WaNo definitions

### File Organization Patterns
- `view/`: All Qt UI components and widgets
- `lib/`: Shared utilities and abstract base classes
- `ctrl_img/`: Control flow icons (ForEach, If, Parallel, While)
- `Media/`: Application icons and images
- Tests mirror source structure in `tests/` directory
