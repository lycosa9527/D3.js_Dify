/**
 * Tree Renderer for MindGraph
 * 
 * This module contains the tree map, org chart, and fishbone rendering functions.
 * Requires: shared-utilities.js, style-manager.js
 * 
 * Performance Impact: Loads only ~60KB instead of full 213KB
 */

// Check if shared utilities are available
if (typeof window.MindGraphUtils === 'undefined') {
    console.error('MindGraphUtils not found! Please load shared-utilities.js first.');
}

const { getTextRadius, addWatermark, getThemeDefaults } = window.MindGraphUtils;

function renderTreeMap(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    
    // Validate spec
    if (!spec || !spec.topic || !Array.isArray(spec.children)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for tree map');
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
    
    const width = baseWidth;
    const height = baseHeight;
    var svg = d3.select('#d3-container').append('svg').attr('width', width).attr('height', height);

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
        const branchFont = THEME.fontBranch || 16;
        const branchBox = measureSvgTextBox(svg, child.label, branchFont, 14, 10);
        const leafFont = THEME.fontLeaf || 14;
        let maxLeafW = 0;
        const leafBoxes = (Array.isArray(child.children) ? child.children : []).map(leaf => {
            const b = measureSvgTextBox(svg, leaf.label, leafFont, 12, 8);
            if (b.w > maxLeafW) maxLeafW = b.w;
            return b;
        });
        const columnContentW = Math.max(branchBox.w, maxLeafW);
        const columnWidth = columnContentW + 60; // padding within column to avoid overlap
        return { child, branchFont, branchBox, leafFont, leafBoxes, maxLeafW, columnWidth };
    });

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
    
    // Watermark
    addWatermark(svg, theme);
}

function renderOrgChart(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.root) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for org chart');
        return;
    }
    
    const baseWidth = dimensions?.baseWidth || 1000;
    const baseHeight = dimensions?.baseHeight || 700;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        rootFill: '#2c3e50',
        rootText: '#ffffff',
        managerFill: '#3498db',
        managerText: '#ffffff',
        employeeFill: '#ecf0f1',
        employeeText: '#2c3e50',
        strokeColor: '#bdc3c7',
        fontRoot: 16,
        fontManager: 14,
        fontEmployee: 12,
        ...theme
    };
    
    // Transform data to D3 hierarchy
    function transformNode(node) {
        const result = {
            name: node.name || node.title || '',
            title: node.title || '',
            level: node.level || 0
        };
        
        if (node.children && Array.isArray(node.children)) {
            result.children = node.children.map(transformNode);
        }
        
        return result;
    }
    
    const root = d3.hierarchy(transformNode(spec.root));
    
    // Calculate node sizes
    const nodeHeight = 50;
    const nodeWidth = 120;
    
    // Create tree layout
    const treeLayout = d3.tree()
        .size([baseHeight - 2 * padding, baseWidth - 2 * padding])
        .nodeSize([nodeWidth + 20, nodeHeight + 40]);
    
    treeLayout(root);
    
    // Create SVG
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    const g = svg.append('g')
        .attr('transform', `translate(${padding}, ${padding})`);
    
    // Draw links
    g.selectAll('.link')
        .data(root.links())
        .enter().append('path')
        .attr('class', 'link')
        .attr('d', d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y))
        .attr('fill', 'none')
        .attr('stroke', THEME.strokeColor)
        .attr('stroke-width', 2);
    
    // Draw nodes
    const node = g.selectAll('.node')
        .data(root.descendants())
        .enter().append('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
    
    // Add rectangles
    node.append('rect')
        .attr('x', -nodeWidth / 2)
        .attr('y', -nodeHeight / 2)
        .attr('width', nodeWidth)
        .attr('height', nodeHeight)
        .attr('rx', 5)
        .attr('fill', d => {
            if (d.depth === 0) return THEME.rootFill;
            if (d.depth === 1) return THEME.managerFill;
            return THEME.employeeFill;
        })
        .attr('stroke', THEME.strokeColor)
        .attr('stroke-width', 1);
    
    // Add text
    node.append('text')
        .attr('dy', 3)
        .attr('text-anchor', 'middle')
        .attr('fill', d => {
            if (d.depth === 0) return THEME.rootText;
            if (d.depth === 1) return THEME.managerText;
            return THEME.employeeText;
        })
        .attr('font-size', d => {
            if (d.depth === 0) return THEME.fontRoot;
            if (d.depth === 1) return THEME.fontManager;
            return THEME.fontEmployee;
        })
        .text(d => d.data.name);
    
    // Watermark
    addWatermark(svg, theme);
}

