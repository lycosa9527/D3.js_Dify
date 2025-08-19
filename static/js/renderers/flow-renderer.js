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
                processFill: '#1976d2',
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
            processFill: '#1976d2',
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
    if (typeof window.MindGraphUtils !== 'undefined' && window.MindGraphUtils.addWatermark) {
        window.MindGraphUtils.addWatermark(svg, theme);
    }
}

function renderFlowMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');

    // Validate spec
    if (!spec || !spec.title || !Array.isArray(spec.steps)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for flow map');
        return;
    }

    // Use provided padding from dimensions; width/height will be computed from content
    const padding = dimensions?.padding || 40;

    const THEME = {
        titleFill: '#1976d2',
        titleText: '#333',  // Changed from white to dark gray/black for better readability
        titleStroke: '#0d47a1',
        titleStrokeWidth: 3,
        stepFill: '#1976d2',      // Deep blue for step nodes (matching bubble map)
        stepText: '#ffffff',      // White text for step nodes
        stepStroke: '#0d47a1',    // Darker blue border for step nodes
        stepStrokeWidth: 2,
        substepFill: '#e3f2fd',   // Light blue for substep nodes (matching bubble map)
        substepText: '#333333',   // Dark text for substep nodes
        substepStroke: '#1976d2', // Blue border for substep nodes
        fontTitle: 20,            // Match bubble map's fontTopic size
        fontStep: 14,             // Match bubble map's fontAttribute size
        fontFamily: 'Inter, Segoe UI, sans-serif', // Match bubble map font family
        hPadTitle: 12,
        vPadTitle: 8,
        hPadStep: 14,
        vPadStep: 10,
        stepSpacing: 80,
        rectRadius: 8,
        ...theme
    };

    // Apply integrated styles if available
    if (theme) {
        if (theme.titleColor) THEME.titleFill = theme.titleColor;
        if (theme.titleTextColor) THEME.titleText = theme.titleTextColor;
        if (theme.stroke) THEME.titleStroke = theme.stroke;
        if (theme.strokeWidth) THEME.titleStrokeWidth = theme.strokeWidth;
        if (theme.stepColor) THEME.stepFill = theme.stepColor;
        if (theme.stepTextColor) THEME.stepText = theme.stepTextColor;
        if (theme.titleFontSize) THEME.fontTitle = theme.titleFontSize;
        if (theme.stepFontSize) THEME.fontStep = theme.stepFontSize;

        if (theme.background) {
            d3.select('#d3-container').style('background-color', theme.background);
        }
    }

    // Create a temporary SVG for measuring text
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

    // Measure title and steps to compute adaptive sizes (vertical layout)
    const titleSize = measureTextSize(spec.title, THEME.fontTitle);
    const stepSizes = spec.steps.map(s => {
        const m = measureTextSize(s, THEME.fontStep);
        return {
            text: s,
            w: Math.max(100, m.w + THEME.hPadStep * 2),
            h: Math.max(42, m.h + THEME.vPadStep * 2)
        };
    });

    // Build substeps mapping and measurements per step
    const stepToSubsteps = {};
    if (Array.isArray(spec.substeps)) {
        spec.substeps.forEach(entry => {
            if (!entry || typeof entry !== 'object') return;
            const stepName = entry.step;
            const subs = Array.isArray(entry.substeps) ? entry.substeps : [];
            if (typeof stepName === 'string' && subs.length) {
                stepToSubsteps[stepName] = subs;
            }
        });
    }
    const subSpacing = 30; // Increased further to prevent overlap
    const subOffsetX = 40; // gap between step rect and substeps group
    const subNodesPerStep = stepSizes.map(stepObj => {
        const subs = stepToSubsteps[stepObj.text] || [];
        return subs.map(txt => {
            const m = measureTextSize(txt, THEME.fontStep);
            return {
                text: txt,
                w: Math.max(80, m.w + THEME.hPadStep * 2),
                h: Math.max(28, m.h + THEME.vPadStep * 2)
            };
        });
    });
    const subGroupWidths = subNodesPerStep.map(nodes => nodes.length ? nodes.reduce((mx, n) => Math.max(mx, n.w), 0) : 0);
    const subGroupHeights = subNodesPerStep.map(nodes => {
        if (!nodes.length) return 0;
        const totalH = nodes.reduce((sum, n) => sum + n.h, 0);
        const spacing = Math.max(0, nodes.length - 1) * subSpacing;
        return totalH + spacing;
    });

    const maxStepWidth = stepSizes.reduce((mw, s) => Math.max(mw, s.w), 0);
    const maxSubGroupWidth = subGroupWidths.reduce((mw, w) => Math.max(mw, w), 0);
    const totalStepsHeight = stepSizes.reduce((sum, s) => sum + s.h, 0);
    
    // Calculate adaptive spacing based on substep heights (simplified)
    let totalVerticalSpacing = 0;
    if (stepSizes.length > 1) {
        for (let i = 0; i < stepSizes.length - 1; i++) {
            const currentStepSubHeight = subGroupHeights[i] || 0;
            const nextStepSubHeight = subGroupHeights[i + 1] || 0;
            
            // Use more efficient spacing calculation
            const maxSubHeight = Math.max(currentStepSubHeight, nextStepSubHeight);
            const minBaseSpacing = 45; // Reduced from 60
            const adaptiveSpacing = maxSubHeight > 0 ? Math.max(minBaseSpacing, maxSubHeight * 0.4 + 20) : minBaseSpacing;
            
            totalVerticalSpacing += adaptiveSpacing;
        }
    }

    // Calculate initial width estimate (will be refined after substep positioning)
    const rightSideWidth = maxSubGroupWidth > 0 ? (subOffsetX + maxSubGroupWidth) : 0;
    const extraPadding = 20; // Additional safety margin for text rendering
    const initialWidth = Math.max(titleSize.w, maxStepWidth + rightSideWidth) + padding * 2 + extraPadding;
    
    // Use agent recommendations as minimum for initial sizing
    let baseWidth, baseHeight;
    if (dimensions && dimensions.baseWidth && dimensions.baseHeight) {
        baseWidth = Math.max(dimensions.baseWidth, initialWidth);
        baseHeight = dimensions.baseHeight; // Will be updated after substep positioning
    } else {
        baseWidth = initialWidth;
        baseHeight = 600; // Initial estimate, will be updated
    }

    // Clean up temp svg (measurement SVG)
    tempSvg.remove();

    const centerX = baseWidth / 2;
    const startY = padding + titleSize.h + THEME.vPadTitle + 10; // Further reduced from 20 to 10

    // Size container to content to avoid external CSS constraining the SVG
    d3.select('#d3-container')
        .style('width', baseWidth + 'px')
        .style('height', baseHeight + 'px');

    // Create actual SVG
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMinYMin meet');

    // Draw title at the top - centered to the canvas width, not the step nodes
    const titleY = padding + titleSize.h; // baseline roughly below top padding
    svg.append('text')
        .attr('x', baseWidth / 2)  // Center to canvas width
        .attr('y', titleY)
        .attr('text-anchor', 'middle')
        .attr('fill', THEME.titleText)
        .attr('font-size', THEME.fontTitle)
        .attr('font-family', THEME.fontFamily)  // Add font family to match bubble map
        .attr('font-weight', 'bold')
        .text(spec.title);

    // NEW APPROACH: Calculate all substep positions first, then position steps accordingly
    
    // Step 1: Calculate all substep node positions with perfect spacing
    const allSubstepPositions = [];
    let currentSubY = startY + 15; // Further reduced from 30 to 15
    
    for (let stepIdx = 0; stepIdx < stepSizes.length; stepIdx++) {
        const nodes = subNodesPerStep[stepIdx];
        const stepPositions = [];
        
        if (nodes.length > 0) {
            // Position each substep with proper spacing
            for (let nodeIdx = 0; nodeIdx < nodes.length; nodeIdx++) {
                const node = nodes[nodeIdx];
                stepPositions.push({
                    x: centerX + stepSizes[stepIdx].w / 2 + subOffsetX,
                    y: currentSubY,
                    w: node.w,
                    h: node.h,
                    text: node.text
                });
                currentSubY += node.h + subSpacing; // Perfect spacing, no overlap
            }
            // Add gap between substep groups (reduced)
            currentSubY += 10; // Reduced from 20 to 10
        }
        allSubstepPositions.push(stepPositions);
    }
    
    // Step 2: Position main steps to align with their substep groups
    const stepCenters = [];
    for (let stepIdx = 0; stepIdx < stepSizes.length; stepIdx++) {
        const substepGroup = allSubstepPositions[stepIdx];
        let stepYCenter;
        
        if (substepGroup.length > 0) {
            // Center step on its substep group
            const firstSubstepY = substepGroup[0].y;
            const lastSubstepY = substepGroup[substepGroup.length - 1].y + substepGroup[substepGroup.length - 1].h;
            stepYCenter = (firstSubstepY + lastSubstepY) / 2;
        } else {
            // No substeps - use sequential positioning with minimal spacing
            if (stepIdx === 0) {
                stepYCenter = startY + 15; // Further reduced from 30 to 15
            } else {
                // Position below previous step with minimum spacing
                const prevStepBottom = stepCenters[stepIdx - 1] + stepSizes[stepIdx - 1].h / 2;
                stepYCenter = prevStepBottom + 40 + stepSizes[stepIdx].h / 2; // Reduced from 60 to 40
            }
        }
        
        stepCenters.push(stepYCenter);
    }
    
    // Step 3: Draw main steps at calculated positions
    stepSizes.forEach((s, index) => {
        const stepXCenter = centerX;
        const stepYCenter = stepCenters[index];

        // Rect
        svg.append('rect')
            .attr('x', stepXCenter - s.w / 2)
            .attr('y', stepYCenter - s.h / 2)
            .attr('width', s.w)
            .attr('height', s.h)
            .attr('rx', THEME.rectRadius)
            .attr('fill', THEME.stepFill)        // Deep blue fill
            .attr('stroke', THEME.stepStroke)    // Darker blue border
            .attr('stroke-width', THEME.stepStrokeWidth);

        // Text
        svg.append('text')
            .attr('x', stepXCenter)
            .attr('y', stepYCenter)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.stepText)        // White text
            .attr('font-size', THEME.fontStep)
            .attr('font-family', THEME.fontFamily)  // Add font family to match bubble map
            .text(s.text);

        // Arrow to next step (if there is one)
        if (index < stepSizes.length - 1) {
            const nextStepYCenter = stepCenters[index + 1];
            const currentBottom = stepYCenter + s.h / 2 + 6;
            const nextTop = nextStepYCenter - stepSizes[index + 1].h / 2 - 6;
            
            if (nextTop > currentBottom) {
                svg.append('line')
                    .attr('x1', stepXCenter)
                    .attr('y1', currentBottom)
                    .attr('x2', stepXCenter)
                    .attr('y2', nextTop)
                    .attr('stroke', '#666')
                    .attr('stroke-width', 2);
                svg.append('polygon')
                    .attr('points', `${stepXCenter},${nextTop} ${stepXCenter - 5},${nextTop - 10} ${stepXCenter + 5},${nextTop - 10}`)
                    .attr('fill', '#666');
            }
        }
    });

    // Calculate accurate canvas dimensions based on actual content positions
    let contentBottom = 0;
    let contentRight = 0;
    
    // Find the bottom of main steps
    if (stepCenters.length > 0) {
        for (let i = 0; i < stepCenters.length; i++) {
            const stepBottom = stepCenters[i] + stepSizes[i].h / 2;
            const stepRight = centerX + stepSizes[i].w / 2;
            contentBottom = Math.max(contentBottom, stepBottom);
            contentRight = Math.max(contentRight, stepRight);
        }
    }
    
    // Find the bottom and right edge of substeps (which now control the layout)
    for (let stepIdx = 0; stepIdx < allSubstepPositions.length; stepIdx++) {
        const stepPositions = allSubstepPositions[stepIdx];
        for (let nodeIdx = 0; nodeIdx < stepPositions.length; nodeIdx++) {
            const substep = stepPositions[nodeIdx];
            const substepBottom = substep.y + substep.h;
            const substepRight = substep.x + substep.w;
            contentBottom = Math.max(contentBottom, substepBottom);
            contentRight = Math.max(contentRight, substepRight);
        }
    }
    
    // Calculate final dimensions with padding
    const calculatedHeight = contentBottom + padding;
    const calculatedWidth = contentRight + padding;
    
    // Step 4: Draw substeps using pre-calculated positions (no overlap possible!)
    allSubstepPositions.forEach((stepPositions, stepIdx) => {
        const stepYCenter = stepCenters[stepIdx];
        const stepRightX = centerX + stepSizes[stepIdx].w / 2;
        
        stepPositions.forEach((substep, nodeIdx) => {
            // Draw substep rectangle
            svg.append('rect')
                .attr('x', substep.x)
                .attr('y', substep.y)
                .attr('width', substep.w)
                .attr('height', substep.h)
                .attr('rx', Math.max(4, THEME.rectRadius - 2))
                .attr('fill', THEME.substepFill)        // Light blue fill
                .attr('stroke', THEME.substepStroke)    // Blue border
                .attr('stroke-width', Math.max(1, THEME.stepStrokeWidth - 1));
            
            // Draw substep text
            svg.append('text')
                .attr('x', substep.x + substep.w / 2)
                .attr('y', substep.y + substep.h / 2)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', THEME.substepText)        // Dark text for readability
                .attr('font-size', Math.max(12, THEME.fontStep - 1))
                .attr('font-family', THEME.fontFamily)  // Add font family to match bubble map
                .text(substep.text);
            
            // Draw L-shaped connector from step to substep
            const substepCenterY = substep.y + substep.h / 2;
            const midX = stepRightX + Math.max(8, subOffsetX / 2);
            
            // Horizontal line from step
            svg.append('line')
                .attr('x1', stepRightX)
                .attr('y1', stepYCenter)
                .attr('x2', midX)
                .attr('y2', stepYCenter)
                .attr('stroke', '#888')
                .attr('stroke-width', 1.5);
            
            // Vertical line to substep level
            svg.append('line')
                .attr('x1', midX)
                .attr('y1', stepYCenter)
                .attr('x2', midX)
                .attr('y2', substepCenterY)
                .attr('stroke', '#888')
                .attr('stroke-width', 1.5);
            
            // Horizontal line to substep
            svg.append('line')
                .attr('x1', midX)
                .attr('y1', substepCenterY)
                .attr('x2', substep.x)
                .attr('y2', substepCenterY)
                .attr('stroke', '#888')
                .attr('stroke-width', 1.5);
        });
    });
    
    // Update SVG dimensions to match calculated content
    if (calculatedWidth > baseWidth || calculatedHeight > baseHeight) {
        svg.attr('width', calculatedWidth)
           .attr('height', calculatedHeight)
           .attr('viewBox', `0 0 ${calculatedWidth} ${calculatedHeight}`);
        
        d3.select('#d3-container')
            .style('width', calculatedWidth + 'px')
            .style('height', calculatedHeight + 'px');
    }
    
    // Add watermark with same styling as bubble maps
    const watermarkText = theme?.watermarkText || 'MindGraph';
    const watermarkFontSize = Math.max(12, Math.min(20, Math.min(calculatedWidth, calculatedHeight) * 0.025));
    const watermarkPadding = Math.max(10, Math.min(20, Math.min(calculatedWidth, calculatedHeight) * 0.02));
    
    svg.append('text')
        .attr('x', calculatedWidth - watermarkPadding)
        .attr('y', calculatedHeight - watermarkPadding)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'alphabetic')
        .attr('fill', '#2c3e50')
        .attr('font-size', watermarkFontSize)
        .attr('font-family', 'Inter, Segoe UI, sans-serif')
        .attr('font-weight', '500')
        .attr('opacity', 0.8)
        .attr('pointer-events', 'none')
        .text(watermarkText);
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
        analogyFill: '#1976d2',
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
    if (typeof window.MindGraphUtils !== 'undefined' && window.MindGraphUtils.addWatermark) {
        window.MindGraphUtils.addWatermark(svg, theme);
    }
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
        flowFill: '#1976d2',
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
    const centralRadius = 25; // Fixed radius for simplicity
    
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
        const flowRadius = 20; // Fixed radius for simplicity
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
                
                const stepRadius = 15; // Fixed radius for simplicity
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
    if (typeof window.MindGraphUtils !== 'undefined' && window.MindGraphUtils.addWatermark) {
        window.MindGraphUtils.addWatermark(svg, theme);
    }
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
    
    // Also make these available as global functions for backward compatibility
    // This ensures the HTML can call renderFlowMap() directly
    window.renderFlowchart = renderFlowchart;
    window.renderFlowMap = renderFlowMap;
    window.renderBridgeMap = renderBridgeMap;
    window.renderMultiFlowMap = renderMultiFlowMap;
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderFlowchart,
        renderFlowMap,
        renderBridgeMap,
        renderMultiFlowMap
    };
}
