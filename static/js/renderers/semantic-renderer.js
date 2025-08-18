/**
 * Semantic Web Renderer for MindGraph
 * 
 * This module contains the semantic web rendering function.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~25KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found! Please load shared-utilities.js first.');
}

const { getTextRadius, addWatermark, getThemeDefaults } = window.MindGraphUtils;

function renderSemanticWeb(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    
    // Validate spec
    if (!spec || !spec.topic || !Array.isArray(spec.branches)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for semantic web');
        return;
    }
    
    // Use provided theme and dimensions or defaults
    const baseWidth = dimensions?.baseWidth || 800;
    const baseHeight = dimensions?.baseHeight || 600;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        topicFill: '#4e79a7',
        topicText: '#fff',
        topicStroke: '#35506b',
        topicStrokeWidth: 3,
        branchFill: '#a7c7e7',
        branchText: '#333',
        branchStroke: '#4e79a7',
        branchStrokeWidth: 2,
        subBranchFill: '#f4f6fb',
        subBranchText: '#333',
        subBranchStroke: '#4e79a7',
        subBranchStrokeWidth: 1,
        fontTopic: 20,
        fontBranch: 16,
        fontSubBranch: 14,
        ...theme
    };
    
    // Apply integrated styles if available
    if (theme) {
        if (theme.topicColor) THEME.topicFill = theme.topicColor;
        if (theme.topicTextColor) THEME.topicText = theme.topicTextColor;
        if (theme.stroke) THEME.topicStroke = theme.stroke;
        if (theme.strokeWidth) THEME.topicStrokeWidth = theme.strokeWidth;
        if (theme.branchColor) THEME.branchFill = theme.branchColor;
        if (theme.branchTextColor) THEME.branchText = theme.branchTextColor;
        if (theme.subBranchColor) THEME.subBranchFill = theme.subBranchColor;
        if (theme.subBranchTextColor) THEME.subBranchText = theme.subBranchTextColor;
        if (theme.topicFontSize) THEME.fontTopic = theme.topicFontSize;
        if (theme.branchFontSize) THEME.fontBranch = theme.branchFontSize;
        if (theme.subBranchFontSize) THEME.fontSubBranch = theme.subBranchFontSize;
        
        if (theme.background) {
            d3.select('#d3-container').style('background-color', theme.background);
        }
    }
    
    const width = baseWidth;
    const height = baseHeight;
    var svg = d3.select('#d3-container').append('svg').attr('width', width).attr('height', height);
    
    // Calculate layout
    const centerX = width / 2;
    const centerY = height / 2;
    const topicRadius = getTextRadius(spec.topic, THEME.fontTopic, 20);
    
    // Draw central topic
    svg.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', topicRadius)
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
    
    // Draw branches in a radial pattern
    const branchCount = spec.branches.length;
    const angleStep = (2 * Math.PI) / branchCount;
    const branchRadius = 120;
    
    spec.branches.forEach((branch, i) => {
        const angle = i * angleStep;
        const branchX = centerX + branchRadius * Math.cos(angle);
        const branchY = centerY + branchRadius * Math.sin(angle);
        const branchNodeRadius = getTextRadius(branch.name, THEME.fontBranch, 15);
        
        // Draw branch node
        svg.append('circle')
            .attr('cx', branchX)
            .attr('cy', branchY)
            .attr('r', branchNodeRadius)
            .attr('fill', THEME.branchFill)
            .attr('stroke', THEME.branchStroke)
            .attr('stroke-width', THEME.branchStrokeWidth);
        
        svg.append('text')
            .attr('x', branchX)
            .attr('y', branchY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.branchText)
            .attr('font-size', THEME.fontBranch)
            .text(branch.name);
        
        // Draw connecting line from topic to branch
        const dx = branchX - centerX;
        const dy = branchY - centerY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        const lineStartX = centerX + (dx / dist) * topicRadius;
        const lineStartY = centerY + (dy / dist) * topicRadius;
        const lineEndX = branchX - (dx / dist) * branchNodeRadius;
        const lineEndY = branchY - (dy / dist) * branchNodeRadius;
        
        svg.append('line')
            .attr('x1', lineStartX)
            .attr('y1', lineStartY)
            .attr('x2', lineEndX)
            .attr('y2', lineEndY)
            .attr('stroke', '#bbb')
            .attr('stroke-width', 2);
        
        // Draw sub-branches
        if (branch.children && branch.children.length > 0) {
            const subBranchCount = branch.children.length;
            const subAngleStep = Math.PI / (subBranchCount + 1);
            const subBranchRadius = 60;
            
            branch.children.forEach((subBranch, j) => {
                const subAngle = angle - Math.PI/2 + (j + 1) * subAngleStep;
                const subBranchX = branchX + subBranchRadius * Math.cos(subAngle);
                const subBranchY = branchY + subBranchRadius * Math.sin(subAngle);
                const subBranchNodeRadius = getTextRadius(subBranch.name, THEME.fontSubBranch, 10);
                
                // Draw sub-branch node
                svg.append('circle')
                    .attr('cx', subBranchX)
                    .attr('cy', subBranchY)
                    .attr('r', subBranchNodeRadius)
                    .attr('fill', THEME.subBranchFill)
                    .attr('stroke', THEME.subBranchStroke)
                    .attr('stroke-width', THEME.subBranchStrokeWidth);
                
                svg.append('text')
                    .attr('x', subBranchX)
                    .attr('y', subBranchY)
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', THEME.subBranchText)
                    .attr('font-size', THEME.fontSubBranch)
                    .text(subBranch.name);
                
                // Draw connecting line from branch to sub-branch
                const subDx = subBranchX - branchX;
                const subDy = subBranchY - branchY;
                const subDist = Math.sqrt(subDx * subDx + subDy * subDy);
                
                const subLineStartX = branchX + (subDx / subDist) * branchNodeRadius;
                const subLineStartY = branchY + (subDy / subDist) * branchNodeRadius;
                const subLineEndX = subBranchX - (subDx / subDist) * subBranchNodeRadius;
                const subLineEndY = subBranchY - (subDy / subDist) * subBranchNodeRadius;
                
                svg.append('line')
                    .attr('x1', subLineStartX)
                    .attr('y1', subLineStartY)
                    .attr('x2', subLineEndX)
                    .attr('y2', subLineEndY)
                    .attr('stroke', '#ccc')
                    .attr('stroke-width', 1);
            });
        }
    });
    
    // Watermark
    addWatermark(svg, theme);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.SemanticRenderer = {
        renderSemanticWeb
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderSemanticWeb
    };
}
