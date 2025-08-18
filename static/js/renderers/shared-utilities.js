/**
 * Shared D3 Utilities for MindGraph Renderers
 * 
 * This module contains common utility functions used across all graph type renderers.
 * By extracting these shared utilities, we eliminate code duplication and reduce
 * the size of individual renderer modules.
 * 
 * Performance Impact: ~15-20KB reduction per renderer module
 */

// --- Safe, memory-leak-free text radius measurement ---
let measurementContainer = null;

function getMeasurementContainer() {
    if (!measurementContainer) {
        const body = d3.select('body');
        if (body.empty()) {
            console.warn('Body element not found, creating measurement container in document');
            measurementContainer = d3.select(document.documentElement)
                .append('div')
                .attr('id', 'measurement-container')
                .style('position', 'absolute')
                .style('visibility', 'hidden')
                .style('pointer-events', 'none');
        } else {
            measurementContainer = body
                .append('div')
                .attr('id', 'measurement-container')
                .style('position', 'absolute')
                .style('visibility', 'hidden')
                .style('pointer-events', 'none');
        }
    }
    return measurementContainer;
}

function getTextRadius(text, fontSize, padding) {
    let textElement = null;
    try {
        const container = getMeasurementContainer();
        textElement = container
            .append('svg')
            .append('text')
            .attr('font-size', fontSize)
            .text(text);
        const bbox = textElement.node().getBBox();
        const radius = Math.ceil(Math.sqrt(bbox.width * bbox.width + bbox.height * bbox.height) / 2 + (padding || 12));
        return Math.max(radius, 30); // Minimum radius
    } catch (error) {
        console.error('Error calculating text radius:', error);
        return 30; // Default fallback
    } finally {
        if (textElement) {
            textElement.remove();
        }
    }
}

function cleanupMeasurementContainer() {
    if (measurementContainer) {
        measurementContainer.remove();
        measurementContainer = null;
    }
}

// --- Watermark utilities ---
function getWatermarkText(theme = null) {
    return theme?.watermark?.text || 'MindGraph';
}

function addWatermark(svg, theme = null) {
    const watermarkText = getWatermarkText(theme);
    const watermarkConfig = theme?.watermark || {};
    
    // Default watermark configuration
    const config = {
        text: watermarkText,
        fontSize: watermarkConfig.fontSize || '12px',
        fill: watermarkConfig.fill || '#cccccc',
        opacity: watermarkConfig.opacity || 0.5,
        position: watermarkConfig.position || 'bottom-right',
        padding: watermarkConfig.padding || 10
    };
    
    // Get SVG dimensions
    const svgNode = svg.node();
    const bbox = svgNode.getBBox();
    const svgWidth = bbox.width || 800;
    const svgHeight = bbox.height || 600;
    
    // Calculate position based on configuration
    let x, y, textAnchor;
    
    switch (config.position) {
        case 'top-left':
            x = config.padding;
            y = config.padding + 12;
            textAnchor = 'start';
            break;
        case 'top-right':
            x = svgWidth - config.padding;
            y = config.padding + 12;
            textAnchor = 'end';
            break;
        case 'bottom-left':
            x = config.padding;
            y = svgHeight - config.padding;
            textAnchor = 'start';
            break;
        case 'bottom-right':
        default:
            x = svgWidth - config.padding;
            y = svgHeight - config.padding;
            textAnchor = 'end';
            break;
    }
    
    // Add watermark text
    svg.append('text')
        .attr('x', x)
        .attr('y', y)
        .attr('text-anchor', textAnchor)
        .attr('font-size', config.fontSize)
        .attr('font-family', 'Arial, sans-serif')
        .attr('fill', config.fill)
        .attr('opacity', config.opacity)
        .style('pointer-events', 'none')
        .text(config.text);
}

// --- Common color and styling utilities ---
function getColorScale(theme, itemCount) {
    const colors = theme?.colors || ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e'];
    return d3.scaleOrdinal()
        .domain(d3.range(itemCount))
        .range(colors);
}

function getThemeDefaults(theme = null) {
    return {
        backgroundColor: theme?.backgroundColor || '#ffffff',
        textColor: theme?.textColor || '#333333',
        fontSize: theme?.fontSize || '14px',
        fontFamily: theme?.fontFamily || 'Arial, sans-serif',
        strokeColor: theme?.strokeColor || '#cccccc',
        strokeWidth: theme?.strokeWidth || 1,
        ...theme
    };
}

// --- Common SVG setup utilities ---
function createSVG(containerId, dimensions) {
    const container = d3.select(`#${containerId}`);
    container.selectAll('*').remove(); // Clean previous content
    
    const svg = container
        .append('svg')
        .attr('width', dimensions.width)
        .attr('height', dimensions.height)
        .style('background-color', 'transparent');
        
    return svg;
}

