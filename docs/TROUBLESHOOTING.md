# Troubleshooting Guide

## Overview

This guide helps you resolve common issues when using MindGraph. If you encounter problems, check this guide first before seeking additional help.

## 🚨 **Quick Diagnosis**

### **1. Check Server Status**
```bash
curl http://localhost:9527/status
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.3.9",
  "services": {
    "qwen_api": "connected",
    "playwright": "ready"
  }
}
```

### **2. Check Application Logs**
```bash
tail -f logs/app.log
```

### **3. Verify Dependencies**
```bash
python dependency_checker/check_dependencies.py
```

## 🔧 **Common Issues & Solutions**

### **Issue 1: Server Won't Start**

#### **Symptoms**
- `python app.py` fails with errors
- Port 9527 already in use
- Import errors

#### **Solutions**

**Port Already in Use:**
```bash
# Find process using port 9527
netstat -tulpn | grep 9527
# or on Windows
netstat -ano | findstr 9527

# Kill the process
kill -9 <PID>
# or on Windows
taskkill /PID <PID> /F
```

**Import Errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version (requires 3.8+)
python --version
```

**Permission Errors:**
```bash
# On Linux/macOS
sudo pip install -r requirements.txt

# On Windows (run as Administrator)
pip install -r requirements.txt
```

### **Issue 2: PNG Generation Fails**

#### **Symptoms**
- API returns 500 error
- "Playwright not ready" error
- Empty or corrupted PNG files

#### **Solutions**

**Playwright Not Installed:**
```bash
# Install Playwright browsers
python -m playwright install chromium

# Verify installation
python -m playwright --version
```

**Browser Launch Issues:**
```bash
# Install system dependencies (Linux)
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1

# On macOS
brew install --cask chromium

# On Windows
# Download and install Chromium manually
```

**Memory Issues:**
```bash
# Check available memory
free -h  # Linux
top       # macOS
taskmgr   # Windows

# Reduce Playwright memory usage
export PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright
```

### **Issue 3: API Authentication Errors**

#### **Symptoms**
- 401 Unauthorized errors
- "API key not configured" messages
- Qwen API connection failures

#### **Solutions**

**Missing API Key:**
```bash
# Set environment variable
export QWEN_API_KEY="your_actual_api_key_here"

# Or create .env file
echo "QWEN_API_KEY=your_actual_api_key_here" > .env
```

**Invalid API Key:**
- Verify your Qwen API key is correct
- Check if the key has expired
- Ensure you have sufficient API credits

**API Service Unavailable:**
```bash
# Test Qwen API directly
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

### **Issue 4: Slow Response Times**

#### **Symptoms**
- API requests take >30 seconds
- Timeout errors
- Server becomes unresponsive

### **Issue 5: HTTP 404 - Endpoint Not Found**

#### **Symptoms**
- `HTTP 404: The requested URL was not found on the server`
- API calls to `/generate_png` or `/generate_graph` fail
- Server logs show 404 errors for valid endpoints

#### **Solutions**

**Check Endpoint URLs:**
```bash
# Both of these endpoints work:
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

curl -X POST http://localhost:9527/api/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

**Verify Server Configuration:**
1. **Check if server is running the updated app.py** with backward compatibility routes
2. **Restart the Flask application** after making changes
3. **Verify route registration** in server logs

**Common Causes:**
- Using wrong endpoint URL (missing `/api` prefix)
- Server not restarted after code changes
- Flask application not running the correct version
- Route not properly registered

**Debug Steps:**
```bash
# 1. Check server status
curl http://localhost:9527/status

# 2. Test both endpoint formats
curl -X POST http://localhost:9527/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

curl -X POST http://localhost:9527/api/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# 3. Check server logs for route registration
tail -f logs/app.log | grep "route"
```

#### **Solutions**

**Optimize Server Performance:**
```bash
# Check CPU and memory usage
htop  # Linux/macOS
top   # Alternative

# Monitor disk I/O
iotop  # Linux
```

**Reduce Response Time:**
```bash
# Use production mode
export DEBUG=False
export FLASK_ENV=production

