/**
 * Mind Map Renderer for MindGraph
 * 
 * This module provides standard mind map rendering using Python agent layout data.
 * - Always requires positioned layout from Python MindMapAgent
 * - Shows error message if Python agent fails (no fallback rendering)
 * 
 * Requires: shared-utilities.js, style-manager.js
 * Performance Impact: Loads only ~50KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found. Please load shared-utilities.js first.');
}

// Note: getTextRadius and addWatermark are available globally from shared-utilities.js

function renderMindMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.topic || !Array.isArray(spec.children)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for mindmap');
        return;
    }
    
    // Determine canvas dimensions
    let baseWidth, baseHeight, padding;
    
    if (spec._recommended_dimensions) {
        // Python agent dimensions
        baseWidth = spec._recommended_dimensions.width;
        baseHeight = spec._recommended_dimensions.height;
        padding = spec._recommended_dimensions.padding;
    } else if (dimensions) {
        // Provided dimensions
        baseWidth = dimensions.baseWidth || 700;
        baseHeight = dimensions.baseHeight || 500;
        padding = dimensions.padding || 40;
    } else {
        // Default dimensions
        baseWidth = 700;
        baseHeight = 500;
        padding = 40;
    }
    
    // Load theme
    let THEME;
    try {
        if (typeof styleManager !== 'undefined' && styleManager.getTheme) {
            THEME = styleManager.getTheme('mindmap', theme, theme);
        } else {
            console.warn('Style manager not available, using fallback theme');
            THEME = {
                centralNodeFill: '#e3f2fd',
                centralNodeText: '#000000',
                centralNodeStroke: '#35506b',
                centralNodeStrokeWidth: 3,
                childNodeFill: '#f5f5f5',
                childNodeText: '#333333',
                childNodeStroke: '#cccccc',
                branchFill: '#a7c7e7',
                branchText: '#333',
                branchStroke: '#4e79a7',
                branchStrokeWidth: 2,
                linkStroke: '#cccccc',
                fontCentral: '18px Inter, sans-serif',
                fontBranch: '16px Inter, sans-serif',
                fontChild: '14px Inter, sans-serif',
                background: '#ffffff'
            };
        }
    } catch (error) {
        console.error('Error getting theme from style manager:', error);
        THEME = {
            centralNodeFill: '#e3f2fd',
            centralNodeText: '#000000',
            centralNodeStroke: '#35506b',
            childNodeFill: '#f5f5f5',
            childNodeText: '#333333',
            childNodeStroke: '#cccccc',
            linkStroke: '#cccccc',
            fontCentral: '18px Inter, sans-serif',
            fontChild: '14px Inter, sans-serif',
            background: '#ffffff'
        };
    }
    
    // Apply container background
    const containerBackground = spec._layout?.params?.background || theme?.background || '#f5f5f5';
    d3.select('#d3-container')
        .style('background-color', containerBackground)
        .style('width', '100%')
        .style('height', '100%')
        .style('min-height', `${baseHeight}px`);
    
    const width = baseWidth;
    const height = baseHeight;
    var svg = d3.select('#d3-container').append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .style('background-color', containerBackground); // Use the same background color
    
    // Require Python agent layout data
    const centerX = width / 2;
    const centerY = height / 2;
    
    if (spec._layout && spec._layout.positions) {
        // Render with positioned layout
        renderMindMapWithLayout(spec._layout, svg, centerX, centerY, THEME);
    } else {
        // Error: No layout data
        d3.select('#d3-container').append('div')
            .style('color', 'red')
            .style('font-size', '18px')
            .style('text-align', 'center')
            .style('padding', '50px')
            .text('Error: Python MindMapAgent failed to provide layout data. No fallback rendering available.');
        console.error('Mindmap rendering failed: No layout data from Python agent');
        return;
    }
    
    // Watermark
    addWatermark(svg, theme);
}

function renderMindMapWithLayout(spec, svg, centerX, centerY, THEME) {
    const positions = spec.positions;
    const connections = spec.connections || [];
    
    // Begin rendering
    console.log(`Rendering mindmap: ${Object.keys(positions).length} nodes, ${connections.length} connections`);
    
    // Draw connections first
    if (connections.length > 0) {
        // Explicit connections
        connections.forEach(conn => {
            let fromPos, toPos;
            
            // Handle topic connections
            if (conn.from.type === 'topic') {
                fromPos = positions['topic'];
            } else if (conn.from.type === 'branch') {
                fromPos = positions[`branch_${conn.branch_index}`];
            }
            
            // Handle branch and child connections
            if (conn.to.type === 'branch') {
                toPos = positions[`branch_${conn.branch_index}`];
            } else if (conn.to.type === 'child') {
                // For child connections, we need both branch_index and child_index
                if (conn.child_index !== undefined) {
                    toPos = positions[`child_${conn.branch_index}_${conn.child_index}`];
                }
            }
            
            if (fromPos && toPos) {
                const fromX = centerX + fromPos.x;
                const fromY = centerY + fromPos.y;

                const fromWidth = fromPos.width || (fromPos.text ? Math.max(80, fromPos.text.length * 8) : 100);
                const fromHeight = fromPos.height || 50;
                
                const toX = centerX + toPos.x;
                const toY = centerY + toPos.y;
                const toWidth = toPos.width || (toPos.text ? Math.max(80, toPos.text.length * 8) : 100);
                const toHeight = toPos.height || 40;
                
                // Calculate line endpoints to stop at node boundaries
                const dx = toX - fromX;
                const dy = toY - fromY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist > 0) {
                    // Ensure lines start and end at node boundaries, not inside nodes
                    const lineStartX = fromX + (dx / dist) * (fromWidth / 2);
                    const lineStartY = fromY + (dy / dist) * (fromHeight / 2);
                    const lineEndX = toX - (dx / dist) * (toWidth / 2);
                    const lineEndY = toY - (dy / dist) * (toHeight / 2);
                    
                    svg.append('line')
                        .attr('x1', lineStartX)
                        .attr('y1', lineStartY)
                        .attr('x2', lineEndX)
                        .attr('y2', lineEndY)
                        .attr('stroke', conn.stroke_color || THEME.linkStroke || '#888')
                        .attr('stroke-width', conn.stroke_width || 2);
                }
            }
        });
    } else {
        // Infer connections from positions
        Object.keys(positions).forEach(key => {
            const pos = positions[key];
            
            if (pos.node_type === 'branch') {
                    // Draw connecting line from center to branch
                    const branchX = centerX + pos.x;
                    const branchY = centerY + pos.y;
    
                    const branchWidth = pos.width || (pos.text ? Math.max(100, pos.text.length * 10) : 100);
                    const branchHeight = pos.height || 50;
                    
                    const dx = branchX - centerX;
                    const dy = branchY - centerY;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    
                    if (dist > 0) {
                        // Calculate line endpoints to stop at node boundaries
                        // Use actual topic node dimensions instead of hardcoded 60px
                        const topicPos = positions['topic'];
                        const topicWidth = topicPos ? (topicPos.width || 120) : 120;
                        const topicHeight = topicPos ? (topicPos.height || 60) : 60;
                        
                        const lineStartX = centerX + (dx / dist) * (topicWidth / 2);
                        const lineStartY = centerY + (dy / dist) * (topicHeight / 2);
                        const lineEndX = branchX - (dx / dist) * (branchWidth / 2);
                        const lineEndY = branchY - (dy / dist) * (branchHeight / 2);
                        
                        svg.append('line')
                            .attr('x1', lineStartX)
                            .attr('y1', lineStartY)
                            .attr('x2', lineEndX)
                            .attr('y2', lineEndY)
                            .attr('stroke', THEME.linkStroke || '#888')
                        .attr('stroke-width', 2);
                    }
                } else if (pos.node_type === 'child') {
                    // Draw connecting line from branch to child
                    const childX = centerX + pos.x;
                    const childY = centerY + pos.y;
    
                    const childWidth = pos.width || (pos.text ? Math.max(80, pos.text.length * 8) : 100);
                    const childHeight = pos.height || 40;
                    
                    const branchKey = `branch_${pos.branch_index}`;
                    if (positions[branchKey]) {
                        const branchPos = positions[branchKey];
                        const branchX = centerX + branchPos.x;
                        const branchY = centerY + branchPos.y;
        
                        const branchWidth = branchPos.width || (branchPos.text ? Math.max(100, branchPos.text.length * 10) : 100);
                        const branchHeight = branchPos.height || 50;
                        
                        // Calculate line endpoints to stop at node boundaries
                        const dx = childX - branchX;
                        const dy = childY - branchY;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        
                        if (dist > 0) {
                            const lineStartX = branchX + (dx / dist) * (branchWidth / 2);
                            const lineStartY = branchY + (dy / dist) * (branchHeight / 2);
                            const lineEndX = childX - (dx / dist) * (childWidth / 2);
                            const lineEndY = childY - (dy / dist) * (childHeight / 2);
                            
        svg.append('line')
                                .attr('x1', lineStartX)
                                .attr('y1', lineStartY)
                                .attr('x2', lineEndX)
                                .attr('y2', lineEndY)
                                .attr('stroke', THEME.linkStroke || '#ccc')
            .attr('stroke-width', 1);
                        }
                    }
                }
            });
        }
        
        // Draw nodes on top
        Object.keys(positions).forEach(key => {
            const pos = positions[key];
            
            if (pos.node_type === 'topic') {
                // Central topic (circle)
                const topicX = centerX + pos.x;
                const topicY = centerY + pos.y;
                const topicWidth = pos.width || 120;
                const topicHeight = pos.height || 60;
                // Larger radius for visual balance
                const topicRadius = Math.max(topicWidth, topicHeight) / 2 * 1.3; // 30% larger for balanced size
                
    svg.append('circle')
                    .attr('cx', topicX)
                    .attr('cy', topicY)
                    .attr('r', topicRadius)
                    .attr('fill', pos.fill || THEME.centralNodeFill || '#1976d2')
                    .attr('stroke', pos.stroke || THEME.centralNodeStroke || '#0d47a1')
                    .attr('stroke-width', pos.stroke_width || 2);
    
    svg.append('text')
                    .attr('x', topicX)
                    .attr('y', topicY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
                    .attr('fill', pos.text_color || THEME.centralNodeText || '#ffffff')
                    .attr('font-size', THEME.fontCentral || '18px')
        .attr('font-weight', 'bold')
                    .text(pos.text || 'Topic');
                    
            } else if (pos.node_type === 'branch') {
                // Branch (rectangle)
                const branchX = centerX + pos.x;
                const branchY = centerY + pos.y;

                const branchWidth = pos.width || (pos.text ? Math.max(100, pos.text.length * 10) : 100);
                const branchHeight = pos.height || 50;
                
                // Draw rectangular node
                svg.append('rect')
                    .attr('x', branchX - branchWidth / 2)
                    .attr('y', branchY - branchHeight / 2)
                    .attr('width', branchWidth)
                    .attr('height', branchHeight)
                    .attr('rx', 8) // Rounded corners
                    .attr('ry', 8)
                    .attr('fill', pos.fill || THEME.branchFill || '#a7c7e7')
                    .attr('stroke', pos.stroke || THEME.branchStroke || '#4e79a7')
                    .attr('stroke-width', pos.stroke_width || THEME.branchStrokeWidth || 2);
    
    svg.append('text')
                    .attr('x', branchX)
                    .attr('y', branchY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
                    .attr('fill', pos.text_color || THEME.branchText || '#333')
                    .attr('font-size', THEME.fontBranch || '16px')
                    .text(pos.text || 'Branch');
                    
            } else if (pos.node_type === 'child') {
                // Child (rectangle)
                const childX = centerX + pos.x;
                const childY = centerY + pos.y;

                const childWidth = pos.width || (pos.text ? Math.max(80, pos.text.length * 8) : 100);
                const childHeight = pos.height || 40;
                
                // Draw rectangular node
                svg.append('rect')
                    .attr('x', childX - childWidth / 2)
                    .attr('y', childY - childHeight / 2)
                    .attr('width', childWidth)
                    .attr('height', childHeight)
                    .attr('rx', 6) // Rounded corners
                    .attr('ry', 6)
                    .attr('fill', pos.fill || THEME.childNodeFill || '#f5f5f5')
                    .attr('stroke', pos.stroke || THEME.childNodeStroke || '#cccccc')
                    .attr('stroke-width', pos.stroke_width || 1);
                
        svg.append('text')
                    .attr('x', childX)
                    .attr('y', childY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
                    .attr('fill', pos.text_color || THEME.childNodeText || '#333')
                    .attr('font-size', THEME.fontChild || '14px')
                    .text(pos.text || 'Child');
            }
        });
        
    console.log('Mindmap rendered successfully');
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.MindMapRenderer = {
        renderMindMap,
        renderMindMapWithLayout
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderMindMap,
        renderMindMapWithLayout
    };
}
