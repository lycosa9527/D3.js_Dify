# MindGraph - AI-Powered Data Visualization Generator

[![Version](https://img.shields.io/badge/version-2.4.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![D3.js](https://img.shields.io/badge/D3.js-7.0+-orange.svg)](https://d3js.org/)
[![License](https://img.shields.io/badge/License-AGPLv3-red.svg)](LICENSE)
[![WakaTime](https://wakatime.com/badge/user/60ba0518-3829-457f-ae10-3eff184d5f69/project/a278db63-dcfb-4dae-b731-330443000199.svg)](https://wakatime.com/badge/user/60ba0518-3829-457f-ae10-3eff184d5f69/project/a278db63-dcfb-4dae-b731-330443000199)

## 🎯 What is MindGraph?

**MindGraph** is an intelligent data visualization platform that automatically generates interactive charts and graphs from natural language descriptions. Powered by AI and D3.js, it transforms your ideas into beautiful, interactive visualizations in seconds.

### ✨ Key Features

- **🤖 AI-Powered**: Understands natural language and selects the best diagram type automatically
- **🏗️ Multi-Agent Architecture**: 6 specialized agents working together for optimal results
- **🧠 Complete Diagram System**: All core diagram types are now fully developed and production-ready
- **🎨 Advanced Theming**: Modern themes via centralized style manager with easy customization
- **🌐 Interactive**: Smooth D3.js interactions (hover, zoom/pan) and instant style updates
- **📱 Export Options**: PNG export and shareable interactive HTML
- **🌍 Multi-language**: English and Chinese support
- **⚡ Real-time**: Instant preview and fast PNG generation

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js (for D3.js components)
- Modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lycosa9527/MindGraph.git
   cd MindGraph
   ```

2. **Install Python dependencies**
   
   **Option 1: Full Installation (Recommended for Development)**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Option 2: Production Only (Minimal Dependencies)**
   ```bash
   pip install Flask>=3.1.1 langchain>=0.3.27 playwright>=1.45.0 Pillow>=10.4.0 requests>=2.32.0 aiohttp>=3.9.0 PyYAML>=6.0.1 python-dotenv>=1.0.1 nest_asyncio>=1.6.0 pyee>=13.0.0 psutil>=6.0.0 typing-extensions>=4.12.0 pydantic>=2.10.0 structlog>=24.1.0 cryptography>=42.0.0
   ```
   
   **Option 3: Minimal Core (Basic Functionality)**
   ```bash
   pip install Flask langchain playwright Pillow
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```
   
   **Required Configuration:**
   - `QWEN_API_KEY` - Required for core functionality

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:9527/debug` to access the web interface.

## 🎨 Supported Diagram Types

### 🧠 Thinking Maps® (Complete Coverage)
- **Bubble Map**: For defining concepts and their characteristics
- **Circle Map**: For brainstorming and defining in context
- **Double Bubble Map**: For comparing and contrasting concepts
- **Brace Map**: For part-whole relationships and hierarchies
- **Flow Map**: For processes and sequences
- **Multi-Flow Map**: For complex processes with multiple flows
- **Bridge Map**: For analogies and relationships

### 🌳 Mind Maps (Enhanced with Clockwise Positioning)
- **Revolutionary Clockwise System**: Branches distributed in perfect clockwise order
- **Smart Branch Alignment**: Branch 2 and 5 automatically align with central topic
- **Perfect Left/Right Balance**: Even distribution between left and right sides
- **Children-First Positioning**: Maintains proven positioning system
- **Scalable Layout**: Works perfectly for 4, 6, 8, 10+ branches

### 🔗 Concept Maps
- **Radial Layout**: Optimized spacing with larger starting radius
- **Enhanced Readability**: Improved font sizes and text wrapping
- **Professional Appearance**: Clean, organized layouts suitable for business use

### 📊 Traditional Charts
- **Tree Maps**: Hierarchical data visualization with rectangle nodes
- **Flow Charts**: Process visualization with step-by-step flow
- **Custom Visualizations**: AI-generated charts based on your descriptions

## 🏗️ Architecture Overview

### Multi-Agent System
MindGraph uses a sophisticated multi-agent architecture where specialized agents handle different aspects of diagram generation:

1. **Qwen Agent**: Primary LLM for natural language understanding
2. **DeepSeek Agent**: Alternative LLM for enhanced reasoning
3. **Brace Map Agent**: Specialized in hierarchical relationships
4. **Flow Map Agent**: Expert in process and sequence visualization
5. **Multi-Flow Map Agent**: Handles complex multi-process flows
6. **Tree Map Agent**: Manages hierarchical tree structures

### Core Components
- **Flask Web Server**: RESTful API and web interface
- **D3.js Renderer**: Interactive visualization engine
- **Style Manager**: Centralized theming and customization
- **Memory System**: User preference tracking and learning

## 🎯 How It Works

### 1. Natural Language Input
Simply describe what you want to visualize:
- "Compare cats and dogs"
- "Define artificial intelligence"
- "Show the relationship between cause and effect"
- "Create a mind map about climate change"

### 2. AI Analysis
The AI:
- Analyzes your request
- Determines the best chart type
- Extracts relevant data characteristics
- Generates appropriate sample data

### 3. Chart Generation
D3.js creates an interactive visualization with:
- Responsive design
- Interactive elements
- Professional styling
- Export capabilities

## 🔧 API Reference

### Main Endpoints

#### Generate Diagram
```http
POST /api/generate_graph
Content-Type: application/json

{
  "prompt": "Create a mind map about artificial intelligence",
  "language": "en"
}
```

#### Generate PNG
```http
POST /api/generate_png
Content-Type: application/json

{
  "prompt": "Create a mind map about artificial intelligence",
  "language": "en"
}
```

#### Style Management
```http
POST /api/update_style
Content-Type: application/json

{
  "theme": "dark",
  "primary_color": "#1976d2",
  "font_size": 14
}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "html": "<div>...</div>",
    "dimensions": {
      "width": 1200,
      "height": 800
    },
    "metadata": {
      "diagram_type": "mindmap",
      "algorithm": "clean_vertical_stack"
    }
  }
}
```

## 🎨 Customization & Theming

### Style Manager
MindGraph includes a powerful style manager that allows you to:
- Change color themes (light/dark)
- Customize primary colors
- Adjust font sizes and families
- Modify border radius and stroke widths
- Apply custom CSS overrides

### Theme Configuration
```javascript
// Example theme configuration
const theme = {
  background: '#ffffff',
  primaryColor: '#1976d2',
  fontSize: 14,
  fontFamily: 'Inter, sans-serif',
  borderRadius: 4,
  strokeWidth: 2
};
```

## 🚀 Performance & Optimization

### Rendering Performance
- **Optimized Algorithms**: Streamlined positioning and layout calculations
- **Memory Efficiency**: Better resource usage in complex operations
- **Fast Generation**: Quick diagram creation even for complex layouts

### Canvas Optimization
- **Content-Based Sizing**: Canvas dimensions calculated from actual content
- **Adaptive Spacing**: Intelligent spacing that responds to content complexity
- **Zero Overlapping**: Advanced algorithms prevent element conflicts

## 🔍 Troubleshooting

### Common Issues

#### API Key Configuration
- Ensure `QWEN_API_KEY` is set in your `.env` file
- Check API key validity and quota limits

#### Rendering Issues
- Clear browser cache and refresh
- Check browser console for JavaScript errors
- Verify D3.js is loading correctly

#### Performance Issues
- Use minimal installation for production
- Monitor memory usage for large diagrams
- Consider reducing diagram complexity

### Getting Help
- Check the [CHANGELOG.md](CHANGELOG.md) for recent updates
- Review browser console for error messages
- Ensure all dependencies are properly installed

## 📈 Version History

### Version 2.4.0 (Current)
- **Complete Diagram System**: All core diagram types finished
- **Revolutionary Mind Map Positioning**: Clockwise system with perfect branch alignment
- **Production Ready**: Enterprise-grade system suitable for business use
- **Enhanced Performance**: Optimized algorithms and improved stability

### Previous Versions
See [CHANGELOG.md](CHANGELOG.md) for complete version history and detailed change logs.

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and code of conduct.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the AGPLv3 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **D3.js Community**: For the amazing visualization library
- **Qwen & DeepSeek Teams**: For powerful AI models
- **Open Source Contributors**: For making this project possible

## 📞 Support

- **Documentation**: This README and [CHANGELOG.md](CHANGELOG.md)
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions on GitHub

---

**MindGraph** - Transforming ideas into beautiful visualizations, one prompt at a time. 🚀