function centerContent(svg, contentGroup, dimensions) {
    try {
        const bbox = contentGroup.node().getBBox();
        const centerX = dimensions.width / 2;
        const centerY = dimensions.height / 2;
        const contentCenterX = bbox.x + bbox.width / 2;
        const contentCenterY = bbox.y + bbox.height / 2;
        
        const translateX = centerX - contentCenterX;
        const translateY = centerY - contentCenterY;
        
        contentGroup.attr('transform', `translate(${translateX}, ${translateY})`);
    } catch (error) {
        console.warn('Could not center content:', error);
    }
}

// --- Text wrapping utilities ---
function wrapText(text, width) {
    text.each(function() {
        const textElement = d3.select(this);
        const words = textElement.text().split(/\s+/).reverse();
        let word;
        let line = [];
        let lineNumber = 0;
        const lineHeight = 1.1; // ems
        const y = textElement.attr("y");
        const dy = parseFloat(textElement.attr("dy")) || 0;
        
        let tspan = textElement.text(null).append("tspan")
            .attr("x", 0)
            .attr("y", y)
            .attr("dy", dy + "em");
            
        while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(" "));
            if (tspan.node().getComputedTextLength() > width) {
                line.pop();
                tspan.text(line.join(" "));
                line = [word];
                tspan = textElement.append("tspan")
                    .attr("x", 0)
                    .attr("y", y)
                    .attr("dy", ++lineNumber * lineHeight + dy + "em")
                    .text(word);
            }
        }
    });
}

// Main rendering dispatcher function
function renderGraph(type, spec, theme = null, dimensions = null) {
    console.log('renderGraph called with:', { type, spec, theme, dimensions });
    
    // Clear the container first
    d3.select('#d3-container').html('');
    
    // Extract style information from spec if available
    let integratedTheme = theme;
    if (spec && spec._style) {
        console.log('Using integrated styles from spec:', spec._style);
        integratedTheme = spec._style;
    }
    
    // Extract style metadata for debugging
    if (spec && spec._style_metadata) {
        console.log('Style metadata:', spec._style_metadata);
    }
    
    switch (type) {
        case 'double_bubble_map':
            renderDoubleBubbleMap(spec, integratedTheme, dimensions);
            break;
        case 'bubble_map':
            renderBubbleMap(spec, integratedTheme, dimensions);
            break;
        case 'circle_map':
            renderCircleMap(spec, integratedTheme, dimensions);
            break;
        case 'tree_map':
            renderTreeMap(spec, integratedTheme, dimensions);
            break;
        case 'concept_map':
            renderConceptMap(spec, integratedTheme, dimensions);
            break;
        case 'mindmap':
            renderMindMap(spec, integratedTheme, dimensions);
            break;
        case 'venn_diagram':
            renderVennDiagram(spec, integratedTheme, dimensions);
            break;
        case 'flowchart':
            renderFlowchart(spec, integratedTheme, dimensions);
            break;
        case 'org_chart':
            renderOrgChart(spec, integratedTheme, dimensions);
            break;
        case 'timeline':
            renderTimeline(spec, integratedTheme, dimensions);
            break;
        case 'bridge_map':
            renderBridgeMap(spec, integratedTheme, dimensions, 'd3-container');
            break;
        case 'brace_map':
            console.log('Rendering brace map with spec:', spec);
            try {
                renderBraceMap(spec, integratedTheme, dimensions);
                console.log('Brace map rendering completed');
            } catch (error) {
                console.error('Error rendering brace map:', error);
                d3.select('#d3-container').append('div')
                    .style('color', 'red')
                    .text(`Error rendering brace map: ${error.message}`);
            }
            break;
        case 'flow_map':
            renderFlowMap(spec, integratedTheme, dimensions);
            break;
        case 'multi_flow_map':
            renderMultiFlowMap(spec, integratedTheme, dimensions);
            break;
        case 'fishbone_diagram':
            renderFishboneDiagram(spec, integratedTheme, dimensions);
            break;
        case 'semantic_web':
            renderSemanticWeb(spec, integratedTheme, dimensions);
            break;
        default:
            console.error(`Unknown graph type: ${type}`);
            d3.select('#d3-container').append('div')
                .style('color', 'red')
                .text(`Error: Unknown graph type '${type}'`);
    }
}

// --- Export utilities for module system ---
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.MindGraphUtils = {
        getMeasurementContainer,
        getTextRadius,
        cleanupMeasurementContainer,
        getWatermarkText,
        addWatermark,
        getColorScale,
        getThemeDefaults,
        createSVG,
        centerContent,
        wrapText,
        renderGraph
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        getMeasurementContainer,
        getTextRadius,
        cleanupMeasurementContainer,
        getWatermarkText,
        addWatermark,
        getColorScale,
        getThemeDefaults,
        createSVG,
        centerContent,
        wrapText,
        renderGraph
    };
}
