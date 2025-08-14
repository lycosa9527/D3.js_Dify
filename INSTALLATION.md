# MindGraph Installation Guide

## Quick Start

### Option 1: Full Installation (Recommended for Development)
```bash
pip install -r requirements.txt
```

### Option 2: Production Only (Minimal Dependencies)
```bash
pip install Flask>=3.1.1 langchain>=0.3.27 playwright>=1.45.0 Pillow>=10.4.0 requests>=2.32.0 aiohttp>=3.9.0 PyYAML>=6.0.1 python-dotenv>=1.0.1 nest_asyncio>=1.6.0 pyee>=13.0.0 psutil>=6.0.0 typing-extensions>=4.12.0 pydantic>=2.10.0 structlog>=24.1.0 cryptography>=42.0.0
```

### Option 3: Minimal Core (Basic Functionality)
```bash
pip install Flask langchain playwright Pillow
```

## Using npm Scripts

If you have Node.js installed, you can use the npm scripts:

```bash
# Install all dependencies (development + production)
npm run install-deps

# Install production dependencies only
npm run install-prod

# Install minimal core dependencies
npm run install-minimal
```

## Docker Installation

For Docker deployment, the Dockerfile automatically installs only production dependencies:

```bash
docker build -t mindgraph .
```

## Requirements File Structure

The `requirements.txt` file is organized into sections:

- **Core Dependencies**: Required for production
- **Development Dependencies**: Optional for development/testing
- **Installation Notes**: Different installation options

## Python Version Compatibility

- **Minimum**: Python 3.8+
- **Tested**: Python 3.13.5
- **Recommended**: Python 3.11+

## Node.js Requirements

- **Minimum**: Node.js 18.19+
- **Recommended**: Node.js 20+ (LTS)

## Post-Installation

After installing dependencies, you may need to:

1. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

2. Set up environment variables (see `.env.example`)

3. Run the application:
   ```bash
   python app.py
   ```

## Troubleshooting

### Common Issues

1. **Playwright Installation**: If you get Playwright errors, run:
   ```bash
   python -m playwright install
   ```

2. **Permission Errors**: On Linux/macOS, you may need:
   ```bash
   sudo pip install -r requirements.txt
   ```

3. **Version Conflicts**: If you have version conflicts:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

### Getting Help

- Check the logs in the `logs/` directory
- Run the dependency checker: `python dependency_checker/check_dependencies.py`
- Review the error messages for specific package issues
