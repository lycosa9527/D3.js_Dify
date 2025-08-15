"""
Mind Map Agent

Enhances mind map specifications by:
- Normalizing and deduplicating topics and branches
- Ensuring proper hierarchical structure validation
- Implementing clockwise branch positioning (top-right, bottom-right, bottom-left, top-left)
- Computing optimal layout with radial positioning
- Providing recommended dimensions based on content complexity
- Generating SVG elements for visualization

The agent accepts a spec of the form:
  { "topic": str, "children": [ {"id": str, "label": str, "children": [{"id": str, "label": str}] } ] }

Returns { "success": bool, "spec": Dict } on success, or { "success": False, "error": str } on failure.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass


@dataclass
class NodePosition:
    """Data structure for node positioning in mind map"""
    x: float
    y: float
    width: float
    height: float
    text: str
    node_type: str  # 'topic', 'branch', 'child'
    branch_index: Optional[int] = None
    child_index: Optional[int] = None
    angle: Optional[float] = None  # Angle from center for radial positioning


class MindMapAgent:
    """Agent to enhance and generate mind map specifications with clockwise branch ordering."""

    # Dynamic limits based on content complexity
    def _get_max_branches(self, content_complexity: str = 'medium') -> int:
        """Get maximum branches based on content complexity."""
        limits = {'simple': 4, 'medium': 8, 'complex': 12, 'extreme': 16}
        return limits.get(content_complexity, 8)
    
    def _get_max_children_per_branch(self, content_complexity: str = 'medium') -> int:
        """Get maximum children per branch based on content complexity."""
        limits = {'simple': 4, 'medium': 6, 'complex': 8, 'extreme': 10}
        return limits.get(content_complexity, 6)

    def enhance_spec(self, spec: Dict) -> Dict:
        """
        Clean and enhance a mind map spec with clockwise branch positioning.

        Args:
            spec: { "topic": str, "children": [ {"id": str, "label": str, "children": [{"id": str, "label": str}] } ] }

        Returns:
            Dict with keys:
              - success: bool
              - spec: enhanced spec with layout and positioning data
        """
        try:
            if not isinstance(spec, dict):
                return {"success": False, "error": "Spec must be a dictionary"}

            topic_raw = spec.get("topic", "")
            children_raw = spec.get("children", [])

            if not isinstance(topic_raw, str) or not isinstance(children_raw, list):
                return {"success": False, "error": "Invalid field types in spec"}

            def clean_text(value: str) -> str:
                return (value or "").strip()

            topic: str = clean_text(topic_raw)
            if not topic:
                return {"success": False, "error": "Missing or empty topic"}

            # Normalize children (main branches)
            normalized_children: List[Dict] = []
            seen_ids: Set[str] = set()

            for i, child in enumerate(children_raw):
                if not isinstance(child, dict):
                    continue
                
                # Clean and validate required fields
                child_id = clean_text(child.get("id", ""))
                child_label = clean_text(child.get("label", ""))
                
                if not child_id or not child_label:
                    continue
                
                if child_id in seen_ids:
                    continue
                
                seen_ids.add(child_id)

                # Normalize nested children
                nested_children_raw = child.get("children", [])
                normalized_nested_children: List[Dict] = []
                
                if isinstance(nested_children_raw, list):
                    for j, nested_child in enumerate(nested_children_raw):
                        if not isinstance(nested_child, dict):
                            continue
                        
                        nested_id = clean_text(nested_child.get("id", ""))
                        nested_label = clean_text(nested_child.get("label", ""))
                        
                        if nested_id and nested_label and nested_id not in seen_ids:
                            seen_ids.add(nested_id)
                            normalized_nested_children.append({
                                "id": nested_id,
                                "label": nested_label
                            })
                            
                            if len(normalized_nested_children) >= self._get_max_children_per_branch():
                                break

                normalized_children.append({
                    "id": child_id,
                    "label": child_label,
                    "children": normalized_nested_children,
                })
                
                if len(normalized_children) >= self._get_max_branches():
                    break

            if not normalized_children:
                return {"success": False, "error": "At least one child branch is required"}

            # Generate layout with clockwise positioning
            layout = self._generate_mind_map_layout(topic, normalized_children)

            # Calculate recommended dimensions
            recommended = self._compute_recommended_dimensions(layout, topic, normalized_children)

            enhanced_spec: Dict = {
                "topic": topic,
                "children": normalized_children,
                "_layout": layout,
                "_recommended_dimensions": recommended,
                "_agent": {
                    "type": "mind_map",
                    "branchCount": len(normalized_children),
                    "maxChildrenPerBranch": max(len(child.get("children", [])) for child in normalized_children) if normalized_children else 0,
                    "positioning": "clockwise_radial"
                }
            }

            return {"success": True, "spec": enhanced_spec}
            
        except Exception as exc:
            return {"success": False, "error": f"MindMapAgent failed: {exc}"}

    def _generate_mind_map_layout(self, topic: str, children: List[Dict]) -> Dict:
        """Generate mind map layout with clockwise branch positioning."""
        
        # Calculate positions for all nodes
        positions = {}
        
        # Central topic at origin with dynamic dimensions
        topic_font_size = self._get_adaptive_font_size(topic, 'topic')
        topic_position = NodePosition(
            x=0.0, y=0.0,
            width=self._calculate_text_width(topic, topic_font_size),
            height=self._get_adaptive_node_height(topic, 'topic'),
            text=topic,
            node_type='topic'
        )
        positions['topic'] = {
            'x': topic_position.x,
            'y': topic_position.y,
            'width': topic_position.width,
            'height': topic_position.height,
            'node_type': topic_position.node_type,
            'text': topic_position.text
        }
        
        # Define angles to ensure branches only appear left or right of the topic
        # Right side: 0° to 45° and 315° to 360° (avoiding top/bottom)
        # Left side: 135° to 225° (avoiding top/bottom)
        num_branches = len(children)
        
        if num_branches == 1:
            angles = [45]  # Top-right
        elif num_branches == 2:
            angles = [45, 225]  # Top-right, bottom-left
        elif num_branches == 3:
            angles = [45, 315, 225]  # Top-right, bottom-right, bottom-left
        elif num_branches == 4:
            angles = [45, 315, 225, 135]  # Top-right, bottom-right, bottom-left, top-left
        elif num_branches == 5:
            # Elegant 5-branch layout with Branch 2 and 5 being longer
            # Branch 1 (45°), Branch 2 (0° - longer), Branch 3 (315°), Branch 4 (135°), Branch 5 (225° - longer)
            angles = [45, 0, 315, 135, 225]  # Top-right, middle-right, bottom-right, top-left, bottom-left
        else:
            # For more than 5 branches, use dynamic angles based on content density
            # Calculate optimal spacing to prevent overlap
            min_angle_separation = max(30, 360 // (num_branches + 2))  # Dynamic separation
            
            angles = []
            right_count = (num_branches + 1) // 2  # Right side gets one more if odd
            left_count = num_branches // 2
            
            # Right side angles (dynamic spacing)
            for i in range(right_count):
                angle = 45 - (i * min_angle_separation)
                if angle < -45:  # Don't go too far down
                    angle = 315 + (i - 2) * min_angle_separation
                angles.append(angle)
            
            # Left side angles (dynamic spacing)
            for i in range(left_count):
                angle = 135 + (i * min_angle_separation)
                if angle > 315:  # Don't go too far up
                    angle = 225 - (i - 2) * min_angle_separation
                angles.append(angle)
            
            # Sort to maintain clockwise order
            angles.sort(key=lambda x: (x + 45) % 360)
        
        # Calculate optimal distribution of all subtopics
        all_children_distribution = self._calculate_optimal_children_distribution(children)
        
        # PRESERVE CLOCKWISE ORDER: Don't reorder angles based on child count
        # This ensures Branch 1 = top-right, Branch 2 = middle-right, etc.
        # The clockwise sequence is more important than left-right balance for visual clarity
        
        # Note: Left-right balance is still achieved through the angle selection above
        # (e.g., 5 branches: 3 on right [45°, 0°, 315°], 2 on left [135°, 225°])
        
        # Calculate dynamic branch radius based on content complexity
        num_children_total = sum(len(child.get('children', [])) for child in children)
        base_branch_radius = self._calculate_adaptive_branch_radius(num_children_total, num_branches)
        
        # For 5 branches, make Branch 2 and 5 longer (more prominent)
        if num_branches == 5:
            # Branch indices: 0=45°, 1=0°, 2=315°, 3=135°, 4=225°
            # Make Branch 1 (0) and Branch 4 (4) longer
            branch_radius_multipliers = [1.0, 1.3, 1.0, 1.0, 1.3]  # 1.3x longer for branches 2 and 5
        else:
            # For other branch counts, use uniform radius
            branch_radius_multipliers = [1.0] * num_branches
        
        branch_positions = []
        
        for i, (child, angle_deg) in enumerate(zip(children, angles)):
            angle_rad = math.radians(angle_deg)
            
            # Calculate branch position with dynamic radius multiplier
            branch_radius = base_branch_radius * branch_radius_multipliers[i]
            branch_x = branch_radius * math.cos(angle_rad)
            branch_y = branch_radius * math.sin(angle_rad)
            
            branch_font_size = self._get_adaptive_font_size(child['label'], 'branch')
            branch_height = self._get_adaptive_node_height(child['label'], 'branch')
            branch_position = NodePosition(
                x=branch_x, y=branch_y,
                width=self._calculate_text_width(child['label'], branch_font_size) + self._get_adaptive_padding(child['label']),
                height=branch_height,
                text=child['label'],
                node_type='branch',
                branch_index=i,
                angle=angle_deg
            )
            
            positions[f'branch_{i}'] = {
                'x': branch_position.x,
                'y': branch_position.y,
                'width': branch_position.width,
                'height': branch_position.height,
                'node_type': branch_position.node_type,
                'branch_index': i,
                'angle': angle_deg,
                'text': branch_position.text
            }
            
            # Position children around their parent branch
            nested_children = child.get('children', [])
            if nested_children:
                child_positions = self._position_children_around_branch(
                    branch_position, nested_children, i
                )
                
                for j, (nested_child, child_pos) in enumerate(zip(nested_children, child_positions)):
                    positions[f'child_{i}_{j}'] = {
                        'x': child_pos.x,
                        'y': child_pos.y,
                        'width': child_pos.width,
                        'height': child_pos.height,
                        'node_type': child_pos.node_type,
                        'branch_index': i,
                        'child_index': j,
                        'text': child_pos.text
                    }
            
            branch_positions.append(branch_position)
        
        # Generate connection data
        connections = self._generate_connections(topic, children, positions)
        
        return {
            "algorithm": "clockwise_radial",
            "positions": positions,
            "connections": connections,
            "branch_angles": {i: angles[i] for i in range(len(angles))},
            "all_children_distribution": all_children_distribution,
            "params": {
                "branchRadius": base_branch_radius,
                "childRadius": 80,
                "angleOffset": 45,  # Starting angle
                "nodeSpacing": 1.5
            }
        }

    def _position_children_around_branch(self, branch_position: NodePosition, children: List[Dict], branch_index: int, all_children_distribution: Dict = None) -> List[NodePosition]:
        """Position children in a block-based layout around their parent branch to prevent overlap."""
        child_positions = []
        num_children = len(children)
        
        if num_children == 0:
            return child_positions
        
        # Calculate the angle from center to branch
        branch_angle = branch_position.angle or 0
        
        # Determine if this branch is on the left or right side of the center
        # Right side: -45° to 45° and 315° to 405° (wrapped)
        # Left side: 135° to 225°
        is_right_side = (-45 <= branch_angle <= 45) or (315 <= branch_angle <= 405)
        
        # Calculate block dimensions for this branch-subtopic group with adaptive sizing
        child_heights = [self._get_adaptive_node_height(child['label'], 'child') for child in children]
        child_spacing = self._get_adaptive_spacing(num_children)
        
        # Moderate spacing between children to prevent overlap
        # Add spacing based on child count, but keep it reasonable
        extra_spacing = max(15, num_children * 8)  # More reasonable spacing
        child_spacing += extra_spacing
        
        block_height = sum(child_heights) + (num_children - 1) * child_spacing
        
        # Calculate dynamic child radius based on content density and text length
        # More children = larger radius to prevent overlap
        # Longer text = more space needed
        max_text_width = max(self._calculate_text_width(child['label'], 14) for child in children)
        
        # Adaptive base radius based on branch density (more branches = more spacing needed)
        # Get total number of branches from the parent context
        total_branches = len([k for k in positions.keys() if k.startswith('branch_')]) if 'positions' in globals() else 6
        density_factor = min(total_branches / 4, 2.0)  # Scale up to 2x for many branches
        
        base_radius = int(120 * density_factor)  # Adaptive base distance
        
        if num_children <= 2:
            child_radius = base_radius + 30  # Few children: closer to branch
        elif num_children <= 5:
            child_radius = base_radius + 50  # Medium children: balanced distance
        else:
            child_radius = base_radius + 70  # Many children: spread out
        
        # Adjust for text length - longer text needs more space
        # Conservative scaling to maintain beautiful layout
        text_factor = min(max_text_width / 100, 1.8)  # Scale up to 1.8x for very long text
        child_radius = int(child_radius * (1 + (text_factor - 1) * 0.3))  # Conservative scaling
        
        # Ensure reasonable radius for very long text without being excessive
        if max_text_width > 200:
            child_radius = max(child_radius, int(max_text_width * 0.8))  # At least 80% of text width
        
        # Calculate child positions based on branch side with natural linear positioning
        # This maintains the beautiful, natural layout you loved
        if is_right_side:
            # Right side: arrange children to the right of the branch in a straight line
            current_y = branch_position.y - block_height / 2
            
            for i, child in enumerate(children):
                # Calculate individual dimensions for each child
                child_font_size = self._get_adaptive_font_size(child['label'], 'child')
                child_height = self._get_adaptive_node_height(child['label'], 'child')
                individual_child_width = self._calculate_text_width(child['label'], child_font_size) + self._get_adaptive_padding(child['label'])
                
                child_x = branch_position.x + child_radius
                child_y = current_y + child_height / 2
                current_y += child_height + child_spacing
                
                child_position = NodePosition(
                    x=child_x, y=child_y,
                    width=individual_child_width,
                    height=child_height,
                    text=child['label'],
                    node_type='child',
                    branch_index=branch_index,
                    child_index=i,
                    angle=branch_angle
                )
                
                child_positions.append(child_position)
        else:
            # Left side: arrange children to the left of the branch in a straight line
            current_y = branch_position.y - block_height / 2
            
            for i, child in enumerate(children):
                # Calculate individual dimensions for each child
                child_font_size = self._get_adaptive_font_size(child['label'], 'child')
                child_height = self._get_adaptive_node_height(child['label'], 'child')
                individual_child_width = self._calculate_text_width(child['label'], child_font_size) + self._get_adaptive_padding(child['label'])
                
                child_x = branch_position.x - child_radius
                child_y = current_y + child_height / 2
                current_y += child_height + child_spacing
                
                child_position = NodePosition(
                    x=child_x, y=child_y,
                    width=individual_child_width,
                    height=child_height,
                    text=child['label'],
                    node_type='child',
                    branch_index=branch_index,
                    child_index=i,
                    angle=branch_angle
                )
                
                child_positions.append(child_position)
        
        return child_positions



    def _position_all_children_globally(self, all_children_distribution: Dict, positions: Dict) -> None:
        """
        Position all subtopics globally based on the optimal distribution.
        This ensures proper left-right balance and prevents above/below placement.
        """
        if not all_children_distribution:
            return
        
        left_subtopics = all_children_distribution.get('left', [])
        right_subtopics = all_children_distribution.get('right', [])
        
        # Position left subtopics (left side of the canvas)
        if left_subtopics:
            self._position_subtopics_on_side(left_subtopics, positions, 'left')
        
        # Position right subtopics (right side of the canvas)
        if right_subtopics:
            self._position_subtopics_on_side(right_subtopics, positions, 'right')

    def _position_subtopics_on_side(self, subtopics: List[Dict], positions: Dict, side: str):
        """Position subtopics on a specific side (left or right) of the canvas."""
        if not subtopics:
            return
        
        # Calculate dimensions
        child_width = max(self._calculate_text_width(st['label'], 14) + 20 for st in subtopics)
        child_height = 40
        child_spacing = 20
        
        # Calculate total height needed
        total_height = len(subtopics) * child_height + (len(subtopics) - 1) * child_spacing
        
        # Determine base position based on side
        if side == 'left':
            base_x = -300  # Left side of canvas
        else:  # right
            base_x = 300   # Right side of canvas
        
        # Center vertically
        start_y = -total_height / 2 + child_height / 2
        
        # Position each subtopic
        for i, subtopic in enumerate(subtopics):
            child_x = base_x
            child_y = start_y + i * (child_height + child_spacing)
            
            # Create child position
            child_position = NodePosition(
                x=child_x, y=child_y,
                width=child_width,
                height=child_height,
                text=subtopic['label'],
                node_type='child',
                branch_index=subtopic['branch_index'],
                child_index=subtopic['child_index'],
                angle=0
            )
            
            # Store in positions
            positions[f'child_{subtopic["branch_index"]}_{subtopic["child_index"]}'] = {
                'x': child_position.x,
                'y': child_position.y,
                'width': child_position.width,
                'height': child_position.height,
                'node_type': child_position.node_type,
                'branch_index': subtopic['branch_index'],
                'child_index': subtopic['child_index'],
                'text': child_position.text
            }

    def _calculate_optimal_children_distribution(self, children: List[Dict]) -> Dict:
        """
        Calculate optimal distribution of all subtopics to ensure:
        1. Even distribution: left and right get equal numbers
        2. Uneven distribution: left gets one more than right
        3. No subtopics are placed above/below the topic (only left/right)
        """
        # Collect all subtopics from all branches
        all_subtopics = []
        for branch_index, branch in enumerate(children):
            nested_children = branch.get('children', [])
            for child_index, child in enumerate(nested_children):
                all_subtopics.append({
                    'branch_index': branch_index,
                    'child_index': child_index,
                    'label': child['label'],
                    'branch_angle': None  # Will be set later
                })
        
        total_subtopics = len(all_subtopics)
        if total_subtopics == 0:
            return {'left': [], 'right': []}
        
        # Calculate distribution
        if total_subtopics % 2 == 0:
            # Even number: split equally
            left_count = total_subtopics // 2
            right_count = total_subtopics // 2
        else:
            # Uneven number: left gets one more
            left_count = (total_subtopics // 2) + 1
            right_count = total_subtopics // 2
        
        # Distribute subtopics
        left_subtopics = all_subtopics[:left_count]
        right_subtopics = all_subtopics[left_count:]
        
        return {
            'left': left_subtopics,
            'right': right_subtopics,
            'total': total_subtopics,
            'left_count': left_count,
            'right_count': right_count
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
                    'stroke_color': '#2c3e50'
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
                            'stroke_color': '#34495e'
                        })
        
        return connections

    def _get_adaptive_font_size(self, text: str, node_type: str) -> int:
        """Get adaptive font size based on text length and node type."""
        text_length = len(text)
        
        if node_type == 'topic':
            if text_length <= 10:
                return 28  # Large for short topics
            elif text_length <= 20:
                return 24  # Standard for medium topics
            else:
                return 20  # Smaller for long topics
        elif node_type == 'branch':
            if text_length <= 8:
                return 20  # Larger for short branches
            elif text_length <= 15:
                return 18  # Standard for medium branches
            else:
                return 16  # Smaller for long branches
        else:  # child
            if text_length <= 6:
                return 16  # Larger for short children
            elif text_length <= 12:
                return 14  # Standard for medium children
            else:
                return 12  # Smaller for long children
    
    def _get_adaptive_node_height(self, text: str, node_type: str) -> int:
        """Get adaptive node height based on text length and node type."""
        text_length = len(text)
        
        if node_type == 'topic':
            if text_length <= 10:
                return 70  # Taller for short topics
            elif text_length <= 20:
                return 60  # Standard for medium topics
            else:
                return 50  # Shorter for long topics
        elif node_type == 'branch':
            if text_length <= 8:
                return 60  # Taller for short branches
            elif text_length <= 15:
                return 50  # Standard for medium branches
            else:
                return 45  # Shorter for long branches
        else:  # child
            if text_length <= 6:
                return 45  # Taller for short children
            elif text_length <= 12:
                return 40  # Standard for medium children
            else:
                return 35  # Shorter for long children

    def _calculate_text_width(self, text: str, font_size: int) -> float:
        """Calculate estimated text width based on font size."""
        if not text:
            return 0
        
        # Improved character width estimation for better accuracy
        char_widths = {
            # Narrow characters
            'i': 0.25, 'l': 0.25, 'I': 0.3, 'f': 0.35, 't': 0.35, 'r': 0.35, 'j': 0.25,
            # Medium characters  
            'a': 0.55, 'b': 0.55, 'c': 0.5, 'd': 0.55, 'e': 0.5, 'g': 0.55, 'h': 0.55,
            'k': 0.55, 'n': 0.55, 'o': 0.55, 'p': 0.55, 'q': 0.55, 's': 0.5, 'u': 0.55,
            'v': 0.5, 'x': 0.5, 'y': 0.5, 'z': 0.5,
            # Wide characters
            'm': 0.8, 'w': 0.8, 'M': 0.8, 'W': 0.8,
            # Numbers
            '0': 0.55, '1': 0.35, '2': 0.55, '3': 0.55, '4': 0.55, '5': 0.55,
            '6': 0.55, '7': 0.55, '8': 0.55, '9': 0.55,
            # Default for unknown characters
            'default': 0.55
        }
        
        total_width = 0
        for char in text:
            char_width = char_widths.get(char, char_widths['default'])
            total_width += char_width * font_size
        
        # Add padding: 20px base + extra padding for longer text
        padding = 20 + (len(text) * 2)  # More padding for longer text
        
        return total_width + padding

    def _calculate_adaptive_base_padding(self, content_size: float, num_branches: int, num_children: int) -> int:
        """Calculate adaptive base padding based on content complexity."""
        # Base padding scales with content size - more conservative values
        if content_size < 300:
            base = 60  # Minimal padding for very small content
        elif content_size < 500:
            base = 80  # Small padding for small content
        elif content_size < 800:
            base = 100  # Medium padding for medium content
        else:
            base = 120  # Large padding for large content (reduced from 150)
        
        # Adjust based on branch count (more branches = more spacing needed)
        branch_factor = min(num_branches / 4, 1.5)  # Reduced from 2.0 to 1.5
        base *= (1 + (branch_factor - 1) * 0.2)  # Reduced from 0.3 to 0.2
        
        # Adjust based on child count (more children = more spacing needed)
        base *= (1 + (min(num_children / 10, 1.3) - 1) * 0.15)  # Reduced from 0.2 to 0.15
        
        return int(base)

    def _calculate_adaptive_branch_radius(self, num_children_total: int, num_branches: int) -> int:
        """Calculate adaptive branch radius based on content density."""
        # Base radius scales with total children
        if num_children_total <= 3:
            base_radius = 180  # Very small content: close branches
        elif num_children_total <= 8:
            base_radius = 220  # Small content: moderate distance
        elif num_children_total <= 15:
            base_radius = 260  # Medium content: balanced distance
        elif num_children_total <= 25:
            base_radius = 300  # Large content: spread out
        else:
            base_radius = 350  # Very large content: maximum spread
        
        # Adjust based on branch count (more branches = more spacing needed)
        if num_branches <= 3:
            branch_factor = 0.9  # Closer for few branches
        elif num_branches <= 6:
            branch_factor = 1.0  # Standard for medium branches
        else:
            branch_factor = 1.2  # Further for many branches
        
        return int(base_radius * branch_factor)

    def _get_adaptive_padding(self, text: str) -> int:
        """Get adaptive padding based on text length."""
        text_length = len(text)
        if text_length <= 5:
            return 15  # Minimal padding for short text
        elif text_length <= 15:
            return 20  # Standard padding for medium text
        else:
            return 25  # Extra padding for long text
    
    def _get_adaptive_spacing(self, num_children: int) -> int:
        """Get adaptive spacing between children based on count."""
        if num_children <= 2:
            return 15  # Tighter spacing for few children
        elif num_children <= 5:
            return 20  # Standard spacing for medium count
        else:
            return 25  # Looser spacing for many children

    def _compute_recommended_dimensions(self, layout: Dict, topic: str, children: List[Dict]) -> Dict:
        """Calculate adaptive canvas dimensions based on layout to prevent overlap."""
        positions = layout.get("positions", {})
        
        if not positions:
            return {"baseWidth": 800, "baseHeight": 600, "width": 800, "height": 600, "padding": 80}
        
        # Find bounds of all positioned elements including their dimensions
        bounds = {
            'min_x': float('inf'),
            'max_x': float('-inf'),
            'min_y': float('inf'),
            'max_y': float('-inf')
        }
        
        for pos_data in positions.values():
            if isinstance(pos_data, dict) and 'x' in pos_data and 'y' in pos_data:
                x, y = pos_data['x'], pos_data['y']
                width = pos_data.get('width', 0) / 2  # Half width for centering
                height = pos_data.get('height', 0) / 2  # Half height for centering
                
                bounds['min_x'] = min(bounds['min_x'], x - width)
                bounds['max_x'] = max(bounds['max_x'], x + width)
                bounds['min_y'] = min(bounds['min_y'], y - height)
                bounds['max_y'] = max(bounds['max_y'], y + height)
        
        if bounds['min_x'] == float('inf'):
            return {"baseWidth": 800, "baseHeight": 600, "width": 800, "height": 600, "padding": 80}
        
        # Calculate required dimensions
        required_width = bounds['max_x'] - bounds['min_x']
        required_height = bounds['max_y'] - bounds['min_y']
        
        # Calculate dynamic padding based on actual content size and complexity
        content_size = max(required_width, required_height)
        num_branches = len([k for k in positions.keys() if k.startswith('branch_')])
        num_children = sum(len(pos.get('children', [])) for pos in positions.values() if pos.get('node_type') == 'branch')
        
        # Adaptive padding based on content size, branch count, and child count
        base_padding = self._calculate_adaptive_base_padding(content_size, num_branches, num_children)
        # More aggressive padding scaling - cap the minimum percentage
        min_padding_percentage = min(0.10, max(0.06, content_size / 1500))  # 6% to 10% based on size
        percentage_padding = content_size * min_padding_percentage
        
        # Use the smaller of base_padding or percentage_padding to prevent excessive padding
        padding = min(base_padding, percentage_padding)
        

        
        # Calculate final dimensions with intelligent padding
        width = required_width + (2 * padding)
        height = required_height + (2 * padding)
        
        # Ensure reasonable minimum dimensions based on content complexity
        min_width = max(800, required_width + self._calculate_adaptive_base_padding(content_size, 1, 1))
        min_height = max(500, required_height + int(self._calculate_adaptive_base_padding(content_size, 1, 1) * 0.7))
        
        # Use the larger of calculated vs minimum
        width = max(width, min_width)
        height = max(height, min_height)
        
        # Round up to nearest 50 for clean dimensions
        width = math.ceil(width / 50) * 50
        height = math.ceil(height / 50) * 50
        
        # Return consistent dimensions
        final_width = width
        final_height = height
        
        return {
            "baseWidth": final_width,
            "baseHeight": final_height,
            "width": final_width,
            "height": final_height,
            "padding": padding,
            "bounds": bounds,
            "required_dimensions": {
                "width": required_width,
                "height": required_height
            }
        }

    def generate_svg_data(self, enhanced_spec: Dict) -> Dict:
        """Generate SVG data for mind map visualization."""
        layout = enhanced_spec.get("_layout", {})
        dimensions = enhanced_spec.get("_recommended_dimensions", {})
        positions = layout.get("positions", {})
        connections = layout.get("connections", [])
        
        svg_elements = []
        
        # Calculate canvas center for positioning adjustment
        canvas_width = dimensions.get("width", 800)
        canvas_height = dimensions.get("height", 600)
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Generate connection lines first (so they appear behind nodes)
        for connection in connections:
            from_pos = connection['from']
            to_pos = connection['to']
            
            # Adjust positions to canvas center
            from_x = center_x + from_pos['x']
            from_y = center_y + from_pos['y']
            to_x = center_x + to_pos['x']
            to_y = center_y + to_pos['y']
            
            svg_elements.append({
                'type': 'line',
                'x1': from_x,
                'y1': from_y,
                'x2': to_x,
                'y2': to_y,
                'stroke': connection.get('stroke_color', '#666'),
                'stroke_width': connection.get('stroke_width', 2),
                'stroke_linecap': 'round'
            })
        
        # Generate nodes
        for node_key, pos_data in positions.items():
            x = center_x + pos_data['x']
            y = center_y + pos_data['y']
            node_type = pos_data['node_type']
            
            # Get node text
            if node_type == 'topic':
                text = enhanced_spec.get('topic', 'Topic')
                font_size = 24
                fill_color = '#2c3e50'
                font_weight = 'bold'
            elif node_type == 'branch':
                branch_index = pos_data.get('branch_index', 0)
                children = enhanced_spec.get('children', [])
                text = children[branch_index]['label'] if branch_index < len(children) else 'Branch'
                font_size = 18
                fill_color = '#34495e'
                font_weight = 'bold'
            elif node_type == 'child':
                branch_index = pos_data.get('branch_index', 0)
                child_index = pos_data.get('child_index', 0)
                children = enhanced_spec.get('children', [])
                if branch_index < len(children):
                    nested_children = children[branch_index].get('children', [])
                    text = nested_children[child_index]['label'] if child_index < len(nested_children) else 'Child'
                else:
                    text = 'Child'
                font_size = 14
                fill_color = '#2c3e50'  # Dark blue-grey for better contrast
                font_weight = 'normal'
            else:
                text = 'Node'
                font_size = 14
                fill_color = '#333'
                font_weight = 'normal'
            
            # Add background circle for nodes (optional styling)
            if node_type == 'topic':
                svg_elements.append({
                    'type': 'circle',
                    'cx': x,
                    'cy': y,
                    'r': 35,
                    'fill': '#ecf0f1',
                    'stroke': '#2c3e50',
                    'stroke_width': 2
                })
            elif node_type == 'branch':
                svg_elements.append({
                    'type': 'circle',
                    'cx': x,
                    'cy': y,
                    'r': 25,
                    'fill': '#ffffff',
                    'stroke': '#34495e',
                    'stroke_width': 2
                })
            else:  # child
                svg_elements.append({
                    'type': 'circle',
                    'cx': x,
                    'cy': y,
                    'r': 18,
                    'fill': '#ffffff',  # White background for better contrast
                    'stroke': '#3498db',  # Blue stroke for visual appeal
                    'stroke_width': 1.5
                })
            
            # Add text
            svg_elements.append({
                'type': 'text',
                'x': x,
                'y': y,
                'text': text,
                'font_size': font_size,
                'fill': fill_color,
                'text_anchor': 'middle',
                'dominant_baseline': 'middle',
                'font_weight': font_weight
            })
        
        return {
            'elements': svg_elements,
            'width': canvas_width,
            'height': canvas_height,
            'background': '#ffffff',
            'layout_data': layout
        }


__all__ = ["MindMapAgent"]
