/**
 * Venn Diagram Renderer for MindGraph
 * 
 * This module contains the Venn diagram rendering function.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~25KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found! Please load shared-utilities.js first.');
}

const { getTextRadius, addWatermark, getThemeDefaults } = window.MindGraphUtils;

function renderVennDiagram(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    
    // Validate spec
    if (!spec || !Array.isArray(spec.sets) || spec.sets.length < 2) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for venn diagram - need at least 2 sets');
        return;
    }
    
    // Use provided theme and dimensions or defaults
    const baseWidth = dimensions?.baseWidth || 800;
    const baseHeight = dimensions?.baseHeight || 600;
    const padding = dimensions?.padding || 40;
    
    // Get theme using style manager
    let THEME;
    try {
        if (typeof styleManager !== 'undefined' && styleManager.getTheme) {
            THEME = styleManager.getTheme('venn_diagram', theme, theme);
        } else {
            console.warn('Style manager not available, using fallback theme');
            THEME = {
                set1Fill: '#ff6b6b',   // Red for first set
                set1Text: '#ffffff',    // White text
                set1Stroke: '#c44569',  // Darker red border
                set1StrokeWidth: 2,
                set2Fill: '#4ecdc4',   // Teal for second set
                set2Text: '#ffffff',    // White text
                set2Stroke: '#26a69a',  // Darker teal border
                set2StrokeWidth: 2,
                set3Fill: '#45b7d1',   // Blue for third set
                set3Text: '#ffffff',    // White text
                set3Stroke: '#2c3e50',  // Darker blue border
                set3StrokeWidth: 2,
                intersectionFill: '#a8e6cf', // Light green for intersections
                intersectionText: '#333333',  // Dark text
                fontSet: 16,
                fontIntersection: 14
            };
        }
    } catch (error) {
        console.error('Error getting theme from style manager:', error);
        THEME = {
            set1Fill: '#ff6b6b',   // Red for first set
            set1Text: '#ffffff',    // White text
            set1Stroke: '#c44569',  // Darker red border
            set1StrokeWidth: 2,
            set2Fill: '#4ecdc4',   // Teal for second set
            set2Text: '#ffffff',    // White text
            set2Stroke: '#26a69a',  // Darker teal border
            set2StrokeWidth: 2,
            set3Fill: '#45b7d1',   // Blue for third set
            set3Text: '#ffffff',    // White text
            set3Stroke: '#2c3e50',  // Darker blue border
            set3StrokeWidth: 2,
            intersectionFill: '#a8e6cf', // Light green for intersections
            intersectionText: '#333333',  // Dark text
            fontSet: 16,
            fontIntersection: 14
        };
    }
    
    const width = baseWidth;
    const height = baseHeight;
    var svg = d3.select('#d3-container').append('svg').attr('width', width).attr('height', height);
    
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 120;
    
    if (spec.sets.length === 2) {
        // Two-set Venn diagram
        const set1X = centerX - radius * 0.6;
        const set1Y = centerY;
        const set2X = centerX + radius * 0.6;
        const set2Y = centerY;
        
        // Draw circles with transparency for overlap
        svg.append('circle')
            .attr('cx', set1X)
            .attr('cy', set1Y)
            .attr('r', radius)
            .attr('fill', THEME.set1Fill)
            .attr('stroke', THEME.set1Stroke)
            .attr('stroke-width', THEME.set1StrokeWidth)
            .attr('opacity', 0.7);
        
        svg.append('circle')
            .attr('cx', set2X)
            .attr('cy', set2Y)
            .attr('r', radius)
            .attr('fill', THEME.set2Fill)
            .attr('stroke', THEME.set2Stroke)
            .attr('stroke-width', THEME.set2StrokeWidth)
            .attr('opacity', 0.7);
        
        // Draw set labels
        svg.append('text')
            .attr('x', set1X - radius * 0.8)
            .attr('y', set1Y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.set1Text)
            .attr('font-size', THEME.fontSet)
            .attr('font-weight', 'bold')
            .text(spec.sets[0].name);
        
        svg.append('text')
            .attr('x', set2X + radius * 0.8)
            .attr('y', set2Y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.set2Text)
            .attr('font-size', THEME.fontSet)
            .attr('font-weight', 'bold')
            .text(spec.sets[1].name);
        
        // Draw intersection label
        svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.intersectionText)
            .attr('font-size', THEME.fontIntersection)
            .text(spec.sets[0].intersection || 'A ∩ B');
        
    } else if (spec.sets.length === 3) {
        // Three-set Venn diagram
        const set1X = centerX - radius * 0.8;
        const set1Y = centerY - radius * 0.4;
        const set2X = centerX + radius * 0.8;
        const set2Y = centerY - radius * 0.4;
        const set3X = centerX;
        const set3Y = centerY + radius * 0.6;
        
        // Draw circles with transparency
        svg.append('circle')
            .attr('cx', set1X)
            .attr('cy', set1Y)
            .attr('r', radius)
            .attr('fill', THEME.set1Fill)
            .attr('stroke', THEME.set1Stroke)
            .attr('stroke-width', THEME.set1StrokeWidth)
            .attr('opacity', 0.6);
        
        svg.append('circle')
            .attr('cx', set2X)
            .attr('cy', set2Y)
            .attr('r', radius)
            .attr('fill', THEME.set2Fill)
            .attr('stroke', THEME.set2Stroke)
            .attr('stroke-width', THEME.set2StrokeWidth)
            .attr('opacity', 0.6);
        
        svg.append('circle')
            .attr('cx', set3X)
            .attr('cy', set3Y)
            .attr('r', radius)
            .attr('fill', THEME.set3Fill)
            .attr('stroke', THEME.set3Stroke)
            .attr('stroke-width', THEME.set3StrokeWidth)
            .attr('opacity', 0.6);
        
        // Draw set labels
        svg.append('text')
            .attr('x', set1X - radius * 0.8)
            .attr('y', set1Y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.set1Text)
            .attr('font-size', THEME.fontSet)
            .attr('font-weight', 'bold')
            .text(spec.sets[0].name);
        
        svg.append('text')
            .attr('x', set2X + radius * 0.8)
            .attr('y', set2Y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.set2Text)
            .attr('font-size', THEME.fontSet)
            .attr('font-weight', 'bold')
            .text(spec.sets[1].name);
        
        svg.append('text')
            .attr('x', set3X)
            .attr('y', set3Y + radius * 0.8)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.set3Text)
            .attr('font-size', THEME.fontSet)
            .attr('font-weight', 'bold')
            .text(spec.sets[2].name);
        
        // Draw intersection labels
        svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY - radius * 0.2)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.intersectionText)
            .attr('font-size', THEME.fontIntersection)
            .text('A ∩ B ∩ C');
        
    } else {
        // For more than 3 sets, show a simplified version
        const angleStep = (2 * Math.PI) / spec.sets.length;
        const circleRadius = Math.min(radius, 200 / spec.sets.length);
        const orbitRadius = radius * 1.5;
        
        spec.sets.forEach((set, i) => {
            const angle = i * angleStep;
            const x = centerX + orbitRadius * Math.cos(angle);
            const y = centerY + orbitRadius * Math.sin(angle);
            
            const colors = [THEME.set1Fill, THEME.set2Fill, THEME.set3Fill];
            const fillColor = colors[i % colors.length];
            const textColor = i % 3 === 0 ? THEME.set1Text : (i % 3 === 1 ? THEME.set2Text : THEME.set3Text);
            
            svg.append('circle')
                .attr('cx', x)
                .attr('cy', y)
                .attr('r', circleRadius)
                .attr('fill', fillColor)
                .attr('stroke', THEME.set1Stroke)
                .attr('stroke-width', 2)
                .attr('opacity', 0.7);
            
            svg.append('text')
                .attr('x', x)
                .attr('y', y)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', textColor)
                .attr('font-size', THEME.fontSet)
                .attr('font-weight', 'bold')
                .text(set.name);
        });
        
        // Central intersection
        svg.append('circle')
            .attr('cx', centerX)
            .attr('cy', centerY)
            .attr('r', circleRadius * 0.6)
            .attr('fill', THEME.intersectionFill)
            .attr('stroke', THEME.intersectionText)
            .attr('stroke-width', 2)
            .attr('opacity', 0.8);
        
        svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.intersectionText)
            .attr('font-size', THEME.fontIntersection)
            .text('∩');
    }
    
    // Watermark
    addWatermark(svg, theme);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.VennRenderer = {
        renderVennDiagram
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderVennDiagram
    };
}
