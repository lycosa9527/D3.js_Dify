# MindGraph Documentation

## 📚 **Documentation Index**

Welcome to the MindGraph documentation! This comprehensive guide covers everything you need to know about using, integrating, and troubleshooting MindGraph.

## 🚀 **Quick Start Guides**

### **[Installation Guide](../INSTALLATION.md)**
Complete setup instructions for different environments:
- **Full Installation** - Development environment with all tools
- **Production Only** - Minimal dependencies for deployment
- **Docker Setup** - Containerized deployment
- **Troubleshooting** - Common setup issues

### **[API Reference](API_REFERENCE.md)**
Complete API documentation for developers:
- **Endpoints** - All available API calls
- **Request/Response** - Data formats and examples
- **Authentication** - API key setup
- **Integration** - Code examples in multiple languages
- **Error Handling** - Status codes and troubleshooting

## 🔗 **Integration Guides**

### **[Dify Integration](DIFY_INTEGRATION.md)**
Step-by-step guide for integrating MindGraph with Dify:
- **Quick Setup** - Get running in 5 minutes
- **Workflow Configuration** - Complete Dify setup
- **Advanced Customization** - Themes, languages, styling
- **Testing & Troubleshooting** - Common integration issues
- **Production Deployment** - Scaling and optimization

### **[API Integration Examples](API_REFERENCE.md#integration-examples)**
Code examples for popular platforms:
- **Python** - Requests library examples
- **JavaScript/Node.js** - Axios integration
- **cURL** - Command-line testing
- **Webhook Setup** - Platform integration

## 🛠️ **Development & Deployment**

### **[Agent Architecture](../docs/AGENT_ARCHITECTURE_COMPREHENSIVE.md)**
Deep dive into MindGraph's AI architecture:
- **Multi-Agent System** - How agents work together
- **LLM Integration** - Qwen and DeepSeek integration
- **Workflow Management** - Request processing pipeline
- **Customization** - Extending agent capabilities

### **[Enhanced Brace Map Documentation](../docs/ENHANCED_BRACE_MAP_DOCUMENTATION.md)**
Specialized documentation for brace map features:
- **Layout Algorithms** - Dynamic positioning
- **Collision Detection** - Preventing overlaps
- **Styling Options** - Visual customization
- **Performance Optimization** - Rendering improvements

### **[Docker Deployment](../docker/README.md)**
Containerized deployment guide:
- **Dockerfile** - Image building
- **Docker Compose** - Multi-service setup
- **Environment Configuration** - Production settings
- **Health Checks** - Monitoring and alerts

## 📊 **Feature Guides**

### **Visualization Types**
Comprehensive coverage of supported chart types:

#### **Thinking Maps (Educational)**
- **Bubble Map** - Central topic with attributes
- **Circle Map** - Topic definition in context
- **Double Bubble Map** - Comparison charts
- **Brace Map** - Whole-to-part relationships
- **Flow Map** - Process sequences
- **Multi-Flow Map** - Cause and effect
- **Bridge Map** - Analogical relationships

#### **Traditional Charts**
- **Bar Charts** - Category comparisons
- **Line Charts** - Time series data
- **Pie Charts** - Proportions and percentages
- **Scatter Plots** - Correlations
- **Area Charts** - Cumulative data
- **Heatmaps** - Matrix visualizations
- **Tree Maps** - Hierarchical data
- **Network Graphs** - Relationship mapping

### **Styling & Customization**
- **Theme System** - Pre-built visual themes
- **Color Management** - Custom color schemes
- **Typography** - Font sizes and styles
- **Layout Options** - Positioning and spacing
- **Export Formats** - PNG and interactive HTML

## 🔧 **Troubleshooting & Support**

### **[Troubleshooting Guide](TROUBLESHOOTING.md)**
Comprehensive problem-solving guide:
- **Quick Diagnosis** - Fast problem identification
- **Common Issues** - Solutions for frequent problems
- **Debugging Techniques** - Advanced troubleshooting
- **Performance Monitoring** - System optimization
- **Getting Help** - Community resources

