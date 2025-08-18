/**
 * Bubble Map Renderer for MindGraph
 * 
 * This module contains the bubble map, double bubble map, and circle map rendering functions.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~50KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found. Please load shared-utilities.js first.');
}

// Note: getTextRadius and addWatermark are available globally from shared-utilities.js

function renderBubbleMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.topic || !Array.isArray(spec.attributes)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for bubble_map');
        return;
    }
    
    // Use provided theme and dimensions or defaults
    const baseWidth = dimensions?.baseWidth || 700;
    const baseHeight = dimensions?.baseHeight || 500;
    const padding = dimensions?.padding || 40;
    
    // Load theme
    let THEME;
    try {
        if (typeof styleManager !== 'undefined' && styleManager.getTheme) {
            THEME = styleManager.getTheme('bubble_map', theme, theme);
        } else {
            console.warn('Style manager not available, using fallback theme');
            THEME = {
                topicFill: '#1976d2',  // Deep blue background
                topicText: '#ffffff',   // White text for contrast
                topicStroke: '#000000', // Black border for topic nodes
                topicStrokeWidth: 3,
                attributeFill: '#e3f2fd',  // Light blue for attributes
                attributeText: '#333333', // Dark text for readability
                attributeStroke: '#000000',  // Black border
                attributeStrokeWidth: 2,
                fontTopic: 20,
                fontAttribute: 14,
                background: '#ffffff'
            };
        }
    } catch (error) {
        console.error('Error getting theme from style manager:', error);
        THEME = {
            topicFill: '#1976d2',
            topicText: '#ffffff',
            topicStroke: '#000000',
            topicStrokeWidth: 3,
            attributeFill: '#e3f2fd',
            attributeText: '#333333',
            attributeStroke: '#000000',
            attributeStrokeWidth: 2,
            fontTopic: 20,
            fontAttribute: 14,
            background: '#ffffff'
        };
    }
    
    // Apply background if specified
    if (theme && theme.background) {
        d3.select('#d3-container').style('background-color', theme.background);
    }
    
    // Calculate sizes
    const topicR = getTextRadius(spec.topic, THEME.fontTopic, 20);
    
    // Calculate uniform radius for all attribute nodes
    const attributeRadii = spec.attributes.map(t => getTextRadius(t, THEME.fontAttribute, 10));
    const uniformAttributeR = Math.max(...attributeRadii, 30); // Use the largest required radius for all
    
    // Calculate layout with collision detection
    const centerX = baseWidth / 2;
    let centerY = baseHeight / 2;
    
    // Calculate even distribution around the topic
    const targetDistance = topicR + uniformAttributeR + 50; // Distance from center
    
    // Create nodes for force simulation with uniform radius
    const nodes = spec.attributes.map((attr, i) => {
        // Calculate even angle distribution around the circle
        const angle = (i * 360 / spec.attributes.length) - 90; // -90 to start from top
        const targetX = centerX + targetDistance * Math.cos(angle * Math.PI / 180);
        const targetY = centerY + targetDistance * Math.sin(angle * Math.PI / 180);
        
        return {
            id: i,
            text: attr,
            radius: uniformAttributeR, // All nodes use the same radius
            targetX: targetX,
            targetY: targetY,
            x: targetX, // Start at target position
            y: targetY
        };
    });
    
    // Add central topic as a fixed node
    const centralNode = {
        id: 'central',
        text: spec.topic,
        radius: topicR,
        x: centerX,
        y: centerY,
        fx: centerX, // Fixed position
        fy: centerY
    };
    
    // Create force simulation with target positioning
    const simulation = d3.forceSimulation([centralNode, ...nodes])
        .force('charge', d3.forceManyBody().strength(-800))
        .force('collide', d3.forceCollide().radius(d => d.radius + 5))
        .force('center', d3.forceCenter(centerX, centerY))
        .force('target', function() {
            nodes.forEach(node => {
                if (node.targetX !== undefined && node.targetY !== undefined) {
                    const dx = node.targetX - node.x;
                    const dy = node.targetY - node.y;
                    node.vx += dx * 0.1; // Pull towards target position
                    node.vy += dy * 0.1;
                }
            });
        })
        .stop();
    
    // Run simulation to find optimal positions
    for (let i = 0; i < 300; ++i) simulation.tick();
    
    // Calculate bounds for SVG
    const positions = nodes.map(n => ({ x: n.x, y: n.y, radius: n.radius }));
    positions.push({ x: centerX, y: centerY, radius: topicR });
    
    const minX = Math.min(...positions.map(p => p.x - p.radius)) - padding;
    const maxX = Math.max(...positions.map(p => p.x + p.radius)) + padding;
    const minY = Math.min(...positions.map(p => p.y - p.radius)) - padding;
    const maxY = Math.max(...positions.map(p => p.y + p.radius)) + padding;
    const width = maxX - minX;
    const height = maxY - minY;
    
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `${minX} ${minY} ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMinYMin meet');
    
    // Draw connecting lines from topic to attributes
    nodes.forEach(node => {
        const dx = node.x - centerX;
        const dy = node.y - centerY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist > 0) {
            const lineStartX = centerX + (dx / dist) * topicR;
            const lineStartY = centerY + (dy / dist) * topicR;
            const lineEndX = node.x - (dx / dist) * node.radius;
            const lineEndY = node.y - (dy / dist) * node.radius;
            
            svg.append('line')
                .attr('x1', lineStartX)
                .attr('y1', lineStartY)
                .attr('x2', lineEndX)
                .attr('y2', lineEndY)
                .attr('stroke', '#888')
                .attr('stroke-width', 2);
        }
    });
    
    // Draw topic circle (center)
    svg.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', topicR)
        .attr('fill', THEME.topicFill)
        .attr('stroke', THEME.topicStroke)
        .attr('stroke-width', THEME.topicStrokeWidth);
    
    svg.append('text')
        .attr('x', centerX)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topicText)
        .attr('font-size', THEME.fontTopic)
        .attr('font-weight', 'bold')
        .text(spec.topic);
    
    // Draw attribute circles
    nodes.forEach(node => {
        svg.append('circle')
            .attr('cx', node.x)
            .attr('cy', node.y)
            .attr('r', node.radius)
            .attr('fill', THEME.attributeFill)
            .attr('stroke', THEME.attributeStroke)
            .attr('stroke-width', THEME.attributeStrokeWidth);
        
        svg.append('text')
            .attr('x', node.x)
            .attr('y', node.y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.attributeText)
            .attr('font-size', THEME.fontAttribute)
            .text(node.text);
    });
    
    // Watermark
    addWatermark(svg, theme);
}

function renderCircleMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.topic || !Array.isArray(spec.context)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for circle_map');
        return;
    }
    
    // Use provided theme and dimensions or defaults
    const baseWidth = dimensions?.baseWidth || 700;
    const baseHeight = dimensions?.baseHeight || 500;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        outerCircleFill: 'none',
        outerCircleStroke: '#2c3e50',
        outerCircleStrokeWidth: 2,
        topicFill: '#4e79a7',
        topicText: '#fff',
        topicStroke: '#35506b',
        topicStrokeWidth: 3,
        contextFill: '#a7c7e7',
        contextText: '#333',
        contextStroke: '#2c3e50',
        contextStrokeWidth: 2,
        fontTopic: 20,
        fontContext: 14,
        ...theme
    };
    
    // Calculate uniform radius for all context nodes
    const contextRadii = spec.context.map(t => getTextRadius(t, THEME.fontContext, 10));
    const uniformContextR = Math.max(...contextRadii, 40);
    
    const topicR = getTextRadius(spec.topic, THEME.fontTopic, 20);
    
    // Calculate circle layout
    const centerX = baseWidth / 2;
    const centerY = baseHeight / 2;
    
    // Calculate optimal radius for outer circle
    const minOuterRadius = topicR + uniformContextR + 60;
    const outerRadius = Math.max(minOuterRadius, 120);
    
    const angleStep = (2 * Math.PI) / spec.context.length;
    
    const width = baseWidth;
    const height = baseHeight;
    
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Draw outer circle
    svg.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', outerRadius)
        .attr('fill', THEME.outerCircleFill)
        .attr('stroke', THEME.outerCircleStroke)
        .attr('stroke-width', THEME.outerCircleStrokeWidth);
    
    // Draw context nodes around the circle
    spec.context.forEach((context, i) => {
        const angle = i * angleStep - Math.PI / 2; // Start from top
        const x = centerX + outerRadius * Math.cos(angle);
        const y = centerY + outerRadius * Math.sin(angle);
        
        svg.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', uniformContextR)
            .attr('fill', THEME.contextFill)
            .attr('stroke', THEME.contextStroke)
            .attr('stroke-width', THEME.contextStrokeWidth);
        
        svg.append('text')
            .attr('x', x)
            .attr('y', y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.contextText)
            .attr('font-size', THEME.fontContext)
            .text(context);
    });
    
    // Draw central topic
    svg.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', topicR)
        .attr('fill', THEME.topicFill)
        .attr('stroke', THEME.topicStroke)
        .attr('stroke-width', THEME.topicStrokeWidth);
    
    svg.append('text')
        .attr('x', centerX)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topicText)
        .attr('font-size', THEME.fontTopic)
        .attr('font-weight', 'bold')
        .text(spec.topic);
    
    // Watermark
    addWatermark(svg, theme);
}

function renderDoubleBubbleMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.topic1 || !spec.topic2) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for double bubble map');
        return;
    }
    
    const baseWidth = dimensions?.baseWidth || 800;
    const baseHeight = dimensions?.baseHeight || 600;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        topic1Fill: '#3498db',
        topic1Text: '#ffffff',
        topic1Stroke: '#2c3e50',
        topic2Fill: '#e74c3c',
        topic2Text: '#ffffff',
        topic2Stroke: '#2c3e50',
        commonFill: '#9b59b6',
        commonText: '#ffffff',
        commonStroke: '#2c3e50',
        attribute1Fill: '#ecf0f1',
        attribute1Text: '#2c3e50',
        attribute2Fill: '#ecf0f1',
        attribute2Text: '#2c3e50',
        fontTopic: 18,
        fontAttribute: 14,
        strokeWidth: 2,
        ...theme
    };
    
    // Calculate text sizes
    const topic1R = getTextRadius(spec.topic1, THEME.fontTopic, 20);
    const topic2R = getTextRadius(spec.topic2, THEME.fontTopic, 20);
    
    // Calculate positions
    const centerX = baseWidth / 2;
    const centerY = baseHeight / 2;
    const separation = Math.max(topic1R + topic2R + 100, 200);
    
    const topic1X = centerX - separation / 2;
    const topic2X = centerX + separation / 2;
    
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Draw topic 1
    svg.append('circle')
        .attr('cx', topic1X)
        .attr('cy', centerY)
        .attr('r', topic1R)
        .attr('fill', THEME.topic1Fill)
        .attr('stroke', THEME.topic1Stroke)
        .attr('stroke-width', THEME.strokeWidth);
    
    svg.append('text')
        .attr('x', topic1X)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topic1Text)
        .attr('font-size', THEME.fontTopic)
        .attr('font-weight', 'bold')
        .text(spec.topic1);
    
    // Draw topic 2
    svg.append('circle')
        .attr('cx', topic2X)
        .attr('cy', centerY)
        .attr('r', topic2R)
        .attr('fill', THEME.topic2Fill)
        .attr('stroke', THEME.topic2Stroke)
        .attr('stroke-width', THEME.strokeWidth);
    
    svg.append('text')
        .attr('x', topic2X)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topic2Text)
        .attr('font-size', THEME.fontTopic)
        .attr('font-weight', 'bold')
        .text(spec.topic2);
    
    // Draw common characteristics in the center
    if (spec.common && Array.isArray(spec.common)) {
        const commonY = centerY - 100;
        spec.common.forEach((item, i) => {
            const commonR = getTextRadius(item, THEME.fontAttribute, 10);
            const y = commonY + i * 30;
            
            svg.append('circle')
                .attr('cx', centerX)
                .attr('cy', y)
                .attr('r', commonR)
                .attr('fill', THEME.commonFill)
                .attr('stroke', THEME.commonStroke)
                .attr('stroke-width', THEME.strokeWidth);
            
            svg.append('text')
                .attr('x', centerX)
                .attr('y', y)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', THEME.commonText)
                .attr('font-size', THEME.fontAttribute)
                .text(item);
        });
    }
    
    // Watermark
    addWatermark(svg, theme);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.BubbleMapRenderer = {
        renderBubbleMap,
        renderCircleMap,
        renderDoubleBubbleMap
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderBubbleMap,
        renderCircleMap,
        renderDoubleBubbleMap
    };
}
