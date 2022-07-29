# forNMA interface

## How to run
Execute the `Interface/main_fornma_window.py` script.

## Development
### Connecting forNMA functions to the interface

Import and call forNMA functions directly on `ForNMAMainWindow` class in `Interface/main_fornma_window.py` script:
- `on_preview_button_clicked` method: executes forNMA in preview mode.
- `on_run_button_clicked` method: executes forNMA in run mode.

Currently, no result visualization is performed, and no multithreading is used (UI will "freeze" while forNMA executes).

### Modifying forNMA text
Text for parameters, help messages, etc. should be modified in the `Interface/fornma_parameters/blueprints.py` file.

## Dependencies
- PySide6 (`pip install pyside6`)
- other forNMA dependencies
