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
- **🏗️ Multi-Agent Architecture**: 6 specialized agents (Qwen, DeepSeek, Brace Map, Flow Map, Multi-Flow Map, Tree Map) working together
- **🌳 Tree Map Enhancements (v2.3.7)**:
  - Rectangle nodes for branches and children
  - Width-adaptive nodes using precise SVG text measurement
  - Vertical stacking with straight connectors (branch → child → child)
  - Auto-sizing canvas that expands to fit content
- **🧠 Educational Focus**: Complete Thinking Maps® coverage (Bubble, Circle, Double Bubble, Brace, Flow, Multi-Flow, Bridge)
- **📊 More Diagrams**: Concept maps, mind maps, and traditional charts
- **🎨 Theming**: Modern themes via centralized style manager; easy color and typography overrides
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
   
   See [INSTALLATION.md](INSTALLATION.md) for detailed installation options.

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

## 🎨 How It Works

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
- Smooth animations
- Interactive tooltips
- Zoom and pan capabilities

### 4. Export & Share
Export your charts as:
- Interactive HTML files
- High-resolution PNG images

## 🏗️ Agent Architecture

MindGraph v2.3.7 features a sophisticated multi-agent system with 6 specialized agents and enhanced brace map layout optimization:

### 🤖 Agent System Overview

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Main Agent** | Central Coordinator | Orchestrates entire workflow, manages other agents |
| **Qwen LLM Agent** | Primary AI Processor | Handles classification, topic extraction, spec generation |
| **DeepSeek Agent** | Development Tool | Creates enhanced prompts for educational context |
| **Brace Map Agent** | Specialized Diagram Agent | Dynamic positioning, layout algorithms, collision detection |
| **Agent Utils** | Utility Functions | Topic extraction, characteristics generation, language detection |
| **LLM Clients** | API Interfaces | Async interfaces for DeepSeek and Qwen APIs |

### 🧠 Intelligent Features

- **Dynamic Positioning**: Content-aware algorithms that adapt to actual data structure
- **Hybrid LLM + Python**: Combines AI intelligence with deterministic algorithms
- **Context Management**: User preference storage and session management
- **Collision Detection**: Advanced algorithms to prevent overlapping elements
- **Multi-Language Support**: Seamless Chinese and English processing

### 📋 Agent Workflow

1. **User Input** → Main Agent receives and validates request
2. **AI Analysis** → Qwen LLM Agent classifies diagram type and extracts topics
3. **Algorithm Selection** → Brace Map Agent chooses optimal layout algorithm
4. **Dynamic Positioning** → Content-aware positioning with collision detection
5. **SVG Generation** → D3.js compatible SVG data creation
6. **Export Options** → PNG or interactive HTML output

## 📊 Supported Chart Types

### 🧠 Thinking Maps® (Educational Diagrams)

| Chart Type | Description | Best For |
|------------|-------------|----------|
| **Bubble Map** | Central topic with connected attributes | Describing characteristics of a single topic |
| **Circle Map** | Outer boundary with central topic and perimeter context | Defining topics in context |
| **Double Bubble Map** | Two topics with shared and unique characteristics | Comparing and contrasting two topics |
| **Bridge Map** | Analogical relationships with relating factors | Showing analogies and similarities |

### 📈 Traditional Charts

| Chart Type | Description | Best For |
|------------|-------------|----------|
| **Bar Chart** | Vertical or horizontal bars | Comparing categories |
| **Line Chart** | Connected data points | Trends over time |
| **Pie Chart** | Circular segments | Proportions and percentages |
| **Scatter Plot** | Points on X-Y axes | Correlations and distributions |
| **Area Chart** | Filled areas under lines | Cumulative data over time |
| **Heatmap** | Color-coded grid | Matrix data visualization |
| **Tree Map** | Nested rectangles | Hierarchical data |
| **Network Graph** | Connected nodes | Relationships and connections |

## 🎨 Example Prompts

Try these prompts to get started:

- "Compare cats and dogs"
- "Define artificial intelligence"
- "Show the relationship between cause and effect"
- "Create a mind map about climate change"
- "Compare traditional and modern education"

## 🔧 API Usage

### Generate Chart from Text

```bash
curl -X POST http://localhost:9527/generate_graph \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Compare cats and dogs",
    "language": "en"
  }'
```

### Export as PNG

```bash
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show monthly revenue trends",
    "language": "en"
  }'
```

## 🐳 Docker Deployment

### Quick Docker Setup

```bash
# Build and run with Docker Compose
cd docker
docker-compose up -d

# Or build manually
docker build -t mindgraph .
docker run -p 9527:9527 mindgraph
```

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running in minutes
- **[Agent Architecture](docs/AGENT_ARCHITECTURE_COMPREHENSIVE.md)** - Complete agent system documentation
- **[Thinking Maps Guide](docs/THINKING_MAPS_GUIDE.md)** - Learn about Thinking Maps®
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Complete Documentation](docs/README.md)** - Full documentation index

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/lycosa9527/MindGraph/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lycosa9527/MindGraph/discussions)

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3) - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by the MindSpring Team**

Transform your ideas into beautiful visualizations with the power of AI! 🚀