function renderFishboneDiagram(spec, theme = null, dimensions = null) {
    d3.select('#d3-container').html('');
    if (!spec || !spec.problem || !Array.isArray(spec.categories)) {
        d3.select('#d3-container').append('div').style('color', 'red').text('Invalid spec for fishbone diagram');
        return;
    }
    
    const baseWidth = dimensions?.baseWidth || 1000;
    const baseHeight = dimensions?.baseHeight || 600;
    const padding = dimensions?.padding || 40;
    
    const THEME = {
        spineColor: '#2c3e50',
        spineWidth: 4,
        problemFill: '#e74c3c',
        problemText: '#ffffff',
        categoryColor: '#3498db',
        categoryWidth: 3,
        categoryFill: '#ecf0f1',
        categoryText: '#2c3e50',
        causeColor: '#95a5a6',
        causeWidth: 2,
        causeText: '#2c3e50',
        fontProblem: 16,
        fontCategory: 14,
        fontCause: 12,
        ...theme
    };
    
    const svg = d3.select('#d3-container').append('svg')
        .attr('width', baseWidth)
        .attr('height', baseHeight)
        .attr('viewBox', `0 0 ${baseWidth} ${baseHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Main spine
    const spineStartX = padding;
    const spineEndX = baseWidth - padding - 100;
    const spineY = baseHeight / 2;
    
    // Draw main spine
    svg.append('line')
        .attr('x1', spineStartX)
        .attr('y1', spineY)
        .attr('x2', spineEndX)
        .attr('y2', spineY)
        .attr('stroke', THEME.spineColor)
        .attr('stroke-width', THEME.spineWidth);
    
    // Problem box
    const problemBox = getTextRadius(spec.problem, THEME.fontProblem, 20);
    svg.append('rect')
        .attr('x', spineEndX + 10)
        .attr('y', spineY - problemBox)
        .attr('width', problemBox * 2)
        .attr('height', problemBox * 2)
        .attr('fill', THEME.problemFill)
        .attr('stroke', THEME.spineColor)
        .attr('stroke-width', 2);
    
    svg.append('text')
        .attr('x', spineEndX + 10 + problemBox)
        .attr('y', spineY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', THEME.problemText)
        .attr('font-size', THEME.fontProblem)
        .attr('font-weight', 'bold')
        .text(spec.problem);
    
    // Category branches
    const categoryCount = spec.categories.length;
    const spineLength = spineEndX - spineStartX;
    const categorySpacing = spineLength / (categoryCount + 1);
    
    spec.categories.forEach((category, i) => {
        const isUpper = i % 2 === 0;
        const categoryX = spineStartX + (i + 1) * categorySpacing;
        const categoryEndY = isUpper ? spineY - 100 : spineY + 100;
        
        // Draw category branch
        svg.append('line')
            .attr('x1', categoryX)
            .attr('y1', spineY)
            .attr('x2', categoryX + (isUpper ? -50 : 50))
            .attr('y2', categoryEndY)
            .attr('stroke', THEME.categoryColor)
            .attr('stroke-width', THEME.categoryWidth);
        
        // Category label
        svg.append('text')
            .attr('x', categoryX + (isUpper ? -60 : 60))
            .attr('y', categoryEndY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', THEME.categoryText)
            .attr('font-size', THEME.fontCategory)
            .attr('font-weight', 'bold')
            .text(category.name);
        
        // Draw causes
        if (category.causes && Array.isArray(category.causes)) {
            category.causes.forEach((cause, j) => {
                const causeY = categoryEndY + (isUpper ? -1 : 1) * (30 + j * 25);
                const causeX = categoryX + (isUpper ? -30 : 30);
                
                // Cause line
                svg.append('line')
                    .attr('x1', categoryX + (isUpper ? -25 : 25))
                    .attr('y2', categoryEndY + (isUpper ? -10 : 10))
                    .attr('x2', causeX)
                    .attr('y2', causeY)
                    .attr('stroke', THEME.causeColor)
                    .attr('stroke-width', THEME.causeWidth);
                
                // Cause text
                svg.append('text')
                    .attr('x', causeX + (isUpper ? -10 : 10))
                    .attr('y', causeY)
                    .attr('text-anchor', isUpper ? 'end' : 'start')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', THEME.causeText)
                    .attr('font-size', THEME.fontCause)
                    .text(cause);
            });
        }
    });
    
    // Watermark
    addWatermark(svg, theme);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.TreeRenderer = {
        renderTreeMap,
        renderOrgChart,
        renderFishboneDiagram
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderTreeMap,
        renderOrgChart,
        renderFishboneDiagram
    };
}
