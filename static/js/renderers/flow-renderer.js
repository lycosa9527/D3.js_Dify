/**
 * Flow Renderer for MindGraph
 * 
 * This module contains the flowchart, flow map, multi-flow map, and bridge map rendering functions.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~45KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found! Please load shared-utilities.js first.');
}

const { getTextRadius, addWatermark, getThemeDefaults } = window.MindGraphUtils;

function renderFlowchart(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');

    // Validate spec
    if (!spec || !spec.title || !Array.isArray(spec.steps)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for flowchart');
        return;
    }

    // Use provided padding; width/height will be derived from content
    const padding = dimensions?.padding || 40;

    // Get theme using style manager
    let THEME;
    try {
        if (typeof styleManager !== 'undefined' && styleManager.getTheme) {
            THEME = styleManager.getTheme('flowchart', theme, theme);
        } else {
            console.warn('Style manager not available, using fallback theme');
            THEME = {
                startFill: '#4caf50',
                startText: '#ffffff',
                startStroke: '#388e3c',
                startStrokeWidth: 2,
                processFill: '#2196f3',
                processText: '#ffffff',
                processStroke: '#1976d2',
                processStrokeWidth: 2,
                decisionFill: '#ff9800',
                decisionText: '#ffffff',
                decisionStroke: '#f57c00',
                decisionStrokeWidth: 2,
                endFill: '#f44336',
                endText: '#ffffff',
                endStroke: '#d32f2f',
                endStrokeWidth: 2,
                fontNode: 14,
                fontEdge: 12
            };
        }
    } catch (error) {
        console.error('Error getting theme from style manager:', error);
        THEME = {
            startFill: '#4caf50',
            startText: '#ffffff',
            startStroke: '#388e3c',
            startStrokeWidth: 2,
            processFill: '#2196f3',
            processText: '#ffffff',
            processStroke: '#1976d2',
            processStrokeWidth: 2,
            decisionFill: '#ff9800',
            decisionText: '#ffffff',
            decisionStroke: '#f57c00',
            decisionStrokeWidth: 2,
            endFill: '#f44336',
            endText: '#ffffff',
            endStroke: '#d32f2f',
            endStrokeWidth: 2,
            fontNode: 14,
            fontEdge: 12
        };
    }

    // Measurement SVG (off-screen)
    const tempSvg = d3.select('body').append('svg')
        .attr('width', 0)
        .attr('height', 0)
        .style('position', 'absolute')
        .style('left', '-9999px')
        .style('top', '-9999px');

    function measureTextSize(text, fontSize) {
        const t = tempSvg.append('text')
            .attr('x', -9999)
            .attr('y', -9999)
            .attr('font-size', fontSize)
            .attr('dominant-baseline', 'hanging')
            .text(text || '');
        const bbox = t.node().getBBox();
        t.remove();
        return { w: Math.ceil(bbox.width), h: Math.ceil(bbox.height || fontSize) };
    }

    // Measure title
    const titleFont = 20;
    const titleSize = measureTextSize(spec.title, titleFont);

    // Measure each step's text and compute adaptive node sizes
    const hPad = 14;
    const vPad = 10;
    const stepSpacing = 40;
    const nodeRadius = 5;

    const nodes = spec.steps.map(step => {
        const txt = step.text || '';
        const m = measureTextSize(txt, THEME.fontNode);
        const w = Math.max(100, m.w + hPad * 2);
        const h = Math.max(40, m.h + vPad * 2);
        return { step, text: txt, w, h };
    });

    // Compute required canvas from content
    const maxNodeWidth = nodes.reduce((acc, n) => Math.max(acc, n.w), 0);
    const requiredWidth = Math.max(titleSize.w, maxNodeWidth) + padding * 2;
    const totalNodesHeight = nodes.reduce((sum, n) => sum + n.h, 0);
    const totalSpacing = Math.max(0, nodes.length - 1) * stepSpacing;
    const requiredHeight = padding + (titleSize.h + 30) + totalNodesHeight + totalSpacing + padding;

    // Apply dimensions by sizing container explicitly
    d3.select('#d3-container')
        .style('width', requiredWidth + 'px')
        .style('height', requiredHeight + 'px');

    // Create visible SVG
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', requiredWidth)
        .attr('height', requiredHeight)
        .attr('viewBox', `0 0 ${requiredWidth} ${requiredHeight}`)
        .attr('preserveAspectRatio', 'xMinYMin meet');

    // Remove temp svg
    tempSvg.remove();

    // Draw title
    const titleY = padding + titleSize.h;
    svg.append('text')
        .attr('x', requiredWidth / 2)
        .attr('y', titleY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#333')
        .attr('font-size', titleFont)
        .attr('font-weight', 'bold')
        .text(spec.title);

    // Vertical layout
    const centerX = requiredWidth / 2;
    let yCursor = titleY + 40;

    nodes.forEach((n, i) => {
        const x = centerX;
        const y = yCursor + n.h / 2;

        let fill, stroke, strokeWidth, textColor;
        switch (n.step.type) {
            case 'start':
                fill = THEME.startFill; stroke = THEME.startStroke; strokeWidth = THEME.startStrokeWidth; textColor = THEME.startText; break;
            case 'decision':
                fill = THEME.decisionFill; stroke = THEME.decisionStroke; strokeWidth = THEME.decisionStrokeWidth; textColor = THEME.decisionText; break;
            case 'end':
                fill = THEME.endFill; stroke = THEME.endStroke; strokeWidth = THEME.endStrokeWidth; textColor = THEME.endText; break;
            default:
                fill = THEME.processFill; stroke = THEME.processStroke; strokeWidth = THEME.processStrokeWidth; textColor = THEME.processText; break;
        }

        if (n.step.type === 'decision') {
            // Diamond using adaptive width/height
            const points = [
                `${x},${y - n.h/2}`,
                `${x + n.w/2},${y}`,
                `${x},${y + n.h/2}`,
                `${x - n.w/2},${y}`
            ].join(' ');
            svg.append('polygon')
                .attr('points', points)
                .attr('fill', fill)
                .attr('stroke', stroke)
                .attr('stroke-width', strokeWidth);
        } else {
            svg.append('rect')
                .attr('x', x - n.w/2)
                .attr('y', y - n.h/2)
                .attr('width', n.w)
                .attr('height', n.h)
                .attr('rx', nodeRadius)
                .attr('fill', fill)
                .attr('stroke', stroke)
                .attr('stroke-width', strokeWidth);
        }

        svg.append('text')
            .attr('x', x)
            .attr('y', y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', textColor || '#fff')
            .attr('font-size', THEME.fontNode)
            .text(n.text);

        // Arrow to next node
        if (i < nodes.length - 1) {
            const nextTopY = y + n.h / 2 + 6;
            const nextBottomY = nextTopY + stepSpacing - 12;
            svg.append('line')
                .attr('x1', x)
                .attr('y1', nextTopY)
                .attr('x2', x)
                .attr('y2', nextBottomY)
                .attr('stroke', '#666')
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)');
        }

        yCursor += n.h + stepSpacing;
    });

    // Arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 8)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#666');

    // Watermark
    addWatermark(svg, theme);
}

function renderFlowMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.topic || !Array.isArray(spec.sequence)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for flow map');
        return;
    }
    
    const baseWidth = dimensions?.baseWidth || 800;
    const baseHeight = dimensions?.baseHeight || 600;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        topicFill: '#3498db',
        topicText: '#ffffff',
        topicStroke: '#2980b9',
        sequenceFill: '#ecf0f1',
        sequenceText: '#2c3e50',
        sequenceStroke: '#bdc3c7',
        arrowColor: '#7f8c8d',
        fontTopic: 18,
        fontSequence: 14,
        strokeWidth: 2,
        ...theme
    };
    
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Draw topic at top center
    const topicRadius = getTextRadius(spec.topic, THEME.fontTopic, 20);
    const topicX = baseWidth / 2;
    const topicY = padding + topicRadius + 20;
    
    svg.append('circle')
        .attr('cx', topicX)
        .attr('cy', topicY)
        .attr('r', topicRadius)
        .attr('fill', THEME.topicFill)
        .attr('stroke', THEME.topicStroke)
        .attr('stroke-width', THEME.strokeWidth);
    
    svg.append('text')
        .attr('x', topicX)
        .attr('y', topicY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topicText)
        .attr('font-size', THEME.fontTopic)
        .attr('font-weight', 'bold')
        .text(spec.topic);
    
    // Draw sequence items in a flowing pattern
    const itemSpacing = 150;
    const rowHeight = 80;
    const itemsPerRow = Math.floor((baseWidth - 2 * padding) / itemSpacing);
    
    spec.sequence.forEach((item, i) => {
        const row = Math.floor(i / itemsPerRow);
        const col = i % itemsPerRow;
        const itemX = padding + col * itemSpacing + itemSpacing / 2;
        const itemY = topicY + topicRadius + 60 + row * rowHeight;
        
        const itemRadius = getTextRadius(item, THEME.fontSequence, 15);
        
        // Draw sequence item
        svg.append('rect')
            .attr('x', itemX - itemRadius)
            .attr('y', itemY - itemRadius * 0.6)
            .attr('width', itemRadius * 2)
            .attr('height', itemRadius * 1.2)
            .attr('rx', 5)
            .attr('fill', THEME.sequenceFill)
            .attr('stroke', THEME.sequenceStroke)
            .attr('stroke-width', THEME.strokeWidth);
        
        svg.append('text')
            .attr('x', itemX)
            .attr('y', itemY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.sequenceText)
            .attr('font-size', THEME.fontSequence)
            .text(item);
        
        // Draw arrow to next item
        if (i < spec.sequence.length - 1) {
            const nextRow = Math.floor((i + 1) / itemsPerRow);
            const nextCol = (i + 1) % itemsPerRow;
            const nextX = padding + nextCol * itemSpacing + itemSpacing / 2;
            const nextY = topicY + topicRadius + 60 + nextRow * rowHeight;
            
            if (row === nextRow) {
                // Same row - horizontal arrow
                svg.append('line')
                    .attr('x1', itemX + itemRadius)
                    .attr('y1', itemY)
                    .attr('x2', nextX - itemRadius)
                    .attr('y2', nextY)
                    .attr('stroke', THEME.arrowColor)
                    .attr('stroke-width', 2)
                    .attr('marker-end', 'url(#arrow)');
            } else {
                // Different row - curved arrow
                const path = `M${itemX},${itemY + itemRadius * 0.6} Q${itemX + 30},${itemY + 30} ${nextX},${nextY - itemRadius * 0.6}`;
                svg.append('path')
                    .attr('d', path)
                    .attr('fill', 'none')
                    .attr('stroke', THEME.arrowColor)
                    .attr('stroke-width', 2)
                    .attr('marker-end', 'url(#arrow)');
            }
        }
    });
    
    // Arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 8)
        .attr('refY', 0)
        .attr('markerWidth', 4)
        .attr('markerHeight', 4)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', THEME.arrowColor);
    
    // Watermark
    addWatermark(svg, theme);
}

function renderBridgeMap(spec, theme = null, dimensions = null, containerId = 'd3-container') {
    d3.select(`#${containerId}`).html('');
    if (!spec || !spec.topic || !Array.isArray(spec.analogies)) {
        d3.select(`#${containerId}`).append('div').style('color', 'red').text('Invalid spec for bridge map');
        return;
    }
    
    const baseWidth = dimensions?.baseWidth || 800;
    const baseHeight = dimensions?.baseHeight || 200;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        topicFill: '#2c3e50',
        topicText: '#ffffff',
        analogyFill: '#3498db',
        analogyText: '#ffffff',
        bridgeColor: '#95a5a6',
        fontTopic: 16,
        fontAnalogy: 14,
        strokeWidth: 2,
        ...theme
    };
    
    const svg = d3.select(`#${containerId}`).append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Calculate positions
    const centerY = baseHeight / 2;
    const topicWidth = 150;
    const analogySpacing = (baseWidth - 2 * padding - topicWidth) / spec.analogies.length;
    
    // Draw main topic
    const topicX = padding + topicWidth / 2;
    svg.append('rect')
        .attr('x', topicX - topicWidth / 2)
        .attr('y', centerY - 25)
        .attr('width', topicWidth)
        .attr('height', 50)
        .attr('rx', 5)
        .attr('fill', THEME.topicFill)
        .attr('stroke', THEME.topicFill)
        .attr('stroke-width', THEME.strokeWidth);
    
    svg.append('text')
        .attr('x', topicX)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topicText)
        .attr('font-size', THEME.fontTopic)
        .attr('font-weight', 'bold')
        .text(spec.topic);
    
    // Draw bridges and analogies
    spec.analogies.forEach((analogy, i) => {
        const analogyX = padding + topicWidth + (i + 0.5) * analogySpacing;
        
        // Bridge line
        svg.append('line')
            .attr('x1', topicX + topicWidth / 2)
            .attr('y1', centerY)
            .attr('x2', analogyX - 60)
            .attr('y2', centerY)
            .attr('stroke', THEME.bridgeColor)
            .attr('stroke-width', 3);
        
        // Analogy box
        const analogyWidth = 120;
        svg.append('rect')
            .attr('x', analogyX - analogyWidth / 2)
            .attr('y', centerY - 25)
            .attr('width', analogyWidth)
            .attr('height', 50)
            .attr('rx', 5)
            .attr('fill', THEME.analogyFill)
            .attr('stroke', THEME.analogyFill)
            .attr('stroke-width', THEME.strokeWidth);
        
        svg.append('text')
            .attr('x', analogyX)
            .attr('y', centerY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.analogyText)
            .attr('font-size', THEME.fontAnalogy)
            .text(analogy);
    });
    
    // Watermark
    addWatermark(svg, theme);
}

function renderMultiFlowMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.central_topic || !Array.isArray(spec.flows)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for multi flow map');
        return;
    }
    
    const baseWidth = dimensions?.baseWidth || 1000;
    const baseHeight = dimensions?.baseHeight || 700;
    const padding = dimensions?.padding || 50;
    
    const THEME = {
        centralFill: '#2c3e50',
        centralText: '#ffffff',
        flowFill: '#3498db',
        flowText: '#ffffff',
        stepFill: '#ecf0f1',
        stepText: '#2c3e50',
        arrowColor: '#7f8c8d',
        fontCentral: 18,
        fontFlow: 16,
        fontStep: 12,
        strokeWidth: 2,
        ...theme
    };
    
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Central topic
    const centerX = baseWidth / 2;
    const centerY = baseHeight / 2;
    const centralRadius = getTextRadius(spec.central_topic, THEME.fontCentral, 25);
    
    svg.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', centralRadius)
        .attr('fill', THEME.centralFill)
        .attr('stroke', THEME.centralFill)
        .attr('stroke-width', THEME.strokeWidth);
    
    svg.append('text')
        .attr('x', centerX)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.centralText)
        .attr('font-size', THEME.fontCentral)
        .attr('font-weight', 'bold')
        .text(spec.central_topic);
    
    // Draw flows radiating outward
    const angleStep = (2 * Math.PI) / spec.flows.length;
    const flowDistance = 200;
    
    spec.flows.forEach((flow, i) => {
        const angle = i * angleStep;
        const flowX = centerX + flowDistance * Math.cos(angle);
        const flowY = centerY + flowDistance * Math.sin(angle);
        
        // Flow topic
        const flowRadius = getTextRadius(flow.topic, THEME.fontFlow, 20);
        svg.append('circle')
            .attr('cx', flowX)
            .attr('cy', flowY)
            .attr('r', flowRadius)
            .attr('fill', THEME.flowFill)
            .attr('stroke', THEME.flowFill)
            .attr('stroke-width', THEME.strokeWidth);
        
        svg.append('text')
            .attr('x', flowX)
            .attr('y', flowY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.flowText)
            .attr('font-size', THEME.fontFlow)
            .attr('font-weight', 'bold')
            .text(flow.topic);
        
        // Connection to center
        svg.append('line')
            .attr('x1', centerX + centralRadius * Math.cos(angle))
            .attr('y1', centerY + centralRadius * Math.sin(angle))
            .attr('x2', flowX - flowRadius * Math.cos(angle))
            .attr('y2', flowY - flowRadius * Math.sin(angle))
            .attr('stroke', THEME.arrowColor)
            .attr('stroke-width', 3);
        
        // Flow steps
        if (flow.steps && Array.isArray(flow.steps)) {
            flow.steps.forEach((step, j) => {
                const stepDistance = 80;
                const stepAngle = angle + (j - (flow.steps.length - 1) / 2) * 0.3;
                const stepX = flowX + stepDistance * Math.cos(stepAngle);
                const stepY = flowY + stepDistance * Math.sin(stepAngle);
                
                const stepRadius = getTextRadius(step, THEME.fontStep, 15);
                svg.append('rect')
                    .attr('x', stepX - stepRadius)
                    .attr('y', stepY - stepRadius * 0.6)
                    .attr('width', stepRadius * 2)
                    .attr('height', stepRadius * 1.2)
                    .attr('rx', 3)
                    .attr('fill', THEME.stepFill)
                    .attr('stroke', THEME.stepText)
                    .attr('stroke-width', 1);
                
                svg.append('text')
                    .attr('x', stepX)
                    .attr('y', stepY)
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', THEME.stepText)
                    .attr('font-size', THEME.fontStep)
                    .text(step);
                
                // Connection to flow topic
                svg.append('line')
                    .attr('x1', flowX + flowRadius * Math.cos(stepAngle))
                    .attr('y1', flowY + flowRadius * Math.sin(stepAngle))
                    .attr('x2', stepX - stepRadius * Math.cos(stepAngle))
                    .attr('y2', stepY - stepRadius * 0.6 * Math.sin(stepAngle))
                    .attr('stroke', THEME.arrowColor)
                    .attr('stroke-width', 1)
                    .attr('stroke-dasharray', '3,3');
            });
        }
    });
    
    // Watermark
    addWatermark(svg, theme);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.FlowRenderer = {
        renderFlowchart,
        renderFlowMap,
        renderBridgeMap,
        renderMultiFlowMap
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderFlowchart,
        renderFlowMap,
        renderBridgeMap,
        renderMultiFlowMap
    };
}
