/**
 * Brace Map Renderer for MindGraph
 * 
 * This module contains the brace map rendering function.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~30KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found! Please load shared-utilities.js first.');
}

// Import required functions from shared utilities - with error handling
let getTextRadius, addWatermark, getThemeDefaults;
try {
    getTextRadius = window.MindGraphUtils.getTextRadius;
    addWatermark = window.MindGraphUtils.addWatermark;
    getThemeDefaults = window.MindGraphUtils.getThemeDefaults;
    
    if (typeof getTextRadius !== 'function' || typeof addWatermark !== 'function' || typeof getThemeDefaults !== 'function') {
        throw new Error('Required functions not available from shared-utilities.js');
    }
} catch (error) {
    console.error('Failed to import required functions:', error);
    throw new Error('Failed to import required functions from shared-utilities.js');
}

function renderBraceMap(spec, theme = null, dimensions = null) {
    console.log('renderBraceMap called with:', { spec, theme, dimensions });
    
    // Clear container and ensure it exists
    const container = d3.select('#d3-container');
    if (container.empty()) {
        console.error('d3-container not found');
        return;
    }
    container.html('');
    
    // Validate spec
    if (!spec || !spec.topic || !Array.isArray(spec.parts)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for brace map');
        return;
    }
    
    // Use provided dimensions only - no hardcoded defaults
    const padding = dimensions?.padding || 40;
    
    // Get complete theme using robust style manager
    let THEME;
    try {
        if (typeof styleManager !== 'undefined' && styleManager.getTheme) {
            THEME = styleManager.getTheme('brace_map', theme, theme);
        } else {
            console.warn('Style manager not available, using fallback theme');
            THEME = {
                topicFill: '#e3f2fd',
                topicText: '#000000',
                topicStroke: '#35506b',
                partFill: '#f5f5f5',
                partText: '#333333',
                partStroke: '#cccccc',
                subpartFill: '#fafafa',
                subpartText: '#666666',
                subpartStroke: '#dddddd',
                fontTopic: '24px Inter, sans-serif',
                fontPart: '18px Inter, sans-serif',
                fontSubpart: '14px Inter, sans-serif',
                background: '#ffffff',
                braceColor: '#666666',
                braceWidth: 3
            };
        }
    } catch (error) {
        console.error('Error getting theme from style manager:', error);
        THEME = {
            topicFill: '#e3f2fd',
            topicText: '#000000',
            topicStroke: '#35506b',
            partFill: '#f5f5f5',
            partText: '#333333',
            partStroke: '#cccccc',
            subpartFill: '#fafafa',
            subpartText: '#666666',
            subpartStroke: '#dddddd',
            fontTopic: '24px Inter, sans-serif',
            fontPart: '18px Inter, sans-serif',
            fontSubpart: '14px Inter, sans-serif',
            background: '#ffffff',
            braceColor: '#666666',
            braceWidth: 3
        };
    }
    
    // Apply background if specified
    if (theme && theme.background) {
        d3.select('#d3-container').style('background-color', theme.background);
    }
    
    // Helpers to measure text width using a temporary hidden SVG text node
    function parseFontSpec(fontSpec) {
        // Expect formats like "24px Inter, sans-serif"
        const match = typeof fontSpec === 'string' ? fontSpec.match(/^(\\d+)px\\s+(.+)$/) : null;
        if (match) {
            return { size: parseInt(match[1], 10), family: match[2] };
        }
        // Fallbacks
        return { size: 16, family: 'Inter, sans-serif' };
    }
    
    function measureTextWidth(text, fontSpec, fontWeight = 'normal') {
        const { size, family } = parseFontSpec(fontSpec);
        // Create a temporary hidden SVG for measurement
        const tempSvg = d3.select('#d3-container')
            .append('svg')
            .attr('width', 0)
            .attr('height', 0)
            .style('position', 'absolute')
            .style('visibility', 'hidden');
        const tempText = tempSvg.append('text')
            .text(text || '')
            .attr('font-size', size)
            .attr('font-family', family)
            .style('font-weight', fontWeight);
        const bbox = tempText.node().getBBox();
        tempSvg.remove();
        return Math.max(0, bbox?.width || 0);
    }

    // Helper to build a curly brace path opening to the right
    function buildCurlyBracePath(braceX, yTop, yBottom, depth) {
        const height = Math.max(0, yBottom - yTop);
        if (height <= 0 || depth <= 0) return '';
        const yMid = (yTop + yBottom) / 2;
        const d1 = height * 0.18;
        const d2 = height * 0.12;
        const mid = height * 0.08;
        return `M ${braceX} ${yTop}
                C ${braceX} ${yTop + d2} ${braceX + depth} ${yTop + d1} ${braceX + depth} ${yMid - mid}
                C ${braceX + depth} ${yMid - mid/2} ${braceX} ${yMid} ${braceX} ${yMid}
                C ${braceX} ${yMid} ${braceX + depth} ${yMid + mid/2} ${braceX + depth} ${yBottom - d1}
                C ${braceX + depth} ${yBottom - d2} ${braceX} ${yBottom - d2/2} ${braceX} ${yBottom}`;
    }

    // Measure content widths
    const topicWidth = measureTextWidth(spec.topic, THEME.fontTopic, 'bold');
    const partWidths = (spec.parts || []).map(p => measureTextWidth(p?.name || '', THEME.fontPart, 'bold'));
    const maxPartWidth = Math.max(100, ...(partWidths.length ? partWidths : [0]));
    const subpartWidths = [];
    (spec.parts || []).forEach(p => {
        (p.subparts || []).forEach(sp => {
            subpartWidths.push(measureTextWidth(sp?.name || '', THEME.fontSubpart));
        });
    });
    const maxSubpartWidth = Math.max(100, ...(subpartWidths.length ? subpartWidths : [0]));

    // Define brace corridors and inter-column spacing
    const mainBraceCorridor = 40;  // space allocated for the big brace visuals
    const smallBraceCorridor = 30; // space allocated for small braces
    const columnSpacing = 30;      // spacing between columns

    // Compute X positions by summing column widths and spacing
    let runningX = padding;
    const column1X = runningX + topicWidth / 2; // Topic
    runningX += topicWidth + columnSpacing;
    const column2X = runningX + mainBraceCorridor / 2; // Big brace
    runningX += mainBraceCorridor + columnSpacing;
    const column3X = runningX + maxPartWidth / 2; // Parts
    runningX += maxPartWidth + columnSpacing;
    const column4X = runningX + smallBraceCorridor / 2; // Small brace
    runningX += smallBraceCorridor + columnSpacing;
    const column5X = runningX + maxSubpartWidth / 2; // Subparts
    runningX += maxSubpartWidth;
    
    // Calculate vertical spacing
    const partSpacing = 80;
    const subpartSpacing = 30;
    
    // Calculate total required height
    const { size: topicFontSize } = parseFontSpec(THEME.fontTopic);
    const { size: partFontSize } = parseFontSpec(THEME.fontPart);
    const { size: subpartFontSize } = parseFontSpec(THEME.fontSubpart);
    
    const topicHeight = topicFontSize + 20;
    let totalPartsHeight = 0;
    (spec.parts || []).forEach(part => {
        totalPartsHeight += partFontSize + 20; // part height
        if (part.subparts && part.subparts.length > 0) {
            totalPartsHeight += (part.subparts.length * (subpartFontSize + 10)) + 10; // subparts height
        }
        totalPartsHeight += partSpacing; // spacing between parts
    });
    
    const totalHeight = padding + topicHeight + 60 + totalPartsHeight + padding;
    const totalWidth = runningX + padding;
    
    // Create SVG with calculated dimensions
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', totalWidth)
        .attr('height', totalHeight)
        .attr('viewBox', `0 0 ${totalWidth} ${totalHeight}`)
        .attr('preserveAspectRatio', 'xMinYMin meet');

    // Draw topic
    const topicY = padding + topicHeight / 2;
    const topicBoxWidth = topicWidth + 40;
    const topicBoxHeight = topicHeight;
    
    svg.append('rect')
        .attr('x', column1X - topicBoxWidth / 2)
        .attr('y', topicY - topicBoxHeight / 2)
        .attr('width', topicBoxWidth)
        .attr('height', topicBoxHeight)
        .attr('rx', 8)
        .attr('fill', THEME.topicFill)
        .attr('stroke', THEME.topicStroke)
        .attr('stroke-width', 2);
    
    svg.append('text')
        .attr('x', column1X)
        .attr('y', topicY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.topicText)
        .attr('font-size', topicFontSize)
        .attr('font-family', parseFontSpec(THEME.fontTopic).family)
        .attr('font-weight', 'bold')
        .text(spec.topic);

    // Draw parts and subparts
    let currentY = topicY + topicHeight / 2 + 60;
    const partsStartY = currentY;
    let partsEndY = currentY;

    (spec.parts || []).forEach((part, partIndex) => {
        const partY = currentY + partFontSize / 2 + 10;
        const partBoxWidth = maxPartWidth + 20;
        const partBoxHeight = partFontSize + 20;
        
        // Draw part
        svg.append('rect')
            .attr('x', column3X - partBoxWidth / 2)
            .attr('y', partY - partBoxHeight / 2)
            .attr('width', partBoxWidth)
            .attr('height', partBoxHeight)
            .attr('rx', 5)
            .attr('fill', THEME.partFill)
            .attr('stroke', THEME.partStroke)
            .attr('stroke-width', 1);
        
        svg.append('text')
            .attr('x', column3X)
            .attr('y', partY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.partText)
            .attr('font-size', partFontSize)
            .attr('font-family', parseFontSpec(THEME.fontPart).family)
            .attr('font-weight', 'bold')
            .text(part.name || '');

        currentY += partBoxHeight + 10;

        // Draw subparts if they exist
        if (part.subparts && part.subparts.length > 0) {
            const subpartsStartY = currentY;
            
            part.subparts.forEach((subpart, subpartIndex) => {
                const subpartY = currentY + subpartFontSize / 2 + 5;
                const subpartBoxWidth = maxSubpartWidth + 15;
                const subpartBoxHeight = subpartFontSize + 10;
                
                svg.append('rect')
                    .attr('x', column5X - subpartBoxWidth / 2)
                    .attr('y', subpartY - subpartBoxHeight / 2)
                    .attr('width', subpartBoxWidth)
                    .attr('height', subpartBoxHeight)
                    .attr('rx', 3)
                    .attr('fill', THEME.subpartFill)
                    .attr('stroke', THEME.subpartStroke)
                    .attr('stroke-width', 1);
                
                svg.append('text')
                    .attr('x', column5X)
                    .attr('y', subpartY)
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', THEME.subpartText)
                    .attr('font-size', subpartFontSize)
                    .attr('font-family', parseFontSpec(THEME.fontSubpart).family)
                    .text(subpart.name || '');

                currentY += subpartBoxHeight + 5;
            });

            // Draw small brace for subparts
            const subpartsEndY = currentY - 5;
            if (subpartsEndY > subpartsStartY) {
                const bracePath = buildCurlyBracePath(
                    column4X - smallBraceCorridor / 2,
                    subpartsStartY,
                    subpartsEndY,
                    smallBraceCorridor / 2
                );
                
                svg.append('path')
                    .attr('d', bracePath)
                    .attr('fill', 'none')
                    .attr('stroke', THEME.braceColor)
                    .attr('stroke-width', THEME.braceWidth / 2);
            }
        }

        currentY += partSpacing;
        partsEndY = currentY - partSpacing / 2;
    });

    // Draw main brace
    if (partsEndY > partsStartY) {
        const bracePath = buildCurlyBracePath(
            column2X - mainBraceCorridor / 2,
            partsStartY,
            partsEndY,
            mainBraceCorridor / 2
        );
        
        svg.append('path')
            .attr('d', bracePath)
            .attr('fill', 'none')
            .attr('stroke', THEME.braceColor)
            .attr('stroke-width', THEME.braceWidth);
    }

    // Watermark - matching mindmap style
    const watermarkText = 'MindGraph';
    
    // Get SVG dimensions
    const w = +svg.attr('width');
    const h = +svg.attr('height');
    
    // Check if SVG uses viewBox
    const viewBox = svg.attr('viewBox');
    let watermarkX, watermarkY, watermarkFontSize;
    
    if (viewBox) {
        // SVG uses viewBox - position within viewBox coordinate system
        const viewBoxParts = viewBox.split(' ').map(Number);
        const viewBoxWidth = viewBoxParts[2];
        const viewBoxHeight = viewBoxParts[3];
        
        // Calculate font size based on viewBox dimensions
        watermarkFontSize = Math.max(8, Math.min(16, Math.min(viewBoxWidth, viewBoxHeight) * 0.02));
        
        // Calculate padding based on viewBox size
        const padding = Math.max(5, Math.min(15, Math.min(viewBoxWidth, viewBoxHeight) * 0.01));
        
        // Position in lower right corner of viewBox
        watermarkX = viewBoxParts[0] + viewBoxWidth - padding;
        watermarkY = viewBoxParts[1] + viewBoxHeight - padding;
    } else {
        // SVG uses standard coordinate system
        watermarkFontSize = Math.max(12, Math.min(20, Math.min(w, h) * 0.025));
        const padding = Math.max(10, Math.min(20, Math.min(w, h) * 0.02));
        watermarkX = w - padding;
        watermarkY = h - padding;
    }
    
    // Add watermark with proper styling - matching mindmap
    svg.append('text')
        .attr('x', watermarkX)
        .attr('y', watermarkY)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'alphabetic')
        .attr('fill', '#2c3e50')  // Original dark blue-grey color
        .attr('font-size', watermarkFontSize)
        .attr('font-family', 'Inter, Segoe UI, sans-serif')
        .attr('font-weight', '500')
        .attr('opacity', 0.8)     // Original 80% opacity
        .attr('pointer-events', 'none')
        .text(watermarkText);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.BraceRenderer = {
        renderBraceMap
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderBraceMap
    };
}
