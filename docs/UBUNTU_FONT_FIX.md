# Ubuntu Server Font Compatibility Fix

## Problem Description

The MindGraph application was working perfectly on Windows but showing a grey background with no visible content on Ubuntu servers. This was caused by missing font loading in the PNG generation HTML templates.

## Root Cause

1. **Font Dependency**: The mindmap renderer uses Inter fonts for text rendering
2. **Missing Font Loading**: The HTML generated for PNG generation was missing font CSS inclusion
3. **Platform Difference**: Windows has Segoe UI as fallback fonts, Ubuntu doesn't
4. **Result**: Text was invisible on Ubuntu, making mindmaps appear as blank grey backgrounds

## Solution Implemented

### 1. Font Loading Function
Added a helper function `_get_font_base64()` in `api_routes.py` that:
- Reads font files from `static/fonts/` directory
- Converts them to base64 encoding
- Returns the encoded data for HTML embedding

### 2. HTML Template Updates
Updated both PNG generation endpoints to include embedded fonts:
- `generate_png()` function - contains nested `render_svg_to_png` function
- `generate_dingtalk()` function - contains nested `render_svg_to_png` function

### 3. Font Embedding
Added `@font-face` declarations for all Inter font weights:
- inter-300.ttf (Light)
- inter-400.ttf (Regular)
- inter-500.ttf (Medium)
- inter-600.ttf (SemiBold)
- inter-700.ttf (Bold)

## Code Structure

The code uses a nested function pattern where each PNG generation endpoint has its own internal rendering function:

```python
@api.route('/generate_png', methods=['POST'])
def generate_png():
    # ... setup code ...
    
    async def render_svg_to_png(spec, graph_type):
        # ... rendering logic with embedded fonts ...
        html = f'''
        <html>
        <!-- Font declarations embedded here -->
        @font-face {{ ... }}
        <!-- Rest of HTML -->
        '''
    
    # ... call the nested function ...

@api.route('/generate_dingtalk', methods=['POST'])
def generate_dingtalk():
    # ... setup code ...
    
    async def render_svg_to_png(spec, graph_type):
        # ... rendering logic with embedded fonts ...
        html = f'''
        <html>
        <!-- Font declarations embedded here -->
        @font-face {{ ... }}
        <!-- Rest of HTML -->
        '''
    
    # ... call the nested function ...
```

## Code Changes

### New Function Added
```python
def _get_font_base64(font_filename):
    """Convert font file to base64 for embedding in HTML."""
    try:
        font_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts', font_filename)
        if os.path.exists(font_path):
            with open(font_path, 'rb') as f:
                import base64
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            logger.warning(f"Font file not found: {font_path}")
            return ""
    except Exception as e:
        logger.error(f"Failed to load font {font_filename}: {e}")
        return ""
```

### HTML Template Update
```html
/* Inter Font Loading for Ubuntu Server Compatibility */
@font-face {
    font-display: swap;
    font-family: 'Inter';
    font-style: normal;
    font-weight: 300;
    src: url('data:font/truetype;base64,{_get_font_base64("inter-300.ttf")}') format('truetype');
}
<!-- Repeat for all font weights -->
```

## Benefits

1. **Cross-Platform Compatibility**: Works on both Windows and Ubuntu
2. **Self-Contained**: No external font dependencies
3. **Performance**: Fonts are embedded directly in HTML, no additional HTTP requests
4. **Reliability**: Eliminates font loading failures on different server configurations
5. **Maintainability**: Each endpoint has its own rendering logic for flexibility

## Testing

The fix has been tested locally and verified that:
- All font files are accessible
- Base64 conversion works correctly
- HTML generation includes proper font declarations
- Font sizes are appropriate (300-700 weight variants)

## Deployment Notes

1. **Restart Required**: Server must be restarted after applying the fix
2. **Font Files**: Ensure all Inter font files are present in `static/fonts/`
3. **Memory Impact**: Base64 encoding increases HTML size by ~2MB (acceptable for PNG generation)
4. **Browser Support**: Modern browsers support data URI fonts

## Files Modified

- `api_routes.py`: Added font loading function and updated HTML templates in both PNG generation endpoints

## Technical Details

### Font Loading Strategy
- **Base64 Encoding**: Fonts are converted to base64 and embedded as data URIs
- **Inline CSS**: Font declarations are included directly in the generated HTML
- **No External Dependencies**: Eliminates network requests for font loading

### Code Organization
- **Nested Functions**: Each endpoint has its own `render_svg_to_png` function for isolation
- **Shared Utilities**: Font loading function is shared between both endpoints
- **Consistent Implementation**: Both endpoints use identical font embedding approach

## Verification

After deployment, verify that:
1. Mindmaps render with visible text on Ubuntu servers
2. PNG generation includes proper text rendering
3. No font-related errors in server logs
4. Consistent rendering between Windows and Ubuntu environments
5. Both `/generate_png` and `/generate_dingtalk` endpoints work correctly
