/**
 * Tree Renderer for MindGraph
 * 
 * This module contains the tree map rendering function.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~60KB instead of full 213KB
 */

// CRITICAL FIX: Add execution tracking
console.log('🌳 Tree renderer: Script execution started');
console.log('🌳 Tree renderer: Script location:', window.location.href);
console.log('🌳 Tree renderer: Current time:', new Date().toISOString());

// Check if shared utilities are available
console.log('🌳 Tree renderer: Checking dependencies...');
console.log('🌳 Tree renderer: window.MindGraphUtils available:', typeof window.MindGraphUtils);
console.log('🌳 Tree renderer: window.addWatermark available:', typeof window.addWatermark);

if (typeof window.MindGraphUtils === 'undefined') {
    console.error('🌳 Tree renderer: MindGraphUtils not found! Please load shared-utilities.js first.');
    // Don't continue if dependencies are missing
    throw new Error('MindGraphUtils not available - shared-utilities.js must be loaded first');
}

// Import required functions from shared utilities - with error handling
// CRITICAL FIX: Don't redeclare addWatermark, use the global one
if (typeof window.MindGraphUtils === 'undefined' || typeof window.MindGraphUtils.addWatermark !== 'function') {
    console.error('🌳 Tree renderer: addWatermark function not found in MindGraphUtils');
    throw new Error('addWatermark function not available - shared-utilities.js must be loaded first');
}

