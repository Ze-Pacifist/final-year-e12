# Service Controller

The `service_controller` module is the core component of the Attack-Defense CTF platform. It manages service health checks, flag planting, and communication with the database and scoreboard.

---

## Features

- **Health Check Automation**: Runs periodic checks on team services to ensure functionality.
- **Flag Management**: Generates unique flags and plants them into team services.
- **Database Integration**: Updates the database with flag and service status information.
- **Scoreboard Updates**: Tracks team performance and updates the scoreboard.

---

## Structure

### Files
- `src/service_controller.py`: Main script for managing the service health checks and flag planting.
- `src/database_operations.py`: Handles all interactions with the SQLite database.
- `src/scoreboard_operations.py`: Manages the scoreboard logic and updates.

### Folders
- `src/checkers`: Folder for storing all checker scripts to be executed by the service_controller

