// D3.js Common Utilities for MindGraph Application
// Shared functions used across multiple graph type renderers

// --- Safe, memory-leak-free text radius measurement ---
let measurementContainer = null;

function getMeasurementContainer() {
    if (!measurementContainer) {
        const body = d3.select('body');
        if (body.empty()) {
            console.warn('Body element not found, creating measurement container in document');
            measurementContainer = d3.select(document.documentElement)
                .append('div')
                .attr('id', 'measurement-container')
                .style('position', 'absolute')
                .style('visibility', 'hidden')
                .style('pointer-events', 'none');
        } else {
            measurementContainer = body
                .append('div')
                .attr('id', 'measurement-container')
                .style('position', 'absolute')
                .style('visibility', 'hidden')
                .style('pointer-events', 'none');
        }
    }
    return measurementContainer;
}

function getTextRadius(text, fontSize, padding) {
    let textElement = null;
    try {
        const container = getMeasurementContainer();
        textElement = container
            .append('svg')
            .append('text')
            .attr('font-size', fontSize)
            .text(text);
        const bbox = textElement.node().getBBox();
        const radius = Math.ceil(Math.sqrt(bbox.width * bbox.width + bbox.height * bbox.height) / 2 + (padding || 12));
        return Math.max(radius, 30); // Minimum radius
    } catch (error) {
        console.error('Error calculating text radius:', error);
        return 30; // Default fallback
    } finally {
        if (textElement) {
            textElement.remove();
        }
    }
}

function getTextDimensions(text, fontSize) {
    let textElement = null;
    try {
        const container = getMeasurementContainer();
        textElement = container
            .append('svg')
            .append('text')
            .attr('font-size', fontSize)
            .text(text);
        const bbox = textElement.node().getBBox();
        return { width: bbox.width, height: bbox.height };
    } catch (error) {
        console.error('Error calculating text dimensions:', error);
        return { width: 100, height: 20 }; // Default fallback
    } finally {
        if (textElement) {
            textElement.remove();
        }
    }
}

// --- Common theme and styling utilities ---
function applyTheme(svg, theme) {
    if (!theme) return;
    
    // Apply background color
    if (theme.backgroundColor) {
        svg.style('background-color', theme.backgroundColor);
    }
    
    // Apply any other common theme properties
    if (theme.fontFamily) {
        svg.style('font-family', theme.fontFamily);
    }
}

function createGradient(svg, id, color1, color2) {
    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient')
        .attr('id', id)
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '100%')
        .attr('y2', '100%');
    
    gradient.append('stop')
        .attr('offset', '0%')
        .style('stop-color', color1);
    
    gradient.append('stop')
        .attr('offset', '100%')
        .style('stop-color', color2);
    
    return gradient;
}

// --- Common positioning and layout utilities ---
function calculateNodePositions(nodes, width, height, layout = 'circle') {
    const positions = [];
    const centerX = width / 2;
    const centerY = height / 2;
    
    switch (layout) {
        case 'circle':
            const radius = Math.min(width, height) * 0.3;
            const angleStep = (2 * Math.PI) / nodes.length;
            nodes.forEach((node, i) => {
                const angle = i * angleStep;
                positions.push({
                    x: centerX + radius * Math.cos(angle),
                    y: centerY + radius * Math.sin(angle)
                });
            });
            break;
            
        case 'grid':
            const cols = Math.ceil(Math.sqrt(nodes.length));
            const rows = Math.ceil(nodes.length / cols);
            const cellWidth = width / cols;
            const cellHeight = height / rows;
            
            nodes.forEach((node, i) => {
                const col = i % cols;
                const row = Math.floor(i / cols);
                positions.push({
                    x: cellWidth * (col + 0.5),
                    y: cellHeight * (row + 0.5)
                });
            });
            break;
            
        default:
            // Default to center positioning
            nodes.forEach(() => {
                positions.push({ x: centerX, y: centerY });
            });
    }
    
    return positions;
}

// --- Common color utilities ---
function generateColorPalette(count, baseColor = '#3498db') {
    const colors = [];
    const hue = d3.hsl(baseColor).h;
    
    for (let i = 0; i < count; i++) {
        const newHue = (hue + (360 / count) * i) % 360;
        colors.push(d3.hsl(newHue, 0.7, 0.6).toString());
    }
    
    return colors;
}

// --- Common animation utilities ---
function animateNodes(selection, duration = 1000) {
    return selection
        .transition()
        .duration(duration)
        .ease(d3.easeElastic);
}

function fadeIn(selection, duration = 500) {
    return selection
        .style('opacity', 0)
        .transition()
        .duration(duration)
        .style('opacity', 1);
}

// --- Watermark utility ---
function addWatermark(svg, theme, dimensions) {
    if (!theme || !theme.showWatermark) return;
    
    const watermark = svg.append('g')
        .attr('class', 'watermark')
        .style('opacity', theme.watermarkOpacity || 0.3);
    
    watermark.append('text')
        .attr('x', dimensions.width - 10)
        .attr('y', dimensions.height - 10)
        .attr('text-anchor', 'end')
        .style('font-size', '12px')
        .style('fill', theme.watermarkColor || '#666')
        .text(theme.watermarkText || 'MindGraph');
}

// --- Export all utilities ---
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        getMeasurementContainer,
        getTextRadius,
        getTextDimensions,
        applyTheme,
        createGradient,
        calculateNodePositions,
        generateColorPalette,
        animateNodes,
        fadeIn,
        addWatermark
    };
} else {
    // Browser environment - functions are globally available
    console.log('D3 utilities loaded successfully');
}