# Optimize Playwright
export PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
```

**Network Issues:**
```bash
# Test network connectivity
ping your-mindgraph-server
telnet your-mindgraph-server 9527

# Check firewall settings
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS/RHEL
```

### **Issue 5: Dify Integration Problems**

#### **Symptoms**
- Webhook calls fail
- Images not displaying
- Timeout errors in Dify

#### **Solutions**

**Webhook Configuration:**
- Verify URL is accessible from Dify
- Check timeout settings (recommend 60+ seconds)
- Ensure proper headers are set

**Response Handling:**
```json
// In Dify webhook node
{
  "response_type": "binary",
  "save_response": true,
  "variable_name": "generated_image"
}
```

**CORS Issues:**
```python
# In app.py, ensure CORS is properly configured
from flask_cors import CORS
CORS(app, origins=["*"])  # For development
```

### **Issue 6: Image Quality Problems**

#### **Symptoms**
- Blurry or pixelated images
- Text not readable
- Incorrect dimensions

#### **Solutions**

**Increase Resolution:**
```bash
# Set environment variables
export D3_BASE_WIDTH=1200
export D3_BASE_HEIGHT=800
export D3_PADDING=60
```

**Font Size Issues:**
```bash
export TOPIC_FONT_SIZE=24
export CHAR_FONT_SIZE=18
```

**Browser Rendering:**
```bash
# Use higher quality Playwright settings
export PLAYWRIGHT_DEVTOOLS=1
export PLAYWRIGHT_HEADLESS=false  # For debugging
```

## 🐳 **Docker-Specific Issues**

### **Issue: Container Won't Build**

**Solution:**
```bash
# Clean build
docker system prune -a
docker build --no-cache -t mindgraph .

# Check Dockerfile syntax
docker run --rm -i hadolint/hadolint < docker/Dockerfile
```

### **Issue: Container Won't Start**

**Solution:**
```bash
# Check container logs
docker logs mindgraph

# Run with interactive mode
docker run -it --rm mindgraph /bin/bash

# Verify environment variables
docker exec mindgraph env | grep QWEN
```

### **Issue: Port Binding Problems**

**Solution:**
```bash
# Check port usage
docker port mindgraph

# Use different port
docker run -p 9528:9527 mindgraph

# Update docker-compose.yml
ports:
  - "9528:9527"
```

## 🔍 **Debugging Techniques**

### **1. Enable Debug Mode**
```bash
export DEBUG=True
export FLASK_DEBUG=1
python app.py
```

### **2. Verbose Logging**
```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=detailed
```

### **3. Test Individual Components**
```bash
# Test Qwen API
python -c "
from llm_clients import get_llm_client
client = get_llm_client('qwen')
print(client.test_connection())
"

# Test Playwright
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Playwright working!')
    browser.close()
"
```

### **4. Network Diagnostics**
```bash
# Check if port is listening
netstat -tulpn | grep 9527

# Test local connectivity
curl -v http://localhost:9527/status

# Check external connectivity
curl -v http://your-external-ip:9527/status
```

## 📊 **Performance Monitoring**

### **1. System Resources**
```bash
# Monitor in real-time
htop
iotop
nethogs

# Check specific process
ps aux | grep python
```

### **2. Application Metrics**
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:9527/status"

# Monitor memory usage
watch -n 1 'ps aux | grep python | grep -v grep'
```

### **3. Log Analysis**
```bash
# Find slow requests
grep "slow" logs/app.log | tail -20

# Check error frequency
grep "ERROR" logs/app.log | wc -l

# Monitor API usage
grep "POST /generate_png" logs/app.log | wc -l
```

## 🆘 **Getting Help**

### **1. Self-Diagnosis Checklist**
- [ ] Server is running and accessible
- [ ] API keys are properly configured
- [ ] Dependencies are installed
- [ ] Network connectivity is working
- [ ] Logs show no critical errors

### **2. Information to Provide**
When seeking help, include:

