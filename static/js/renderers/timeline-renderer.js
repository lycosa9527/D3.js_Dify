/**
 * Timeline Renderer for MindGraph
 * 
 * This module contains the timeline rendering function.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~20KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found! Please load shared-utilities.js first.');
}

const { getTextRadius, addWatermark, getThemeDefaults } = window.MindGraphUtils;

function renderTimeline(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    
    // Validate spec
    if (!spec || !spec.title || !Array.isArray(spec.events)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for timeline');
        return;
    }
    
    // Use provided theme and dimensions or defaults
    const baseWidth = dimensions?.baseWidth || 900;
    const baseHeight = dimensions?.baseHeight || 400;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        titleFill: '#4e79a7',
        titleText: '#fff',
        titleStroke: '#35506b',
        titleStrokeWidth: 3,
        eventFill: '#a7c7e7',
        eventText: '#333',
        eventStroke: '#4e79a7',
        eventStrokeWidth: 2,
        lineColor: '#666',
        lineWidth: 3,
        fontTitle: 20,
        fontEvent: 14,
        fontDate: 12,
        ...theme
    };
    
    // Apply integrated styles if available
    if (theme) {
        if (theme.titleColor) THEME.titleFill = theme.titleColor;
        if (theme.titleTextColor) THEME.titleText = theme.titleTextColor;
        if (theme.eventColor) THEME.eventFill = theme.eventColor;
        if (theme.eventTextColor) THEME.eventText = theme.eventTextColor;
        if (theme.lineColor) THEME.lineColor = theme.lineColor;
        if (theme.titleFontSize) THEME.fontTitle = theme.titleFontSize;
        if (theme.eventFontSize) THEME.fontEvent = theme.eventFontSize;
        
        if (theme.background) {
            d3.select('#d3-container').style('background-color', theme.background);
        }
    }
    
    const width = baseWidth;
    const height = baseHeight;
    var svg = d3.select('#d3-container').append('svg').attr('width', width).attr('height', height);
    
    // Draw title
    const titleY = padding + 30;
    const titleRadius = getTextRadius(spec.title, THEME.fontTitle, 20);
    
    svg.append('circle')
        .attr('cx', width / 2)
        .attr('cy', titleY)
        .attr('r', titleRadius)
        .attr('fill', THEME.titleFill)
        .attr('stroke', THEME.titleStroke)
        .attr('stroke-width', THEME.titleStrokeWidth);
    
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', titleY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.titleText)
        .attr('font-size', THEME.fontTitle)
        .attr('font-weight', 'bold')
        .text(spec.title);
    
    // Draw timeline line
    const lineY = titleY + titleRadius + 60;
    const lineStartX = padding + 50;
    const lineEndX = width - padding - 50;
    
    svg.append('line')
        .attr('x1', lineStartX)
        .attr('y1', lineY)
        .attr('x2', lineEndX)
        .attr('y2', lineY)
        .attr('stroke', THEME.lineColor)
        .attr('stroke-width', THEME.lineWidth);
    
    // Draw events
    const eventCount = spec.events.length;
    const eventSpacing = (lineEndX - lineStartX) / (eventCount + 1);
    
    spec.events.forEach((event, i) => {
        const eventX = lineStartX + (i + 1) * eventSpacing;
        const eventY = lineY;
        const eventRadius = 8;
        
        // Draw event circle
        svg.append('circle')
            .attr('cx', eventX)
            .attr('cy', eventY)
            .attr('r', eventRadius)
            .attr('fill', THEME.eventFill)
            .attr('stroke', THEME.eventStroke)
            .attr('stroke-width', THEME.eventStrokeWidth);
        
        // Draw event label
        svg.append('text')
            .attr('x', eventX)
            .attr('y', eventY + 30)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.eventText)
            .attr('font-size', THEME.fontEvent)
            .attr('font-weight', 'bold')
            .text(event.title);
        
        // Draw event date
        if (event.date) {
            svg.append('text')
                .attr('x', eventX)
                .attr('y', eventY + 50)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', '#666')
                .attr('font-size', THEME.fontDate)
                .text(event.date);
        }
        
        // Draw event description
        if (event.description) {
            svg.append('text')
                .attr('x', eventX)
                .attr('y', eventY + 70)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', THEME.eventText)
                .attr('font-size', THEME.fontDate)
                .text(event.description);
        }
        
        // Draw connecting line to timeline
        svg.append('line')
            .attr('x1', eventX)
            .attr('y1', eventY - eventRadius)
            .attr('x2', eventX)
            .attr('y2', eventY + eventRadius)
            .attr('stroke', THEME.eventStroke)
            .attr('stroke-width', THEME.eventStrokeWidth);
    });
    
    // Draw arrow at the end of timeline
    const arrowSize = 8;
    svg.append('polygon')
        .attr('points', `${lineEndX},${lineY} ${lineEndX + arrowSize},${lineY - arrowSize/2} ${lineEndX + arrowSize},${lineY + arrowSize/2}`)
        .attr('fill', THEME.lineColor);
    
    // Watermark
    addWatermark(svg, theme);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.TimelineRenderer = {
        renderTimeline
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderTimeline
    };
}