// Main tree map rendering function - EXPOSE TO GLOBAL SCOPE
function renderTreeMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    
    // Validate spec
    if (!spec || !spec.topic || !Array.isArray(spec.children)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for tree map');
        return;
    }
    
    // Handle empty children case
    if (spec.children.length === 0) {
        d3.select('#d3-container').append('div').style('color', 'orange').text('Tree map has no branches to display');
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
            THEME = styleManager.getTheme('tree_map', theme, theme);
        } else {
            console.warn('Style manager not available, using fallback theme');
            THEME = {
                rootFill: '#1976d2',  // Deeper blue
                rootText: '#ffffff',   // White text for contrast
                rootStroke: '#0d47a1', // Darker blue border
                rootStrokeWidth: 3,
                branchFill: '#e3f2fd', // Light blue for branches
                branchText: '#333333',  // Dark text
                branchStroke: '#1976d2', // Blue border
                branchStrokeWidth: 2,
                leafFill: '#f8f9fa',   // Very light blue for leaves
                leafText: '#333333',    // Dark text
                leafStroke: '#1976d2',  // Blue border
                leafStrokeWidth: 1,
                fontRoot: 20,
                fontBranch: 16,
                fontLeaf: 14
            };
        }
    } catch (error) {
        console.error('Error getting theme from style manager:', error);
        THEME = {
            rootFill: '#1976d2',
            rootText: '#ffffff',
            rootStroke: '#0d47a1',
            rootStrokeWidth: 3,
            branchFill: '#e3f2fd',
            branchText: '#333333',
            branchStroke: '#1976d2',
            branchStrokeWidth: 2,
            leafFill: '#f8f9fa',
            leafText: '#333333',
            leafStroke: '#1976d2',
            leafStrokeWidth: 1,
            fontRoot: 20,
            fontBranch: 16,
            fontLeaf: 14
        };
    }
    
    // Ensure THEME is always defined
    if (!THEME) {
        THEME = {
            rootFill: '#1976d2',
            rootText: '#ffffff',
            rootStroke: '#0d47a1',
            rootStrokeWidth: 3,
            branchFill: '#e3f2fd',
            branchText: '#333333',
            branchStroke: '#1976d2',
            branchStrokeWidth: 2,
            leafFill: '#f8f9fa',
            leafText: '#333333',
            leafStroke: '#1976d2',
            leafStrokeWidth: 1,
            fontRoot: 20,
            fontBranch: 16,
            fontLeaf: 14
        };
    }
    
    const width = baseWidth;
    const height = baseHeight;
    
    // Apply container background - matching mind map renderer
    const containerBackground = theme?.background || '#f5f5f5';
    d3.select('#d3-container')
        .style('background-color', containerBackground)
        .style('width', '100%')
        .style('height', '100%')
        .style('min-height', `${baseHeight}px`);
    
    var svg = d3.select('#d3-container').append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('background-color', containerBackground); // Use the same background color

    // Helpers to measure text accurately for width-adaptive rectangles
    const avgCharPx = 0.6; // fallback approximation
    function measureTextApprox(text, fontPx, hPad = 14, vPad = 10) {
        const tw = Math.max(1, (text ? text.length : 0) * fontPx * avgCharPx);
        const th = Math.max(1, fontPx * 1.2);
        return { w: Math.ceil(tw + hPad * 2), h: Math.ceil(th + vPad * 2) };
    }
    function measureSvgTextBox(svg, text, fontPx, hPad = 14, vPad = 10) {
        try {
            const temp = svg.append('text')
                .attr('x', -10000)
                .attr('y', -10000)
                .attr('font-size', fontPx)
                .attr('font-family', 'Inter, sans-serif')
                .attr('visibility', 'hidden')
                .text(text || '');
            const node = temp.node();
            let textWidth = 0;
            if (node && node.getComputedTextLength) {
                textWidth = node.getComputedTextLength();
            } else if (node && node.getBBox) {
                textWidth = node.getBBox().width || 0;
            }
            temp.remove();
            const textHeight = Math.max(1, fontPx * 1.2);
            return { w: Math.ceil(textWidth + hPad * 2), h: Math.ceil(textHeight + vPad * 2) };
        } catch (e) {
            // Fallback to approximation if DOM measurement fails
            return measureTextApprox(text, fontPx, hPad, vPad);
        }
    }
    
    // Calculate layout
    const rootX = width / 2;
    const rootY = 80;
    const rootFont = THEME.fontRoot || 20;
    const rootBox = measureSvgTextBox(svg, spec.topic, rootFont, 16, 12);
    // Draw root node as rectangle
    svg.append('rect')
        .attr('x', rootX - rootBox.w / 2)
        .attr('y', rootY - rootBox.h / 2)
        .attr('width', rootBox.w)
        .attr('height', rootBox.h)
        .attr('rx', 6)
        .attr('ry', 6)
        .attr('fill', THEME.rootFill)
        .attr('stroke', THEME.rootStroke)
        .attr('stroke-width', THEME.rootStrokeWidth);
    svg.append('text')
        .attr('x', rootX)
        .attr('y', rootY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.rootText)
        .attr('font-size', rootFont)
        .attr('font-weight', 'bold')
        .text(spec.topic);
    
    // Draw branches
    const branchY = rootY + rootBox.h / 2 + 60;
    let requiredBottomY = branchY + 40;

    // First pass: measure branches and leaves, compute per-column width
    const branchLayouts = spec.children.map((child) => {
        // Validate child structure
        if (!child || typeof child.label !== 'string') {
            console.warn('Invalid child structure:', child);
            return null;
        }
        
        const branchFont = THEME.fontBranch || 16;
        const branchBox = measureSvgTextBox(svg, child.label, branchFont, 14, 10);
        const leafFont = THEME.fontLeaf || 14;
        let maxLeafW = 0;
        const leafBoxes = (Array.isArray(child.children) ? child.children : []).map(leaf => {
            if (!leaf || typeof leaf.label !== 'string') {
                console.warn('Invalid leaf structure:', leaf);
                return null;
            }
            const b = measureSvgTextBox(svg, leaf.label, leafFont, 12, 8);
            if (b.w > maxLeafW) maxLeafW = b.w;
            return b;
        }).filter(box => box !== null); // Filter out invalid leaves
        
        const columnContentW = Math.max(branchBox.w, maxLeafW);
        const columnWidth = columnContentW + 60; // padding within column to avoid overlap
        return { child, branchFont, branchBox, leafFont, leafBoxes, maxLeafW, columnWidth };
    }).filter(layout => layout !== null); // Filter out invalid layouts

    // Second pass: assign x positions cumulatively to prevent overlap
    let runningX = padding;
    branchLayouts.forEach((layout) => {
        const xCenter = runningX + layout.columnWidth / 2;
        layout.branchX = xCenter;
        runningX += layout.columnWidth; // advance to next column start
    });

    // Compute content width and adapt canvas width if needed; otherwise center within available space
    const totalColumnsWidth = runningX - padding;
    const contentWidth = padding * 2 + totalColumnsWidth;
    let offsetX = 0;
    if (contentWidth <= width) {
        offsetX = (width - contentWidth) / 2;
    } else {
        // Expand SVG canvas to fit content
        d3.select(svg.node()).attr('width', contentWidth);
    }
    branchLayouts.forEach(layout => { layout.branchX += offsetX; });

    // Render branches and children stacked vertically with straight connectors
    branchLayouts.forEach(layout => {
        const { child, branchFont, branchBox, leafFont, leafBoxes, maxLeafW } = layout;
        const branchX = layout.branchX;

        // Draw branch rectangle and label with width adaptive to characters
        svg.append('rect')
            .attr('x', branchX - branchBox.w / 2)
            .attr('y', branchY - branchBox.h / 2)
            .attr('width', branchBox.w)
            .attr('height', branchBox.h)
            .attr('rx', 6)
            .attr('ry', 6)
            .attr('fill', THEME.branchFill)
            .attr('stroke', THEME.branchStroke)
            .attr('stroke-width', THEME.branchStrokeWidth);

        svg.append('text')
            .attr('x', branchX)
            .attr('y', branchY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.branchText)
            .attr('font-size', branchFont)
            .text(child.label);

        // Root to branch straight connector
        svg.append('line')
            .attr('x1', rootX)
            .attr('y1', rootY + rootBox.h / 2)
            .attr('x2', branchX)
            .attr('y2', branchY - branchBox.h / 2)
            .attr('stroke', '#bbb')
            .attr('stroke-width', 2);

        // Children: stacked vertically, centered, with straight vertical connectors
        const leaves = Array.isArray(child.children) ? child.children : [];
        if (leaves.length > 0) {
            const vGap = 12;
            const startY = branchY + branchBox.h / 2 + 20;

            // Compute vertical centers bottom-up using actual heights (center-aligned at branchX)
            const centersY = [];
            let cy = startY + (leafBoxes[0]?.h || (leafFont * 1.2 + 10)) / 2;
            leaves.forEach((_, j) => {
                const prevH = j === 0 ? 0 : (leafBoxes[j - 1]?.h || (leafFont * 1.2 + 10));
                const h = leafBoxes[j]?.h || (leafFont * 1.2 + 10);
                if (j === 0) {
                    centersY.push(cy);
                } else {
                    cy = centersY[j - 1] + prevH / 2 + vGap + h / 2;
                    centersY.push(cy);
                }
            });

            // Draw child rectangles and labels centered at branchX
            leaves.forEach((leaf, j) => {
                const box = leafBoxes[j] || measureSvgTextBox(svg, leaf.label, leafFont, 12, 8);
                const leafY = centersY[j];
                // Width adaptive to characters for each node
                const rectW = box.w;
                svg.append('rect')
                    .attr('x', branchX - rectW / 2)
                    .attr('y', leafY - box.h / 2)
                    .attr('width', rectW)
                    .attr('height', box.h)
                    .attr('rx', 4)
                    .attr('ry', 4)
                    .attr('fill', THEME.leafFill || '#ffffff')
                    .attr('stroke', THEME.leafStroke || '#c8d6e5')
                    .attr('stroke-width', THEME.leafStrokeWidth != null ? THEME.leafStrokeWidth : 1);

                svg.append('text')
                    .attr('x', branchX)
                    .attr('y', leafY)
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', THEME.leafText)
                    .attr('font-size', leafFont)
                    .text(leaf.label);
            });

            // Draw straight vertical connectors: branch -> first child, then between consecutive children
            const firstTop = centersY[0] - (leafBoxes[0]?.h || (leafFont * 1.2 + 10)) / 2;
            svg.append('line')
                .attr('x1', branchX)
                .attr('y1', branchY + branchBox.h / 2)
                .attr('x2', branchX)
                .attr('y2', firstTop)
                .attr('stroke', '#cccccc')
                .attr('stroke-width', 1.5);

            for (let j = 0; j < centersY.length - 1; j++) {
                const thisBottom = centersY[j] + (leafBoxes[j]?.h || (leafFont * 1.2 + 10)) / 2;
                const nextTop = centersY[j + 1] - (leafBoxes[j + 1]?.h || (leafFont * 1.2 + 10)) / 2;
                svg.append('line')
                    .attr('x1', branchX)
                    .attr('y1', thisBottom)
                    .attr('x2', branchX)
                    .attr('y2', nextTop)
                    .attr('stroke', '#cccccc')
                    .attr('stroke-width', 1.5);
            }

            const lastBottom = centersY[centersY.length - 1] + (leafBoxes[leafBoxes.length - 1]?.h || (leafFont * 1.2 + 10)) / 2;
            requiredBottomY = Math.max(requiredBottomY, lastBottom + 30);
        } else {
            requiredBottomY = Math.max(requiredBottomY, branchY + branchBox.h / 2 + 40);
        }
    });

    // Expand SVG height if content exceeds current height
    const finalNeededHeight = Math.ceil(requiredBottomY + padding);
    if (finalNeededHeight > height) {
        svg.attr('height', finalNeededHeight);
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



// CRITICAL FIX: Export functions to global scope for dispatcher access
console.log('🌳 Tree renderer: Starting function export...');
console.log('🌳 Tree renderer: renderTreeMap function exists:', typeof renderTreeMap);

// CRITICAL FIX: Use try-catch to ensure export doesn't fail silently
try {
    if (typeof window !== 'undefined') {
        // Browser environment - attach to window
        console.log('🌳 Tree renderer: Attaching to window object...');
        
        // Force the assignment - check if properties already exist
        if (!window.hasOwnProperty('renderTreeMap')) {
            Object.defineProperty(window, 'renderTreeMap', {
                value: renderTreeMap,
                writable: true,
                configurable: true
            });
            console.log('✅ renderTreeMap property defined');
        } else {
            console.log('ℹ️ renderTreeMap property already exists, updating value');
            window.renderTreeMap = renderTreeMap;
        }
        
        if (!window.hasOwnProperty('TreeRenderer')) {
            Object.defineProperty(window, 'TreeRenderer', {
                value: {
                    renderTreeMap: renderTreeMap
                },
                writable: true,
                configurable: true
            });
            console.log('✅ TreeRenderer property defined');
        } else {
            console.log('ℹ️ TreeRenderer property already exists, updating value');
            window.TreeRenderer = { renderTreeMap: renderTreeMap };
        }
        
        console.log('✅ Tree renderer functions exported to global scope');
        console.log('🌳 Tree renderer: window.renderTreeMap now available:', typeof window.renderTreeMap);
        console.log('🌳 Tree renderer: window.TreeRenderer now available:', typeof window.TreeRenderer);
        
        // Verify the export worked
        if (typeof window.renderTreeMap === 'function') {
            console.log('✅ SUCCESS: renderTreeMap is now available globally');
        } else {
            console.error('❌ FAILED: renderTreeMap is not available globally');
        }
        
        if (typeof window.TreeRenderer === 'object' && window.TreeRenderer.renderTreeMap) {
            console.log('✅ SUCCESS: TreeRenderer.renderTreeMap is now available globally');
        } else {
            console.error('❌ FAILED: TreeRenderer.renderTreeMap is not available globally');
        }
        
    } else if (typeof module !== 'undefined' && module.exports) {
        // Node.js environment
        module.exports = {
            renderTreeMap,
            TreeRenderer: {
                renderTreeMap
            }
        };
    }
} catch (error) {
    console.error('❌ CRITICAL ERROR during function export:', error);
    // Try alternative export method
    try {
        console.log('🔄 Attempting alternative export method...');
        if (typeof window !== 'undefined') {
            window.renderTreeMap = renderTreeMap;
            window.TreeRenderer = { renderTreeMap: renderTreeMap };
            console.log('✅ Alternative export completed');
        }
    } catch (altError) {
        console.error('❌ Alternative export also failed:', altError);
    }
}

// CRITICAL FIX: Final execution confirmation
console.log('🌳 Tree renderer: Script execution completed');
console.log('🌳 Tree renderer: Final status check:');
console.log('  - renderTreeMap function defined:', typeof renderTreeMap);
console.log('  - window.renderTreeMap available:', typeof window.renderTreeMap);
console.log('  - window.TreeRenderer available:', typeof window.TreeRenderer);