```bash
# System information
python --version
pip list | grep -E "(flask|langchain|playwright)"
docker --version  # if using Docker

# Error logs
tail -50 logs/app.log

# Configuration
env | grep -E "(QWEN|DEEPSEEK|DEBUG)"

# Test results
curl -v http://localhost:9527/status
```

### **3. Community Resources**
- **GitHub Issues**: [Report bugs and feature requests](https://github.com/your-repo/MindGraph/issues)
- **Discussions**: [Ask questions and share solutions](https://github.com/your-repo/MindGraph/discussions)
- **Documentation**: [Complete API reference](API_REFERENCE.md)

## 🔄 **Prevention Tips**

### **1. Regular Maintenance**
```bash
# Update dependencies monthly
pip install -r requirements.txt --upgrade

# Clean up old logs
find logs/ -name "*.log" -mtime +30 -delete

# Monitor disk space
df -h
```

### **2. Monitoring Setup**
```bash
# Set up health checks
crontab -e
# Add: */5 * * * * curl -f http://localhost:9527/status || echo "Server down"

# Monitor resource usage
# Use tools like Prometheus, Grafana, or simple scripts
```

### **3. Backup Strategy**
```bash
# Backup configuration
cp .env .env.backup
cp config.py config.py.backup

# Backup generated images
tar -czf mindgraph_exports_$(date +%Y%m%d).tar.gz mindgraph_exports/
```

## 📊 **Diagram Quality Issues (v2.3.9)**

### **Flow Map Improvements**

**If you're experiencing flow map issues, v2.3.9 includes major fixes:**

#### **Fixed Issues:**
- ✅ **Substep Overlapping**: Completely eliminated through new positioning algorithm
- ✅ **Excessive Spacing**: 75% reduction in title spacing, 50% reduction in group spacing  
- ✅ **Canvas Sizing**: Adaptive canvas that perfectly fits content
- ✅ **Text Cutoff**: Proper padding and text extension handling

#### **Flow Map Troubleshooting:**

**Problem: Substeps Still Overlap**
```bash
# Solution: Ensure you're using v2.3.9
curl http://localhost:9527/status | grep version
# Should show "2.3.9"

# Clear browser cache if using web interface
# Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
```

**Problem: Too Much Spacing Around Title**
```bash
# This is now optimized in v2.3.9
# Title spacing reduced from 40px to 10px
# Content offset reduced from 60px to 15px
# No action needed - automatic improvement
```

### **Classification Improvements**

**Enhanced Chinese Support in v2.3.9:**

#### **Fixed Classifications:**
- ✅ **"括号图"** → Now correctly identifies as `brace_map` (was `org_chart`)
- ✅ **"复流程图"** → Now correctly identifies as `multi_flow_map` (was `flow_map`)
- ✅ **All Chinese Terms** → Comprehensive coverage for all 12 diagram types

#### **Classification Troubleshooting:**

**Problem: Wrong Diagram Type Generated**
```bash
# Test classification accuracy
curl -X POST http://localhost:9527/api/generate_png \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成关于咖啡制作的流程图", "language": "zh"}'
  
# Should generate flow_map, not multi_flow_map or other types
```

**Problem: Chinese Prompts Not Working**
```bash
# Verify language parameter
{
  "prompt": "制作学习方法的圆圈图",
  "language": "zh"  # Important: specify Chinese
}

# v2.3.9 has comprehensive Chinese examples for all diagram types
```

### **Canvas and Rendering Issues**

#### **Adaptive Canvas (v2.3.9):**

**Problem: Canvas Too Large or Too Small**
```bash
# v2.3.9 automatically calculates optimal canvas size
# Canvas dimensions now match content bounds perfectly
# No manual adjustments needed
```

**Problem: Text Cut Off at Edges**
```bash
# Fixed in v2.3.9 with proper text extension calculations
# Added safety margins and padding calculations
# Automatic improvement - no action required
```

---

**Still having issues?** Check the [API Reference](API_REFERENCE.md) or open a GitHub issue with detailed information about your problem.
