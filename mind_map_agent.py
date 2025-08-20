#!/usr/bin/env python3
"""
MindGraph v2.4.0 - Advanced Mind Map Agent with Clockwise Positioning System

This agent implements a revolutionary clockwise positioning system that:
- Distributes branches evenly between left and right sides
- Aligns Branch 2 and 5 with the central topic for perfect visual balance
- Maintains the proven children-first positioning system
- Provides scalable layouts for 4, 6, 8, 10+ branches
- Creates production-ready, enterprise-grade mind maps

Features:
- Clockwise branch distribution (first half → RIGHT, second half → LEFT)
- Smart branch alignment with central topic
- 5-column system preservation: [Left Children] [Left Branches] [Topic] [Right Branches] [Right Children]
- Adaptive canvas sizing and coordinate centering
- Advanced text width calculation for precise node sizing
"""

import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

from config import Config


@dataclass
class NodePosition:
    """Data structure for node positioning"""
    x: float
    y: float
    width: float
    height: float
    text: str
    node_type: str  # 'topic', 'branch', 'child'
    branch_index: Optional[int] = None
    child_index: Optional[int] = None
    angle: Optional[float] = None


class MindMapAgent:
    """
    MindGraph v2.4.0 - Advanced Mind Map Agent with Clockwise Positioning System
    
    This agent implements a revolutionary clockwise positioning system that creates
    perfectly balanced, production-ready mind maps with intelligent branch distribution
    and smart alignment features.
    
    Key Features:
    - Clockwise branch distribution for perfect left/right balance
    - Smart branch alignment (Branch 2 & 5 align with central topic)
    - Children-first positioning system for optimal layout
    - Scalable layouts supporting 4+ branches
    - Enterprise-grade positioning algorithms
    """
    
    def __init__(self):
        self.config = Config()
    
    def enhance_spec(self, spec: Dict) -> Dict:
        """Enhance mind map specification with layout data"""
        try:
            if not spec or not isinstance(spec, dict):
                return {"success": False, "error": "Invalid specification"}
            
            if 'topic' not in spec or not spec['topic']:
                return {"success": False, "error": "Missing topic"}
            
            if 'children' not in spec or not isinstance(spec['children'], list):
                return {"success": False, "error": "Missing children"}
            
            if not spec['children']:
                return {"success": False, "error": "At least one child branch is required"}
            
            # Generate clean layout
            layout = self._generate_mind_map_layout(spec['topic'], spec['children'])
            
            # Add layout to spec
            spec['_layout'] = layout
            spec['_recommended_dimensions'] = layout.get('params', {}).copy()  # Copy params
            spec['_agent'] = 'mind_map_agent'
            
            return {"success": True, "spec": spec}
            
        except Exception as e:
            return {"success": False, "error": f"MindMapAgent failed: {e}"}
    
    def _generate_mind_map_layout(self, topic: str, children: List[Dict]) -> Dict:
        """
        Generate clean mind map layout using CLEAN POSITIONING SYSTEM:
        
        WORKFLOW: 
        1. Calculate left/right branch distribution
        2. Stack all children nodes vertically on each side
        3. Position branch nodes at the center of their children groups
        4. Central topic positioned at vertical center of all subtopic nodes
        """
        # Initialize positions dictionary
        positions = {}
        
        # STEP 1: Analyze how many branches we get from LLM
        num_branches = len(children)
        # LLM returned branches
        
        # STEP 2: Calculate left/right branch distribution
        left_branch_count = (num_branches + 1) // 2  # More branches on left if odd
        right_branch_count = num_branches - left_branch_count
        
        # Branch distribution calculated
        
        # STEP 3: Calculate column positions with proper spacing
        gap_topic_to_branch = 200  # Space between topic and branches
        gap_branch_to_child = 120   # Space between branches and children
        
        # Calculate maximum dimensions using adaptive font sizes for consistency
        max_branch_width = 0
        max_child_width = 0
        
        for branch in children:
            # Calculate branch width with adaptive font size
            branch_font_size = self._get_adaptive_font_size(branch['label'], 'branch')
            branch_width = self._calculate_text_width(branch['label'], branch_font_size) + self._get_adaptive_padding(branch['label'])
            max_branch_width = max(max_branch_width, branch_width)
            
            # Calculate child widths with adaptive font sizes
            for child in branch.get('children', []):
                child_font_size = self._get_adaptive_font_size(child['label'], 'child')
                child_width = self._calculate_text_width(child['label'], child_font_size) + self._get_adaptive_padding(child['label'])
                max_child_width = max(max_child_width, child_width)
        
        # Column positions
        left_children_x = -(gap_topic_to_branch + max_branch_width + gap_branch_to_child + max_child_width/2)
        left_branches_x = -(gap_topic_to_branch + max_branch_width/2)
        right_branches_x = gap_topic_to_branch + max_branch_width/2
        right_children_x = gap_topic_to_branch + max_branch_width + gap_branch_to_child + max_child_width/2
        
        # Column positions and max dimensions calculated
        
        # STEP 4: Stack ALL children vertically on each side first (before positioning topic)
        all_children_positions = {}  # Store child positions by branch index
        
        # Left side children stacking
        left_children_y = 0
        left_branch_children = []
        
        # Right side children stacking  
        right_children_y = 0
        right_branch_children = []
        
        for i, branch_data in enumerate(children):
            nested_children = branch_data.get('children', [])
            
            if nested_children:
                # Determine which side this branch goes on based on clockwise positioning
                # For even distribution: first half goes RIGHT, second half goes LEFT
                # 6 branches: Branch 1,2,3 → RIGHT, Branch 4,5,6 → LEFT
                # 8 branches: Branch 1,2,3,4 → RIGHT, Branch 5,6,7,8 → LEFT
                mid_point = num_branches // 2
                is_left_side = i >= mid_point
                
                # Position children in correct column
                if is_left_side:
                    child_x = left_children_x
                    current_y = left_children_y
                    side_children = left_branch_children
                else:
                    child_x = right_children_x
                    current_y = right_children_y
                    side_children = right_branch_children
                
                # Branch side determined
                
                # Stack children vertically with proper spacing
                child_positions = []
                child_spacing = 25  # Fixed spacing between children
                
                for j, child in enumerate(nested_children):
                    child_font_size = self._get_adaptive_font_size(child['label'], 'child')
                    child_height = self._get_adaptive_node_height(child['label'], 'child')
                    child_width = self._calculate_text_width(child['label'], child_font_size) + self._get_adaptive_padding(child['label'])
                    
                    # Stack vertically: each child below the previous one
                    child_y = current_y + (child_height / 2)
                    current_y += child_height + child_spacing
                    
                    # Store child position
                    child_key = f'child_{i}_{j}'
                    positions[child_key] = {
                        'x': child_x, 'y': child_y,
                        'width': child_width, 'height': child_height,
                        'text': child['label'], 'node_type': 'child',
                        'branch_index': i, 'child_index': j, 'angle': 0,
                        'fill': '#e8f4fd',  # Very light blue for children
                        'text_color': '#2c3e50',  # Dark text for readability
                        'stroke': '#90caf9',  # Light blue border
                        'stroke_width': 2
                    }
                    
                    child_positions.append({
                        'x': child_x, 'y': child_y,
                        'width': child_width, 'height': child_height,
                        'text': child['label'], 'node_type': 'child',
                        'branch_index': i, 'child_index': j, 'angle': 0,
                        'fill': '#e8f4fd',
                        'text_color': '#2c3e50',
                        'stroke': '#90caf9',
                        'stroke_width': 2
                    })
                
                # Update tracking for this side
                if is_left_side:
                    left_children_y = current_y + 20  # Add spacing between branch groups
                else:
                    right_children_y = current_y + 20  # Add spacing between branch groups
                
                all_children_positions[i] = child_positions
                side_children.append((i, child_positions))
        
        # STEP 5: Position branch nodes using clockwise positioning system
        for i, branch_data in enumerate(children):
            branch_text = branch_data['label']
            branch_font_size = self._get_adaptive_font_size(branch_text, 'branch')
            branch_width = self._calculate_text_width(branch_text, branch_font_size) + self._get_adaptive_padding(branch_text)
            branch_height = self._get_adaptive_node_height(branch_text, 'branch')
            
            # Determine which side this branch goes on based on clockwise positioning
            # For even distribution: first half goes RIGHT, second half goes LEFT
            # 6 branches: Branch 1,2,3 → RIGHT, Branch 4,5,6 → LEFT
            # 8 branches: Branch 1,2,3,4 → RIGHT, Branch 5,6,7,8 → LEFT
            mid_point = num_branches // 2
            is_left_side = i >= mid_point
            
            # Position branch in correct column
            if is_left_side:
                branch_x = left_branches_x
            else:
                branch_x = right_branches_x
            
            # Get children for this branch
            branch_children = all_children_positions.get(i, [])
            
            # Calculate branch Y position using clockwise positioning
            if branch_children:
                # Position branch at the center of its children group
                children_center_y = sum(child['y'] for child in branch_children) / len(branch_children)
                branch_y = children_center_y
                # Branch positioned (centered on children)
            else:
                # No children, use clockwise positioning
                branch_y = self._calculate_clockwise_branch_y(i, num_branches, is_left_side)
                # Branch positioned (clockwise)
            
            # Store branch position
            positions[f'branch_{i}'] = {
                'x': branch_x, 'y': branch_y,
                'width': branch_width, 'height': branch_height,
                'text': branch_text, 'node_type': 'branch',
                'branch_index': i, 'angle': 0,
                'fill': '#bbdefb',  # Light blue for branches
                'text_color': '#1565c0',  # Dark blue text for contrast
                'stroke': '#1976d2',  # Blue border
                'stroke_width': 2
            }
        
        # STEP 6: Position central topic at vertical center of all subtopic nodes
        # Calculate the vertical center of all branch nodes (subtopics)
        branch_positions = [pos for pos in positions.values() if pos['node_type'] == 'branch']
        
        if branch_positions:
            # Calculate vertical center of all branches using min/max range
            branch_y_positions = [pos['y'] for pos in branch_positions]
            min_branch_y = min(branch_y_positions)
            max_branch_y = max(branch_y_positions)
            topic_y = (min_branch_y + max_branch_y) / 2
            
            # Special alignment: Branch 2 (index 1) and Branch 5 (index 4) should align with central topic
            # Adjust their Y positions to match the central topic Y
            if num_branches >= 2:
                # Align Branch 2 (index 1) with central topic
                branch_2_key = f'branch_1'
                if branch_2_key in positions:
                    positions[branch_2_key]['y'] = topic_y
                    # Branch 2 aligned with central topic
            
            if num_branches >= 5:
                # Align Branch 5 (index 4) with central topic
                branch_5_key = f'branch_4'
                if branch_5_key in positions:
                    positions[branch_5_key]['y'] = topic_y
                    # Branch 5 aligned with central topic
            
            # Central topic positioned at vertical center of branches
        else:
            # Fallback if no branches
            topic_y = 0
            # Central topic positioned at default center
        
        # Position central topic
        topic_text = topic
        topic_font_size = self._get_adaptive_font_size(topic_text, 'topic')
        topic_width = self._calculate_text_width(topic_text, topic_font_size) + self._get_adaptive_padding(topic_text)
        topic_height = self._get_adaptive_node_height(topic_text, 'topic')
        
        positions['topic'] = {
            'x': 0, 'y': topic_y,  # Centered horizontally, vertically among branches
            'width': topic_width, 'height': topic_height,
            'text': topic_text, 'node_type': 'topic', 'angle': 0,
            'fill': '#1976d2',  # Deep blue for central topic
            'text_color': '#ffffff',  # White text for contrast
            'stroke': '#1565c0',  # Darker blue border
            'stroke_width': 3
        }
        
        # STEP 7: Generate connections
        connections = self._generate_connections(topic, children, positions)
        
        # STEP 8: Center all coordinates around (0,0) to prevent D3.js cutoff
        # Calculate the center of all content
        all_x = [pos['x'] for pos in positions.values()]
        all_y = [pos['y'] for pos in positions.values()]
        
        if all_x and all_y:
            content_center_x = (min(all_x) + max(all_x)) / 2
            content_center_y = (min(all_y) + max(all_y)) / 2
            
            # Adjust all positions to center around (0,0)
            for key in positions:
                positions[key]['x'] -= content_center_x
                positions[key]['y'] -= content_center_y
            
            # All coordinates centered around (0,0)
        
        # STEP 9: Compute recommended dimensions AFTER all positioning and centering is complete
        recommended_dimensions = self._compute_recommended_dimensions(positions, topic, children)
        
        # Final layout completed
        
        return {
            'algorithm': 'clean_vertical_stack',
            'positions': positions,
            'connections': connections,
            'params': {
                'leftChildrenX': left_children_x,
                'leftBranchesX': left_branches_x,
                'topicX': 0,
                'topicY': topic_y,  # Include topic Y position for reference
                'rightBranchesX': right_branches_x,
                'rightChildrenX': right_children_x,
                'numBranches': num_branches,
                'leftBranchCount': left_branch_count,
                'rightBranchCount': right_branch_count,
                'numChildren': sum(len(branch.get('children', [])) for branch in children),
                'baseWidth': recommended_dimensions['baseWidth'],
                'baseHeight': recommended_dimensions['baseHeight'],
                'width': recommended_dimensions['width'],
                'height': recommended_dimensions['height'],
                'padding': recommended_dimensions['padding'],
                'background': '#f5f5f5'  # Light grey background
            }
        }
    
    def _generate_connections(self, topic: str, children: List[Dict], positions: Dict) -> List[Dict]:
        """Generate connection data for lines between nodes."""
        connections = []
        
        topic_pos = positions.get('topic', {})
        topic_x, topic_y = topic_pos.get('x', 0), topic_pos.get('y', 0)
        
        # Connections from topic to branches
        for i, child in enumerate(children):
            branch_key = f'branch_{i}'
            if branch_key in positions:
                branch_pos = positions[branch_key]
                branch_x, branch_y = branch_pos['x'], branch_pos['y']
                
                connections.append({
                    'type': 'topic_to_branch',
                    'from': {'x': topic_x, 'y': topic_y, 'type': 'topic'},
                    'to': {'x': branch_x, 'y': branch_y, 'type': 'branch'},
                    'branch_index': i,
                    'stroke_width': 3,
                    'stroke_color': '#000000'  # Black connection for better visibility
                })
                
                # Connections from branch to children
                nested_children = child.get('children', [])
                for j, nested_child in enumerate(nested_children):
                    child_key = f'child_{i}_{j}'
                    if child_key in positions:
                        child_pos = positions[child_key]
                        child_x, child_y = child_pos['x'], child_pos['y']
                        
                        connections.append({
                            'type': 'branch_to_child',
                            'from': {'x': branch_x, 'y': branch_y, 'type': 'branch'},
                            'to': {'x': child_x, 'y': child_y, 'type': 'child'},
                            'branch_index': i,
                            'child_index': j,
                            'stroke_width': 2,
                            'stroke_color': '#000000'  # Black connection for better visibility
                        })
        
        return connections
    
    def _compute_recommended_dimensions(self, positions: Dict, topic: str, children: List[Dict]) -> Dict:
        """Compute recommended canvas dimensions based on content."""
        if not positions:
            return {"baseWidth": 800, "baseHeight": 600, "width": 800, "height": 600, "padding": 80}
        
        # Calculate bounds including node dimensions
        all_x = [pos['x'] for pos in positions.values()]
        all_y = [pos['y'] for pos in positions.values()]
        all_widths = [pos['width'] for pos in positions.values()]
        all_heights = [pos['height'] for pos in positions.values()]
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        max_width = max(all_widths)
        max_height = max(all_heights)
        
        # Calculate content dimensions CORRECTLY
        # For width: from leftmost node edge to rightmost node edge
        # For height: from topmost node edge to bottommost node edge
        content_width = (max_x + max_width/2) - (min_x - max_width/2)
        content_height = (max_y + max_height/2) - (min_y - max_height/2)
        
        # Add generous padding to prevent cutting off
        # Increase padding for height to account for vertical stacking
        padding_x = 140
        padding_y = 200  # Increased vertical padding to prevent cutting off
        
        total_width = content_width + (padding_x * 2)
        total_height = content_height + (padding_y * 2)
        
        # Ensure minimum dimensions
        total_width = max(total_width, 1000)  # Increased minimum width
        total_height = max(total_height, 800)  # Increased minimum height
        
        # Canvas calculation completed
        
        return {
            "baseWidth": total_width,
            "baseHeight": total_height,
            "width": total_width,
            "height": total_height,
            "padding": max(padding_x, padding_y)  # Use the larger padding value
        }
    
    def _get_adaptive_font_size(self, text: str, node_type: str) -> int:
        """Get adaptive font size based on text length and node type."""
        text_length = len(text)
        
        if node_type == 'topic':
            if text_length <= 10:
                return 28
            elif text_length <= 20:
                return 24
            else:
                return 20
        elif node_type == 'branch':
            if text_length <= 8:
                return 20
            elif text_length <= 15:
                return 18
            else:
                return 16
        else:  # child
            if text_length <= 6:
                return 16
            elif text_length <= 12:
                return 14
            else:
                return 12
    
    def _get_adaptive_node_height(self, text: str, node_type: str) -> int:
        """Get adaptive node height based on text length and node type."""
        text_length = len(text)
        
        if node_type == 'topic':
            if text_length <= 10:
                return 70
            elif text_length <= 20:
                return 60
            else:
                return 50
        elif node_type == 'branch':
            if text_length <= 8:
                return 60
            elif text_length <= 15:
                return 50
            else:
                return 45
        else:  # child
            if text_length <= 6:
                return 45
            elif text_length <= 12:
                return 40
            else:
                return 35
    
    def _calculate_text_width(self, text: str, font_size: int) -> float:
        """Calculate estimated text width based on font size."""
        if not text:
            return 0
        
        # More accurate text width calculation
        # Different character types have different widths
        total_width = 0
        for char in text:
            if char.isupper():
                # Uppercase letters are wider
                char_width = font_size * 0.8
            elif char.islower():
                # Lowercase letters are narrower
                char_width = font_size * 0.6
            elif char.isdigit():
                # Numbers are medium width
                char_width = font_size * 0.7
            elif char in '.,;:!?':
                # Punctuation is narrow
                char_width = font_size * 0.3
            elif char in 'MW':
                # Wide characters
                char_width = font_size * 1.0
            elif char in 'il|':
                # Narrow characters
                char_width = font_size * 0.3
            else:
                # Default for other characters
                char_width = font_size * 0.7
            
            total_width += char_width
        
        # Add a small amount for character spacing
        total_width += len(text) * 2
        
        return total_width
    
    def _get_adaptive_padding(self, text: str) -> int:
        """Get adaptive padding based on text length."""
        text_length = len(text)
        if text_length <= 5:
            return 30  # Increased padding
        elif text_length <= 10:
            return 35  # Increased padding
        elif text_length <= 15:
            return 40  # Increased padding
        else:
            return 45  # Increased padding
    
    def _get_adaptive_spacing(self, num_children: int) -> int:
        """Get adaptive spacing between children based on count."""
        if num_children <= 2:
            return 20  # Reduced spacing for tighter grouping
        elif num_children <= 4:
            return 18  # Reduced spacing
        elif num_children <= 6:
            return 15  # Reduced spacing
        else:
            return 12  # Reduced spacing
    
    def _calculate_clockwise_branch_y(self, branch_index: int, total_branches: int, is_left_side: bool) -> float:
        """
        Calculate Y position for branch using clockwise positioning system.
        
        Clockwise positioning with corrected side distribution:
        - Branch 1,2,3... (first half): RIGHT side (top to bottom)
        - Branch 4,5,6... (second half): LEFT side (top to bottom)
        
        For 6 branches: Branch 1,2,3 → RIGHT, Branch 4,5,6 → LEFT
        For 8 branches: Branch 1,2,3,4 → RIGHT, Branch 5,6,7,8 → LEFT
        """
        mid_point = total_branches // 2
        
        if is_left_side:
            # LEFT side branches (second half)
            # Calculate position within left side (0 = first left branch)
            left_index = branch_index - mid_point
            
            if total_branches <= 4:
                # 4 branches: Branch 3,4 → LEFT
                if left_index == 0:  # Branch 3 (Lower Left)
                    return -200
                else:  # Branch 4 (Top Left)
                    return 200
            elif total_branches <= 6:
                # 6 branches: Branch 4,5,6 → LEFT
                if left_index == 0:  # Branch 4 (Lower Left, top)
                    return -150
                elif left_index == 1:  # Branch 5 (Lower Left, bottom)
                    return -250
                else:  # Branch 6 (Top Left)
                    return 200
            elif total_branches <= 8:
                # 8 branches: Branch 5,6,7,8 → LEFT
                if left_index == 0:  # Branch 5 (Lower Left, top)
                    return -200
                elif left_index == 1:  # Branch 6 (Lower Left, bottom)
                    return -300
                elif left_index == 2:  # Branch 7 (Top Left, top)
                    return 300
                else:  # Branch 8 (Top Left, bottom)
                    return 200
            else:
                # For 9+ branches, use dynamic positioning
                base_y = 200
                spacing = 100
                return -base_y + (left_index * spacing)
        else:
            # RIGHT side branches (first half)
            # Calculate position within right side (0 = first right branch)
            right_index = branch_index
            
            if total_branches <= 4:
                # 4 branches: Branch 1,2 → RIGHT
                if right_index == 0:  # Branch 1 (Top Right)
                    return 200
                else:  # Branch 2 (Lower Right)
                    return -200
            elif total_branches <= 6:
                # 6 branches: Branch 1,2,3 → RIGHT
                if right_index == 0:  # Branch 1 (Top Right, top)
                    return 250
                elif right_index == 1:  # Branch 2 (Top Right, bottom)
                    return 150
                else:  # Branch 3 (Lower Right)
                    return -200
            elif total_branches <= 8:
                # 8 branches: Branch 1,2,3,4 → RIGHT
                if right_index == 0:  # Branch 1 (Top Right, top)
                    return 300
                elif right_index == 1:  # Branch 2 (Top Right, bottom)
                    return 200
                elif right_index == 2:  # Branch 3 (Lower Right, top)
                    return -200
                else:  # Branch 4 (Lower Right, bottom)
                    return -300
            else:
                # For 9+ branches, use dynamic positioning
                base_y = 200
                spacing = 100
                return base_y - (right_index * spacing)
    
    def _generate_empty_layout(self, topic: str) -> Dict:
        """Generate empty layout for edge cases."""
        return {
            'algorithm': 'empty',
            'positions': {'topic': {'x': 0, 'y': 0, 'width': 100, 'height': 50, 'text': topic, 'node_type': 'topic'}},
            'connections': [],
            'params': {'numBranches': 0, 'numChildren': 0}
        }
    
    def _generate_error_layout(self, topic: str, error_msg: str) -> Dict:
        """Generate error layout for error cases."""
        return {
            'algorithm': 'empty',
            'positions': {'topic': {'x': 0, 'y': 0, 'width': 100, 'height': 50, 'text': topic, 'node_type': 'topic'}},
            'connections': [],
            'params': {'error': error_msg, 'numBranches': 0, 'numChildren': 0}
        }
    
    # Removed deprecated _get_middle_branch_y_positions method - no longer needed
    
    def _get_max_branches(self) -> int:
        """Get maximum number of branches allowed."""
        return 20  # Reasonable limit for mind maps
