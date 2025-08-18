# MindGraph API Reference

## Overview

MindGraph provides a RESTful API for generating AI-powered data visualizations from natural language prompts. The API supports both interactive graph generation and direct PNG export, making it ideal for integration with platforms like Dify, chatbots, and web applications.

**Base URL**: `http://localhost:9527` (or your deployed server URL)

**API Version**: 2.4.0

**Endpoint Compatibility**: Both `/endpoint` and `/api/endpoint` formats are supported for backward compatibility.

## Authentication

Currently, the API uses API key authentication through environment variables:

- **QWEN_API_KEY**: Required for core functionality
- **DEEPSEEK_API_KEY**: Optional for enhanced features

## Endpoints

### 1. PNG Generation (Primary Endpoint)

Generates a PNG image directly from a text prompt.

```http
POST /generate_png
POST /api/generate_png
```

**Note**: Both endpoints are supported for backward compatibility. The `/api/generate_png` endpoint is the primary one.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "prompt": "Compare cats and dogs",
  "language": "en",
  "style": {
    "theme": "modern",
    "colors": {
      "primary": "#4e79a7",
      "secondary": "#f28e2c"
    }
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | ✅ | Natural language description of what to visualize |
| `language` | string | ❌ | Language code (`en` or `zh`). Defaults to `en` |
| `style` | object | ❌ | Visual styling options |

#### Default Values

When parameters are omitted, MindGraph automatically applies sensible defaults:

- **`language`**: Defaults to `"en"` (English) if not specified
- **`style`**: Uses professional default theme and color scheme if not specified
- **`prompt`**: **Required** - cannot be omitted or left blank

#### Style Options

```json
{
  "theme": "modern|classic|minimal|dark|light",
  "colors": {
    "primary": "#hexcolor",
    "secondary": "#hexcolor",
    "background": "#hexcolor"
  },
  "fontSize": {
    "title": 18,
    "subtitle": 14,
    "body": 12
  }
}
```

#### Default Style Configuration

When no style is specified, MindGraph automatically applies:

```json
{
  "theme": "modern",
  "colors": {
    "primary": "#4e79a7",
    "secondary": "#f28e2c",
    "background": "#ffffff"
  },
  "fontSize": {
    "title": 18,
    "subtitle": 14,
    "body": 12
  }
}
```

#### Response

**Success (200):**
- **Content-Type**: `image/png`
- **Body**: PNG image data

**Error (400/500):**
```json
{
  "error": "Error description",
```

### 2. Cache Management

#### Clear Cache Endpoint

Clears the modular JavaScript cache for development and debugging purposes.

```http
POST /api/clear_cache
```

**Note**: This endpoint is primarily for development use to clear cached JavaScript modules.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:** Empty (no body required)

#### Response

**Success (200):**
```json
{
  "status": "success",
  "message": "Cache cleared successfully"
}
```

**Error (500):**
```json
{
  "status": "error",
  "message": "Error description"
}
```

#### Use Cases

- **Development**: Clear cache when making changes to JavaScript modules
- **Debugging**: Reset cache state when troubleshooting rendering issues
- **Testing**: Ensure fresh module loading for testing scenarios
  "status": "error",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Example Usage

```bash
# Basic PNG generation (minimal request - uses all defaults)
# Both endpoints work:
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare cats and dogs"}' \
  --output comparison.png

# Or use the primary API endpoint:
curl -X POST http://localhost:9527/api/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare cats and dogs"}' \
  --output comparison.png

# With language specification
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare cats and dogs", "language": "zh"}' \
  --output comparison_zh.png

# With custom styling
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a mind map about artificial intelligence",
    "language": "en",
    "style": {
      "theme": "modern",
      "colors": {
        "primary": "#4e79a7",
        "secondary": "#f28e2c"
      }
    }
  }' \
  --output ai_mindmap.png
```

#### Request Body Examples (From Simple to Complex)

**Level 1: Minimal (Just Prompt)**
```json
{
  "prompt": "Compare cats and dogs"
}
```
✅ **Works perfectly** - Uses all defaults

**Level 2: With Language**
```json
{
  "prompt": "Compare cats and dogs",
  "language": "zh"
}
```
✅ **Works perfectly** - Uses default styling

**Level 3: With Basic Style**
```json
{
  "prompt": "Compare cats and dogs",
  "style": {
    "theme": "classic"
  }
}
```
✅ **Works perfectly** - Overrides theme, keeps other defaults

**Level 4: Full Customization**
```json
{
  "prompt": "Compare cats and dogs",
  "language": "en",
  "style": {
    "theme": "dark",
    "colors": {
      "primary": "#ff6b6b",
      "secondary": "#4ecdc4"
    }
  }
}
```
✅ **Full control** - Overrides all defaults

#### What NOT to Do

**❌ Invalid Requests**
```json
{
  "prompt": ""  // Empty prompt - will fail
}
```

```json
{
  "prompt": "Compare cats and dogs",
  "language": "fr"  // Unsupported language - will fail
}
```

```json
{
  "prompt": "Compare cats and dogs",
  "style": {
    "theme": "invalid_theme"  // Invalid theme - will use default
  }
}
```

#### Best Practices for Request Bodies

- **For Quick Testing**: Use minimal request with just `prompt`
- **For Production**: Include language detection and consistent theming
- **For Dify Integration**: `{"prompt": "{{user_input}}"}` works perfectly
- **Progressive Enhancement**: Start simple, add complexity as needed

### 2. Interactive Graph Generation

Generates an interactive D3.js visualization with JSON data.

```http
POST /generate_graph
POST /api/generate_graph
```

**Note**: Both endpoints are supported for backward compatibility. The `/api/generate_graph` endpoint is the primary one.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "prompt": "Compare traditional and modern education",
  "language": "en",
  "style": {
    "theme": "modern"
  }
}
```

#### Response

**Success (200):**
```json
{
  "status": "success",
  "data": {
    "type": "double_bubble_map",
    "svg_data": "...",
    "d3_config": {...},
    "metadata": {
      "prompt": "Compare traditional and modern education",
      "language": "en",
      "generated_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

### 3. Health Check

Returns application status and version information.

```http
GET /status
```

#### Response

```json
{
  "status": "healthy",
  "version": "2.4.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "qwen_api": "connected",
    "deepseek_api": "not_configured",
    "playwright": "ready"
  },
  "system": {
    "python_version": "3.13.5",
    "memory_usage": "45.2MB",
    "uptime": "2h 15m"
  }
}
```

## Integration Examples

### Dify Integration

#### 1. Webhook Configuration

In your Dify workflow, configure a webhook node:

- **URL**: `http://your-mindgraph-server:9527/generate_png`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`

#### 2. Request Body Template

```json
{
  "prompt": "{{user_input}}",
  "language": "{{detected_language}}",
  "style": {
    "theme": "{{selected_theme}}"
  }
}
```

#### 3. Response Handling

The webhook will receive a PNG image that you can:
- Display directly to the user
- Save to a file
- Send back through Dify's response

### Python Integration

```python
import requests
import json

def generate_png(prompt, language="en", style=None):
    url = "http://localhost:9527/generate_png"
    
    payload = {
        "prompt": prompt,
        "language": language
    }
    
    if style:
        payload["style"] = style
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        # Save PNG to file
        with open("generated_graph.png", "wb") as f:
            f.write(response.content)
        return "generated_graph.png"
    else:
        error = response.json()
        raise Exception(f"API Error: {error['error']}")

# Usage
try:
    filename = generate_png(
        prompt="Compare cats and dogs",
        language="en",
        style={"theme": "modern"}
    )
    print(f"Graph saved as: {filename}")
except Exception as e:
    print(f"Error: {e}")
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');
const fs = require('fs');

async function generatePNG(prompt, language = 'en', style = null) {
    try {
        const payload = {
            prompt: prompt,
            language: language
        };
        
        if (style) {
            payload.style = style;
        }
        
        const response = await axios.post('http://localhost:9527/generate_png', payload, {
            responseType: 'arraybuffer',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Save PNG to file
        fs.writeFileSync('generated_graph.png', response.data);
        return 'generated_graph.png';
        
    } catch (error) {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
    }
}

// Usage
generatePNG('Compare cats and dogs', 'en', { theme: 'modern' })
    .then(filename => console.log(`Graph saved as: ${filename}`))
    .catch(error => console.error('Error:', error));
```

## Supported Visualization Types

### Thinking Maps (Educational)

| Type | Description | Best For | Example Prompt |
|------|-------------|----------|----------------|
| **Bubble Map** | Central topic with connected attributes | Describing characteristics | "Define artificial intelligence" |
| **Circle Map** | Outer boundary with central topic | Defining topics in context | "What is climate change?" |
| **Double Bubble Map** | Two topics with shared/unique characteristics | Comparing and contrasting | "Compare cats and dogs" |
| **Brace Map** | Whole-to-part relationships | Breaking down concepts | "Parts of a computer" |
| **Flow Map** | Sequence of events | Processes and timelines | "How to make coffee" |
| **Multi-Flow Map** | Cause and effect relationships | Analyzing consequences | "Effects of climate change" |
| **Bridge Map** | Analogical relationships | Showing similarities | "Learning is like building" |

#### 🚀 Flow Map Enhancements (v2.3.9)

The Flow Map has received major improvements for optimal visual presentation:

**Ultra-Compact Layout Features:**
- **Revolutionary Positioning**: Substep-first algorithm eliminates all overlapping issues
- **Adaptive Spacing**: Canvas dimensions automatically adjust to content
- **75% Title Spacing Reduction**: Minimal spacing around topic text for maximum content density
- **Professional Design**: Clean, compact layout without sacrificing readability

**Enhanced Flow Map Structure:**
- **Main Steps**: Sequential process steps positioned vertically
- **Substeps**: Sub-processes connected to main steps with L-shaped connectors
- **Adaptive Canvas**: Automatically sized to fit all content perfectly
- **Smart Positioning**: Substeps positioned first, then main steps align to their groups

**Example Flow Map Prompt:**
```json
{
  "prompt": "制作咖啡的流程图",
  "language": "zh"
}
```

**Flow Map JSON Structure:**
```json
{
  "title": "制作咖啡",
  "steps": ["准备材料", "加热水", "冲泡", "享用"],
  "substeps": [
    {"step": "准备材料", "substeps": ["咖啡豆", "过滤纸", "咖啡杯"]},
    {"step": "加热水", "substeps": ["烧开水", "调节温度"]},
    {"step": "冲泡", "substeps": ["湿润过滤纸", "倒入咖啡粉", "缓慢注水"]},
    {"step": "享用", "substeps": ["品尝", "清洗器具"]}
  ]
}
```

### Traditional Charts

| Type | Description | Best For | Example Prompt |
|------|-------------|----------|----------------|
| **Bar Chart** | Vertical/horizontal bars | Comparing categories | "Sales by region" |
| **Line Chart** | Connected data points | Trends over time | "Monthly revenue trends" |
| **Pie Chart** | Circular segments | Proportions and percentages | "Market share distribution" |
| **Scatter Plot** | Points on X-Y axes | Correlations and distributions | "Height vs weight correlation" |
| **Area Chart** | Filled areas under lines | Cumulative data over time | "Cumulative sales growth" |
| **Heatmap** | Color-coded grid | Matrix data visualization | "Correlation matrix" |
| **Tree Map** | Nested rectangles | Hierarchical data | "Company organization structure" |
| **Network Graph** | Connected nodes | Relationships and connections | "Social network connections" |

## Error Handling

### HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| **200** | Success | Request processed successfully |
| **400** | Bad Request | Invalid prompt, missing parameters, or unsupported language |
| **401** | Unauthorized | Missing or invalid API key |
| **500** | Internal Server Error | Server-side processing error, API service unavailable |

### Error Response Format

```json
{
  "error": "Detailed error description",
  "status": "error",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z",
  "details": {
    "parameter": "Additional error context",
    "suggestion": "How to fix the error"
  }
}
```

### Common Error Scenarios

1. **Invalid Prompt**
   ```json
   {
     "error": "Prompt is too short or contains invalid characters",
     "code": "INVALID_PROMPT",
     "suggestion": "Use descriptive prompts with at least 3 words"
   }
   ```

2. **Unsupported Language**
   ```json
   {
     "error": "Language 'fr' is not supported",
     "code": "UNSUPPORTED_LANGUAGE",
     "suggestion": "Use 'en' for English or 'zh' for Chinese"
   }
   ```

3. **API Service Unavailable**
   ```json
   {
     "error": "Qwen API service is currently unavailable",
     "code": "API_UNAVAILABLE",
     "suggestion": "Check your API key and try again later"
   }
   ```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default Limit**: 100 requests per minute per IP
- **Burst Limit**: 10 requests per second
- **Headers**: Rate limit information is included in response headers

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Best Practices

### 1. Prompt Engineering

- **Be Specific**: "Compare renewable vs fossil fuel energy sources" vs "energy"
- **Include Context**: "Show monthly sales trends for Q4 2023"
- **Specify Chart Type**: "Create a bar chart comparing sales by region"

### 2. Request Body Optimization

- **Start Simple**: Begin with just the `prompt` field, add complexity as needed
- **Use Defaults**: Leverage automatic defaults for language and styling
- **Minimal Requests**: `{"prompt": "your text"}` works perfectly for most use cases
- **Progressive Enhancement**: Add language and style options for specific requirements

### 3. Error Handling

- Always check HTTP status codes
- Implement retry logic for 5xx errors
- Provide user-friendly error messages

### 4. Performance Optimization

- Cache generated images when possible
- Use appropriate image formats (PNG for quality, JPEG for size)
- Implement client-side caching headers

### 5. Security Considerations

- Validate all input parameters
- Implement proper authentication
- Use HTTPS in production
- Sanitize user prompts

## Troubleshooting

### Common Issues

1. **PNG Generation Fails**
   - Check Playwright browser installation: `python -m playwright install chromium`
   - Verify system has sufficient memory
   - Check logs for detailed error messages

2. **API Timeout**
   - Increase timeout settings for complex prompts
   - Check network connectivity
   - Verify server performance

3. **Image Quality Issues**
   - Adjust D3.js configuration parameters
   - Use higher resolution settings
   - Check browser compatibility

### Getting Help

- Check application logs in the `logs/` directory
- Run the dependency checker: `python dependency_checker/check_dependencies.py`
- Review error messages for specific guidance
- Check system resources and API service status

## Changelog

### Version 2.5.0
- Added `/api/clear_cache` endpoint for development workflow
- Fixed flow map rendering with professional substep positioning
- Enhanced modular JavaScript system integration
- Improved watermark styling consistency across diagram types

### Version 2.4.0
- Added comprehensive API documentation
- Enhanced error handling and response formats
- Improved rate limiting implementation
- Added style customization options

### Version 2.3.8
- Added PNG generation endpoint
- Enhanced D3.js visualization support
- Improved multi-language support
- Added health check endpoint

---

For more information, see the [main documentation](../README.md).