### **Common Problem Areas**
- **Server Startup** - Port conflicts, dependencies
- **PNG Generation** - Playwright issues, memory problems
- **API Authentication** - Key configuration, service availability
- **Performance** - Slow responses, resource usage
- **Integration** - Webhook failures, CORS issues
- **Docker** - Container building, networking

## 📖 **API Reference Details**

### **Core Endpoints**
- **`POST /generate_png`** - PNG image generation
- **`POST /generate_graph`** - Interactive visualization data
- **`GET /status`** - Health check and system info

### **Request Parameters**
- **`prompt`** - Natural language description (required)
- **`language`** - Language code: `en` or `zh`
- **`style`** - Visual customization options

### **Response Formats**
- **PNG Images** - Binary image data
- **JSON Data** - Structured visualization information
- **Error Responses** - Detailed error information

### **Authentication**
- **API Keys** - Qwen and DeepSeek integration
- **Environment Variables** - Configuration setup
- **Security** - Production deployment considerations

## 🌐 **Platform Integration**

### **Supported Platforms**
- **Dify** - Complete workflow integration
- **Chatbots** - Natural language processing
- **Web Applications** - RESTful API integration
- **Mobile Apps** - Cross-platform compatibility
- **Desktop Tools** - Local integration options

### **Integration Patterns**
- **Webhook Integration** - Push-based workflows
- **API Integration** - Pull-based requests
- **Real-time Processing** - Live visualization generation
- **Batch Processing** - Multiple request handling

## 📈 **Performance & Scaling**

### **Performance Metrics**
- **Response Times** - 2-30 seconds depending on complexity
- **Throughput** - 100+ requests per minute
- **Resource Usage** - Memory and CPU optimization
- **Caching** - Response optimization strategies

### **Scaling Strategies**
- **Horizontal Scaling** - Multiple instances
- **Load Balancing** - Request distribution
- **Resource Management** - Memory and CPU optimization
- **Monitoring** - Performance tracking and alerts

## 🔒 **Security & Best Practices**

### **Security Considerations**
- **API Key Management** - Secure key storage
- **Input Validation** - Prompt sanitization
- **Rate Limiting** - Abuse prevention
- **HTTPS** - Production encryption

### **Best Practices**
- **Prompt Engineering** - Effective visualization requests
- **Error Handling** - Graceful failure management
- **Monitoring** - System health tracking
- **Backup** - Configuration and data protection

## 📞 **Getting Help**

### **Self-Service Resources**
- **Documentation** - This comprehensive guide
- **Troubleshooting** - Problem-solving guide
- **API Reference** - Technical specifications
- **Examples** - Integration code samples

### **Community Support**
- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - Questions and community help
- **Contributing** - How to contribute to the project

### **Contact Information**
- **Repository**: [GitHub Repository](https://github.com/your-repo/MindGraph)
- **Issues**: [Bug Reports](https://github.com/your-repo/MindGraph/issues)
- **Discussions**: [Community Help](https://github.com/your-repo/MindGraph/discussions)

## 📝 **Documentation Updates**

### **Version History**
- **v2.4.0** - Comprehensive API documentation, Dify integration guide
- **v2.3.8** - Enhanced troubleshooting, performance optimization
- **v2.3.7** - Agent architecture documentation, brace map features

### **Contributing to Docs**
We welcome documentation improvements! To contribute:
1. Fork the repository
2. Make your changes
3. Submit a pull request
4. Include clear descriptions of your changes

---

**Need help getting started?** Begin with the [Installation Guide](../INSTALLATION.md) or jump straight to [Dify Integration](DIFY_INTEGRATION.md) if you're integrating with Dify.

**Looking for technical details?** Check the [API Reference](API_REFERENCE.md) for complete endpoint documentation.

**Having problems?** Start with the [Troubleshooting Guide](TROUBLESHOOTING.md) for common solutions.
