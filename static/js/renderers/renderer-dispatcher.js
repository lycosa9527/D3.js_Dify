/**
 * Renderer Dispatcher for MindGraph
 * 
 * This module provides the main rendering dispatcher function.
 * It must be loaded AFTER all individual renderer modules.
 * 
 * Performance Impact: Minimal - just function routing
 */

// Main rendering dispatcher function
function renderGraph(type, spec, theme = null, dimensions = null) {
    console.log('renderGraph called with:', { type, spec, theme, dimensions });
    
    // Clear the container first
    d3.select('#d3-container').html('');
    
    // Extract style information from spec if available
    let integratedTheme = theme;
    if (spec && spec._style) {
        console.log('Using integrated styles from spec:', spec._style);
        // Merge spec styles with backend theme (backend background takes priority)
        integratedTheme = {
            ...spec._style,
            background: theme?.background
        };
        console.log('Merged theme background (backend priority):', integratedTheme.background);
    } else {
        // Use theme as-is (no fallbacks)
        integratedTheme = theme;
        console.log('Using backend theme background:', integratedTheme?.background);
    }
    
    // Extract style metadata for debugging
    if (spec && spec._style_metadata) {
        console.log('Style metadata:', spec._style_metadata);
    }
    
    switch (type) {
        case 'double_bubble_map':
            if (typeof renderDoubleBubbleMap === 'function') {
                renderDoubleBubbleMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderDoubleBubbleMap function not found');
                showRendererError('double_bubble_map');
            }
            break;
        case 'bubble_map':
            if (typeof renderBubbleMap === 'function') {
                renderBubbleMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderBubbleMap function not found');
                showRendererError('bubble_map');
            }
            break;
        case 'circle_map':
            if (typeof renderCircleMap === 'function') {
                renderCircleMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderCircleMap function not found');
                showRendererError('circle_map');
            }
            break;
        case 'tree_map':
            console.log('Renderer dispatcher: Processing tree_map case');
            console.log('Renderer dispatcher: renderTreeMap function available:', typeof renderTreeMap);
            console.log('Renderer dispatcher: window.renderTreeMap available:', typeof window.renderTreeMap);
            console.log('Renderer dispatcher: window.TreeRenderer available:', typeof window.TreeRenderer);
            if (window.TreeRenderer) {
                console.log('Renderer dispatcher: window.TreeRenderer.renderTreeMap available:', typeof window.TreeRenderer.renderTreeMap);
            }
            
            // CRITICAL FIX: Check all possible locations for the function
            let treeMapRenderer = null;
            if (typeof renderTreeMap === 'function') {
                treeMapRenderer = renderTreeMap;
                console.log('Renderer dispatcher: Using global renderTreeMap');
            } else if (typeof window.renderTreeMap === 'function') {
                treeMapRenderer = window.renderTreeMap;
                console.log('Renderer dispatcher: Using window.renderTreeMap');
            } else if (window.TreeRenderer && typeof window.TreeRenderer.renderTreeMap === 'function') {
                treeMapRenderer = window.TreeRenderer.renderTreeMap;
                console.log('Renderer dispatcher: Using window.TreeRenderer.renderTreeMap');
            }
            
            if (treeMapRenderer) {
                console.log('Renderer dispatcher: Calling tree map renderer');
                treeMapRenderer(spec, integratedTheme, dimensions);
            } else {
                console.error('renderTreeMap function not found anywhere');
                showRendererError('tree_map');
            }
            break;
        case 'concept_map':
            if (typeof renderConceptMap === 'function') {
                renderConceptMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderConceptMap function not found');
                showRendererError('concept_map');
            }
            break;
        case 'mindmap':
            if (typeof renderMindMap === 'function') {
                renderMindMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderMindMap function not found');
                showRendererError('mindmap');
            }
            break;
        case 'flowchart':
            if (typeof renderFlowchart === 'function') {
                renderFlowchart(spec, integratedTheme, dimensions);
            } else {
                console.error('renderFlowchart function not found');
                showRendererError('flowchart');
            }
            break;

        case 'bridge_map':
            if (typeof renderBridgeMap === 'function') {
                renderBridgeMap(spec, integratedTheme, dimensions, 'd3-container');
            } else {
                console.error('renderBridgeMap function not found');
                showRendererError('bridge_map');
            }
            break;
        case 'brace_map':
            if (typeof renderBraceMap === 'function') {
                console.log('Rendering brace map with spec:', spec);
                try {
                    renderBraceMap(spec, integratedTheme, dimensions);
                    console.log('Brace map rendering completed');
                } catch (error) {
                    console.error('Error rendering brace map:', error);
                    showRendererError('brace_map', error.message);
                }
            } else {
                console.error('renderBraceMap function not found');
                showRendererError('brace_map');
            }
            break;
        case 'flow_map':
            if (typeof renderFlowMap === 'function') {
                renderFlowMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderFlowMap function not found');
                showRendererError('flow_map');
            }
            break;
        case 'multi_flow_map':
            if (typeof renderMultiFlowMap === 'function') {
                renderMultiFlowMap(spec, integratedTheme, dimensions);
            } else {
                console.error('renderMultiFlowMap function not found');
                showRendererError('multi_flow_map');
            }
            break;
        default:
            console.error(`Unknown graph type: ${type}`);
            showRendererError('unknown', `Unknown graph type '${type}'`);
    }
}

// Helper function to show renderer errors
function showRendererError(type, message = null) {
    const errorMsg = message || `Renderer for '${type}' not loaded or not available`;
    d3.select('#d3-container').append('div')
        .style('color', 'red')
        .style('font-size', '18px')
        .style('text-align', 'center')
        .style('padding', '50px')
        .text(`Error: ${errorMsg}`);
}

// Export functions for module system
if (typeof window !== 'undefined') {
    // Browser environment - attach to window
    window.renderGraph = renderGraph;
    window.showRendererError = showRendererError;
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        renderGraph,
        showRendererError
    };
}
