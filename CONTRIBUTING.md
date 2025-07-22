# Contributing to Live HLS Stream Monitor

Thank you for your interest in contributing to Live HLS Stream Monitor! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, please include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, FFmpeg version)
- **Sample HLS URLs** that demonstrate the issue (if applicable)
- **Error messages** or logs

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear description** of the enhancement
- **Use cases** that would benefit from this feature
- **Possible implementation approach** (if you have ideas)

### Pull Requests

1. **Fork** the repository
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the coding guidelines below
4. **Test your changes** thoroughly
5. **Commit your changes** with clear commit messages
6. **Push** to your fork and **submit a pull request**

## Development Guidelines

### Code Style

- Follow **PEP 8** Python style guidelines
- Use **meaningful variable and function names**
- Add **docstrings** for functions and classes
- Keep functions **focused and concise**
- Use **type hints** where appropriate

### Testing

- Test your changes with various HLS stream types:
  - Master playlists with multiple variants
  - Direct media playlists
  - Live streams vs VOD
  - HTTP and HTTPS streams
- Ensure **error handling** works correctly
- Test with and without **FFmpeg/FFprobe** installed
- Verify **cross-platform compatibility** when possible
- **Privacy compliance**: Ensure no data is stored or transmitted unnecessarily

### Documentation

- Update **README.md** if adding new features
- Add **inline comments** for complex logic
- Update **API documentation** for new endpoints
- Include **example usage** for new features

## Project Structure

```
live-hls-stream-monitor/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── index.html        # Main dashboard
│   ├── live.html         # Live monitoring interface
│   └── ...
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── ...
```

## Key Components

- **Flask Routes**: Handle web requests and API endpoints
- **HLS Analysis**: Parse playlists and extract stream information
- **FFprobe Integration**: Media analysis using external tools
- **Real-time Updates**: JavaScript for live dashboard updates
- **System Metrics**: Optional system performance monitoring

## Setting Up Development Environment

1. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/live-hls-stream-monitor.git
   cd live-hls-stream-monitor
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install psutil  # Optional for system metrics
   ```

4. **Install FFmpeg** for full functionality:
   - Windows: `choco install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

5. **Run the application**:
   ```bash
   python app.py
   ```

## Areas for Contribution

### High Priority
- **Performance optimization** for large playlists
- **Additional audio/video codec support**
- **Enhanced error handling** and user feedback
- **Mobile responsiveness** improvements

### Medium Priority
- **Export functionality** for metrics data
- **Custom dashboard layouts**
- **Stream comparison tools**
- **Automated testing suite**

### Low Priority
- **Docker containerization**
- **Configuration file support**
- **Plugin system** for custom analyzers
- **Internationalization** (i18n)

## Questions?

If you have questions about contributing:
- Open an **issue** for discussion
- Check existing **issues** and **pull requests**
- Review the **project documentation**

Thank you for contributing to Live HLS Stream Monitor! 🎉
