# Dify Integration Guide

## Overview

This guide shows you how to integrate MindGraph with Dify to automatically generate PNG visualizations from user prompts. Users can describe what they want to visualize in natural language, and Dify will return a professional PNG image.

## 🎯 **What You'll Achieve**

- **User Input**: "Compare cats and dogs"
- **Dify Processing**: Sends request to MindGraph API
- **MindGraph**: Generates PNG visualization
- **Result**: User receives a beautiful comparison chart

## 🚀 **Quick Setup (5 minutes)**

### **Step 1: Start MindGraph Server**

```bash
# Clone and setup
git clone https://github.com/your-repo/MindGraph.git
cd MindGraph

# Install dependencies
pip install -r requirements.txt

# Set your API key
export QWEN_API_KEY="your_qwen_api_key_here"

# Start server
python app.py
```

**Server will be available at**: `http://localhost:9527`

### **Step 2: Test the API**

```bash
# Test PNG generation
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare cats and dogs", "language": "en"}' \
  --output test.png
```

If you get a PNG file, the API is working! 🎉

## 🔧 **Dify Configuration**

### **1. Create New Workflow**

1. Open Dify and create a new workflow
2. Add a **User Input** node for the prompt
3. Add a **Webhook** node for MindGraph API
4. Add a **Response** node to return the image

### **2. Configure Webhook Node**

**Basic Settings:**
- **Name**: `MindGraph PNG Generator`
- **URL**: `http://your-server:9527/generate_png`
- **Method**: `POST`
- **Timeout**: `60 seconds`

**Headers:**
```
Content-Type: application/json
```

**Request Body Template:**
```json
{
  "prompt": "{{user_input}}",
  "language": "en",
  "style": {
    "theme": "modern"
  }
}
```

**Response Handling:**
- **Response Type**: `Binary`
- **Save Response**: `Yes`
- **Variable Name**: `generated_image`

### **3. Configure Response Node**

**Response Content:**
```
I've generated a visualization for you: "{{user_input}}"

![Generated Chart]({{generated_image}})
```

**Response Type**: `Markdown`

## 📋 **Complete Workflow Example**

### **Workflow Structure**

```
User Input → Webhook (MindGraph) → Response
```

### **Node 1: User Input**
- **Variable Name**: `user_input`
- **Description**: `What would you like to visualize?`
- **Type**: `Text`

### **Node 2: Webhook (MindGraph)**
- **URL**: `http://localhost:9527/generate_png`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**: 
```json
{
  "prompt": "{{user_input}}",
  "language": "en",
  "style": {
    "theme": "modern"
  }
}
```

### **Node 3: Response**
- **Content**: 
```
Perfect! I've created a visualization for: "{{user_input}}"

![Generated Chart]({{generated_image}})

The chart shows the key differences and similarities you requested. You can download this image or ask me to create another visualization with different styling.
```

## 🎨 **Advanced Customization**

### **1. Dynamic Language Detection**

**Add Language Detection Node:**
```json
{
  "prompt": "{{user_input}}",
  "language": "{{detected_language}}",
  "style": {
    "theme": "{{selected_theme}}"
  }
}
```

### **2. Theme Selection**

**Add Theme Selection Node:**
```json
{
  "prompt": "{{user_input}}",
  "language": "{{language}}",
  "style": {
    "theme": "{{theme_choice}}",
    "colors": {
      "primary": "{{primary_color}}",
      "secondary": "{{secondary_color}}"
    }
  }
}
```

### **3. Chart Type Specification**

**Enhanced Prompt Processing:**
```json
{
  "prompt": "Create a {{chart_type}} showing {{user_input}}",
  "language": "{{language}}",
  "style": {
    "theme": "{{theme}}"
  }
}
```

## 🔍 **Testing Your Integration**

### **Test Cases**

1. **Simple Comparison**
   - Input: "Compare cats and dogs"
   - Expected: Double bubble map

2. **Process Description**
   - Input: "How to make coffee"
   - Expected: Flow map

3. **Concept Definition**
   - Input: "What is artificial intelligence?"
   - Expected: Bubble map

4. **Cause and Effect**
   - Input: "Effects of climate change"
   - Expected: Multi-flow map

### **Troubleshooting**

**If PNG generation fails:**
```bash
# Check server status
curl http://localhost:9527/status

# Check logs
tail -f logs/app.log

# Verify Playwright
python -m playwright install chromium
```

**If Dify webhook fails:**
- Check URL accessibility
- Verify timeout settings
- Check response handling configuration

## 📱 **User Experience Examples**

### **Example 1: Educational Use**

**User**: "I need a chart to compare traditional and modern education methods"

**Dify Response**: 
```
I've created a comprehensive comparison chart for you!

![Education Comparison](generated_image)

This double bubble map shows:
- **Traditional Education**: Classroom-based, fixed curriculum, teacher-centered
- **Modern Education**: Technology-integrated, flexible learning, student-centered
- **Shared Elements**: Knowledge transfer, assessment, skill development

The chart clearly highlights the differences and commonalities between these approaches.
```

### **Example 2: Business Analysis**

**User**: "Show me the relationship between marketing spend and sales growth"

**Dify Response**:
```
Here's a visualization of the marketing spend vs. sales growth relationship:

![Marketing Analysis](generated_image)

This flow map illustrates:
- **Input**: Marketing budget allocation
- **Process**: Campaign execution and customer engagement
- **Output**: Sales growth and revenue increase
- **Feedback Loop**: Performance data informing future strategies

The visualization shows how marketing investments flow through to business outcomes.
```

## 🚀 **Production Deployment**

### **1. Server Deployment**

```bash
# Using Docker (recommended)
cd docker
docker-compose up -d

# Or direct deployment
pip install -r requirements-production.txt
python app.py --host 0.0.0.0 --port 9527
```

### **2. Environment Variables**

```bash
# Required
export QWEN_API_KEY="your_production_key"

# Optional
export DEEPSEEK_API_KEY="your_deepseek_key"
export DEBUG=False
export HOST=0.0.0.0
export PORT=9527
```

### **3. Security Considerations**

- Use HTTPS in production
- Implement API key rotation
- Set up rate limiting
- Monitor API usage

## 📊 **Performance Optimization**

### **1. Caching Strategy**

- Cache common visualizations
- Implement client-side caching
- Use CDN for image delivery

### **2. Response Time**

- **Simple charts**: 2-5 seconds
- **Complex visualizations**: 5-15 seconds
- **Large datasets**: 15-30 seconds

### **3. Scaling Tips**

- Use multiple MindGraph instances
- Implement load balancing
- Monitor resource usage

## 🔗 **Useful Links**

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Installation Guide](../INSTALLATION.md)** - Setup instructions
- **[Main Documentation](../README.md)** - Project overview
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 💡 **Pro Tips**

1. **Prompt Engineering**: Be specific about what you want to visualize
2. **Theme Consistency**: Use consistent themes across related charts
3. **Language Support**: Leverage multi-language capabilities for global users
4. **Error Handling**: Always provide fallback responses if generation fails
5. **User Feedback**: Collect feedback to improve prompt suggestions

## 🎉 **Congratulations!**

You've successfully integrated MindGraph with Dify! Users can now:

- Describe visualizations in natural language
- Receive professional PNG charts instantly
- Download and share generated images
- Create consistent, branded visualizations

**Next Steps:**
- Test with real users
- Collect feedback and iterate
- Explore advanced customization options
- Scale your deployment

---

**Need Help?** Check the [troubleshooting guide](TROUBLESHOOTING.md) or open an issue on GitHub.
