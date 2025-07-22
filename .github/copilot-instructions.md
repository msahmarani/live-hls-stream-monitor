<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# HLS Stream Analyzer Project

This is a Flask web application for analyzing HLS (.m3u8) streams and playlists.

## Project Structure
- `app.py`: Main Flask application with HLS analysis functionality
- `templates/`: HTML templates for the web interface
  - `index.html`: Main form for entering playlist URLs
  - `variants.html`: Display available stream variants for master playlists
  - `result.html`: Show detailed segment analysis with charts
- `requirements.txt`: Python dependencies

## Key Features
- Parse HLS master and media playlists
- Extract video information using ffprobe
- Check HTTP status of segments
- Display resolution and frame rate charts using Chart.js
- Support for both master playlist variant selection and direct media playlist analysis

## Dependencies
- Flask: Web framework
- m3u8: HLS playlist parsing
- requests: HTTP requests
- ffprobe: Video analysis (requires FFmpeg installation)

## Coding Guidelines
- Use proper error handling for network requests and ffprobe calls
- Include timeout values for external requests
- Validate URLs before processing
- Handle both master playlists (with variants) and media playlists
- Use Chart.js for data visualization in the frontend
