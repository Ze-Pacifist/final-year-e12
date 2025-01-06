# Team Container

The `teams` folder contains the setup and configuration for team-specific containers, which host the challenges for the Attack-Defense CTF platform.

---

## Structure

### Files and Directories

- **`challenges/`**: Directory containing all the challenge files.
- **`Dockerfile`**: Docker configuration file to build the team container image.
- **`entrypoint.sh`**: The script executed when the container starts. It initializes and runs Supervisord.
- **`supervisord.conf`**: Configuration file for Supervisord to manage and start all challenges/services within the container.
