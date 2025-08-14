"""
Multi-Flow Map Agent

This agent enhances the basic multi-flow map spec (event, causes, effects)
by cleaning data, de-duplicating entries, applying basic heuristics for
importance ordering, and recommending canvas dimensions based on content size.

Output remains a valid spec for existing D3 renderers, with optional
metadata under private keys (prefixed with "_") that renderers can ignore.
"""

from __future__ import annotations

from typing import Dict, List


class MultiFlowMapAgent:
    """Utility agent to improve multi-flow map specs before rendering."""

    MAX_ITEMS_PER_SIDE: int = 10

    def enhance_spec(self, spec: Dict) -> Dict:
        """
        Clean and enhance a multi-flow map spec.

        Args:
            spec: { "event": str, "causes": List[str], "effects": List[str] }

        Returns:
            Dict with keys:
              - success: bool
              - spec: enhanced spec (always valid against existing schema)
        """
        try:
            if not isinstance(spec, dict):
                return {"success": False, "error": "Spec must be a dictionary"}

            event_raw = spec.get("event", "")
            causes_raw = spec.get("causes", [])
            effects_raw = spec.get("effects", [])

            if not isinstance(event_raw, str) or not isinstance(causes_raw, list) or not isinstance(effects_raw, list):
                return {"success": False, "error": "Invalid field types in spec"}

            # Normalize text values
            def clean_text(value: str) -> str:
                return (value or "").strip()

            event: str = clean_text(event_raw)

            def normalize_list(items: List[str]) -> List[str]:
                seen = set()
                normalized: List[str] = []
                for item in items:
                    if not isinstance(item, str):
                        continue
                    cleaned = clean_text(item)
                    if not cleaned or cleaned in seen:
                        continue
                    seen.add(cleaned)
                    normalized.append(cleaned)
                # Clamp to maximum supported items
                return normalized[: self.MAX_ITEMS_PER_SIDE]

            causes: List[str] = normalize_list(causes_raw)
            effects: List[str] = normalize_list(effects_raw)

            if not event:
                return {"success": False, "error": "Missing or empty event"}
            if not causes:
                return {"success": False, "error": "At least one cause is required"}
            if not effects:
                return {"success": False, "error": "At least one effect is required"}

            # Basic importance heuristic (longer text may need larger radius)
            def score_importance(text: str) -> int:
                length = len(text)
                if length >= 30:
                    return 3
                if length >= 15:
                    return 2
                return 1

            cause_importance = [score_importance(c) for c in causes]
            effect_importance = [score_importance(e) for e in effects]

            # Calculate dimensions based on content complexity
            max_side = max(len(causes), len(effects))
            total_items = len(causes) + len(effects)
            
            # Estimate text width requirements (rough approximation)
            max_cause_length = max((len(c) for c in causes), default=0)
            max_effect_length = max((len(e) for e in effects), default=0)
            max_text_length = max(max_cause_length, max_effect_length, len(event))
            
            # Dynamic width calculation based on content
            # Base width accounts for: margins + side gaps + central event
            base_width = 600  # Reduced base for better scaling
            text_width_factor = max_text_length * 8  # Approximate pixels per character
            width_for_sides = text_width_factor * 2 + 300  # Both sides + gaps
            width = max(base_width, width_for_sides)
            
            # Dynamic height calculation (optimized for minimal excess space)
            base_height = 300  # Smaller base height for better scaling
            
            # Realistic item height calculation with slight scaling for larger content
            base_item_height = 35  # Base: ~16px text + 19px padding/spacing
            # Add slight scaling for larger content to prevent overcrowding
            scaling_factor = 1.0 + (max_side - 2) * 0.02  # 2% per item beyond 2
            item_height_estimate = base_item_height * min(scaling_factor, 1.3)  # Cap at 30% increase
            
            event_and_margins = 140  # Central event (50px) + top/bottom margins (90px total)
            height_for_content = max_side * item_height_estimate + event_and_margins
            height = max(base_height, height_for_content)
            
            # Additional height for very long text (but more conservative)
            if max_text_length > 50:
                # Only add extra height for really long text that might wrap
                extra_height = min(100, (max_text_length - 50) * 1.5)  # Much more conservative
                height += extra_height

            enhanced_spec: Dict = {
                "event": event,
                "causes": causes,
                "effects": effects,
                # Private metadata for optional renderer consumption
                "_agent": {
                    "type": "multi_flow_map",
                    "cause_importance": cause_importance,
                    "effect_importance": effect_importance,
                },
                "_recommended_dimensions": {
                    "baseWidth": width,
                    "baseHeight": height,
                    "padding": 40,
                    "width": width,
                    "height": height,
                },
            }

            return {"success": True, "spec": enhanced_spec}
        except Exception as exc:  # Defensive guard
            return {"success": False, "error": f"Unexpected error: {exc}"}


