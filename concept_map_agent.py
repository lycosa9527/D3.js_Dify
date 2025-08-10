"""
Concept Map Agent

Enhances concept map specifications by:
- Normalizing and deduplicating concepts
- Ensuring relationships reference existing concepts and deduplicating unordered pairs
- Cleaning labels
- Generating layout hints (rings, clusters, angle hints)
- Computing evenly-spread node positions with a lightweight force routine
- Providing recommended dimensions sized to fit all content
"""

from typing import Dict, List, Set, Tuple

# Import configuration
try:
    from concept_map_config import *
except ImportError:
    # Default values if config file not found
    NODE_SPACING = 1.2
    CANVAS_PADDING = 80
    MIN_NODE_DISTANCE = 120
    INNER_RADIUS = 0.25
    MIN_RADIUS = 0.45
    MAX_RADIUS = 0.95
    GAP_FACTOR = 0.9
    TARGET_RADIUS = 0.75
    REPULSION_FORCE = 0.025
    SPRING_FORCE = 0.03
    STEP_SIZE = 0.15
    ITERATIONS = 200


class ConceptMapAgent:
    """Agent to enhance and sanitize concept map specifications."""

    MAX_CONCEPTS: int = 30
    MAX_LABEL_LEN: int = 60

    def enhance_spec(self, spec: Dict) -> Dict:
        try:
            if not isinstance(spec, dict):
                return {"success": False, "error": "Spec must be a dictionary"}

            topic = spec.get("topic")
            concepts = spec.get("concepts") or []
            relationships = spec.get("relationships") or []

            if not isinstance(topic, str) or not topic.strip():
                return {"success": False, "error": "Invalid or missing 'topic'"}
            if not isinstance(concepts, list) or not isinstance(relationships, list):
                return {"success": False, "error": "'concepts' and 'relationships' must be lists"}

            normalized_topic = self._clean_text(topic, self.MAX_LABEL_LEN)

            def canonical(label: str) -> str:
                # Canonical form for matching: lowercase + remove all whitespace
                if not isinstance(label, str):
                    return ""
                import re
                s = label.lower()
                s = re.sub(r"\s+", "", s)
                return s

            # Normalize and dedupe concepts
            normalized_concepts: List[str] = []
            seen: Set[str] = set()
            canon_to_display: Dict[str, str] = {}
            for c in concepts:
                if not isinstance(c, str):
                    continue
                cleaned = self._clean_text(c, self.MAX_LABEL_LEN)
                canon = canonical(cleaned)
                if cleaned and canon not in seen and cleaned != normalized_topic:
                    normalized_concepts.append(cleaned)
                    seen.add(canon)
                    canon_to_display[canon] = cleaned
                if len(normalized_concepts) >= self.MAX_CONCEPTS:
                    break

            concept_set: Set[str] = set(normalized_concepts)

            # Sanitize relationships and enforce single edge between unordered pair
            sanitized_relationships: List[Dict[str, str]] = []
            missing_concepts: Set[str] = set()
            pair_seen_unordered: Set[Tuple[str, str]] = set()
            for rel in relationships:
                if not isinstance(rel, dict):
                    continue
                frm_raw = self._clean_text(rel.get("from", ""), self.MAX_LABEL_LEN)
                to_raw = self._clean_text(rel.get("to", ""), self.MAX_LABEL_LEN)
                label = self._clean_text(rel.get("label", ""), self.MAX_LABEL_LEN)
                if not frm_raw or not to_raw or not label:
                    continue
                # Canonical matching to align with concept set
                frm_c = canonical(frm_raw)
                to_c = canonical(to_raw)
                topic_c = canonical(normalized_topic)
                if frm_c == to_c:
                    continue
                # Map canonical back to display
                frm = canon_to_display.get(frm_c, frm_raw)
                to = canon_to_display.get(to_c, to_raw)
                key = tuple(sorted((frm_c, to_c)))
                if key in pair_seen_unordered:
                    continue
                pair_seen_unordered.add(key)

                if frm_c not in seen and frm_c != topic_c:
                    missing_concepts.add(frm_c)  # Store canonical form
                if to_c not in seen and to_c != topic_c:
                    missing_concepts.add(to_c)  # Store canonical form

                sanitized_relationships.append({"from": frm, "to": to, "label": label})

            # Add missing endpoints as concepts if capacity allows
            for mc_canon in list(missing_concepts):
                if len(normalized_concepts) < self.MAX_CONCEPTS and mc_canon not in seen:
                    # Find the original display text for this canonical form
                    mc_display = None
                    for rel in relationships:
                        if isinstance(rel, dict):
                            frm_raw = self._clean_text(rel.get("from", ""), self.MAX_LABEL_LEN)
                            to_raw = self._clean_text(rel.get("to", ""), self.MAX_LABEL_LEN)
                            if canonical(frm_raw) == mc_canon:
                                mc_display = frm_raw
                                break
                            elif canonical(to_raw) == mc_canon:
                                mc_display = to_raw
                                break
                    
                    if mc_display:
                        normalized_concepts.append(mc_display)
                        seen.add(mc_canon)
                        canon_to_display[mc_canon] = mc_display

            # Final filter: drop any relationship whose endpoints are not in concepts or topic
            concept_or_topic = set(normalized_concepts)
            concept_or_topic.add(normalized_topic)
            sanitized_relationships = [
                r for r in sanitized_relationships
                if r["from"] in concept_or_topic and r["to"] in concept_or_topic
            ]

            # If spec already contains keys/parts from a two-stage workflow, use them for sector layout
            if isinstance(spec.get('keys'), list):
                layout = self._generate_layout_sectors_from_keys_parts(normalized_topic, spec)
            elif spec.get('_method') == 'enhanced_30':
                # Use radial/circular layout for enhanced_30 method (concentric circles)
                layout = self._generate_layout_radial(normalized_topic, normalized_concepts, sanitized_relationships)
            elif spec.get('_method') == 'network_first':
                # Use Sugiyama layout for network-first approach
                layout = self._generate_layout_sugiyama(normalized_topic, normalized_concepts, sanitized_relationships)
            else:
                # Default: use Sugiyama layout for structured organization
                layout = self._generate_layout_sugiyama(normalized_topic, normalized_concepts, sanitized_relationships)

            # Compute recommended dimensions based on normalized positions extents
            recommended = self._compute_recommended_dimensions_from_layout(
                layout=layout,
                topic=normalized_topic,
                concepts=normalized_concepts,
            )

            enhanced_spec: Dict = {
                "topic": normalized_topic,
                "concepts": normalized_concepts,
                "relationships": sanitized_relationships,
                "_layout": layout,
                "_recommended_dimensions": recommended,
                "_config": {
                    "nodeSpacing": 4.0,  # Maximum node spacing multiplier (increased from 3.0)
                    "canvasPadding": 140,  # Even more padding around the diagram (increased from 120)
                    "minNodeDistance": 320  # Maximum minimum distance between nodes in pixels (increased from 250)
                }
            }
            
            # Preserve important metadata from original spec
            if spec.get('_method'):
                enhanced_spec['_method'] = spec['_method']
            if spec.get('_concept_count'):
                enhanced_spec['_concept_count'] = spec['_concept_count']

            if isinstance(spec.get("_style"), dict):
                enhanced_spec["_style"] = spec["_style"]

            return {"success": True, "spec": enhanced_spec}
        except Exception as exc:
            return {"success": False, "error": f"ConceptMapAgent failed: {exc}"}

    def generate_simplified_two_stage(self, user_prompt: str, llm_client, language: str = "en") -> Dict:
        """
        Generate concept map using simplified two-stage approach.
        
        Stage 1: Generate concepts
        Stage 2: Generate relationships
        
        This approach is much more reliable than the complex unified generation.
        """
        try:
            # Stage 1: Generate concepts using enhanced prompts
            stage1_prompt_key = f"concept_map_enhanced_stage1_{language}"
            stage1_prompt = self._get_prompt(stage1_prompt_key, user_prompt=user_prompt)
            
            # Fallback to original prompts if enhanced not found
            if not stage1_prompt:
                stage1_prompt_key = f"concept_map_stage1_concepts_{language}"
                stage1_prompt = self._get_prompt(stage1_prompt_key, user_prompt=user_prompt)
            
            if not stage1_prompt:
                return {"success": False, "error": f"Prompt not found: {stage1_prompt_key}"}
            
            # Get concepts from LLM
            concepts_response = self._get_llm_response(llm_client, stage1_prompt)
            if not concepts_response:
                return {"success": False, "error": "No response from LLM for concepts generation"}
            
            # Parse concepts response
            try:
                concepts_data = self._parse_json_response(concepts_response)
                if not concepts_data:
                    return {"success": False, "error": "Failed to parse concepts response"}
                
                topic = concepts_data.get("topic", "")
                concepts = concepts_data.get("concepts", [])
                
                if not topic or not concepts:
                    return {"success": False, "error": "Missing topic or concepts in response"}
                
            except Exception as e:
                return {"success": False, "error": f"Failed to parse concepts: {str(e)}"}
            
            # Stage 2: Generate relationships using enhanced prompts
            stage2_prompt_key = f"concept_map_enhanced_stage2_{language}"
            stage2_prompt = self._get_prompt(stage2_prompt_key, topic=topic, concepts=concepts)
            
            # Fallback to original prompts if enhanced not found
            if not stage2_prompt:
                stage2_prompt_key = f"concept_map_stage2_relationships_{language}"
                stage2_prompt = self._get_prompt(stage2_prompt_key, topic=topic, concepts=concepts)
            
            if not stage2_prompt:
                return {"success": False, "error": f"Prompt not found: {stage2_prompt_key}"}
            
            # Get relationships from LLM
            relationships_response = self._get_llm_response(llm_client, stage2_prompt)
            if not relationships_response:
                return {"success": False, "error": "No response from LLM for relationships generation"}
            
            # Parse relationships response
            try:
                relationships_data = self._parse_json_response(relationships_response)
                if not relationships_data:
                    return {"success": False, "error": "Failed to parse relationships response"}
                
                relationships = relationships_data.get("relationships", [])
                
                if not relationships:
                    return {"success": False, "error": "No relationships generated"}
                
            except Exception as e:
                return {"success": False, "error": f"Failed to parse relationships: {str(e)}"}
            
            # Combine and enhance
            combined_spec = {
                "topic": topic,
                "concepts": concepts,
                "relationships": relationships
            }
            
            # Enhance the specification
            enhanced_spec = self.enhance_spec(combined_spec)
            if not enhanced_spec.get("success", False):
                return enhanced_spec
            
            return enhanced_spec
            
        except Exception as e:
            return {"success": False, "error": f"Two-stage generation failed: {str(e)}"}
    
    def generate_three_stage(self, user_prompt: str, llm_client, language: str = "en") -> Dict:
        """
        Generate concept map using streamlined 2-stage approach.
        
        Uses existing topic extraction from main agent, then:
        Stage 1: Generate exactly 30 key concepts based on user prompt  
        Stage 2: Generate relationships between topic and all concepts
        
        This approach integrates with existing workflow: [existing topic extraction] → 30 concepts → relationships.
        """
        try:
            # Use the existing LLM calling pattern from agent.py
            from agent import _invoke_llm_prompt
            
            # Stage 1: Generate exactly 30 concepts based on user prompt
            concepts_prompt_key = f"concept_map_30_concepts_{language}"
            concepts_prompt = self._get_prompt(concepts_prompt_key, central_topic=user_prompt)
            
            if not concepts_prompt:
                return {"success": False, "error": f"30 concepts prompt not found: {concepts_prompt_key}"}
            
            # Get concepts using the existing LLM pattern
            concepts_response = _invoke_llm_prompt(concepts_prompt, {})
            if not concepts_response:
                return {"success": False, "error": "No response from LLM for concepts generation"}
            
            # Parse concepts response
            try:
                concepts_data = self._parse_json_response(concepts_response)
                if not concepts_data:
                    return {"success": False, "error": "Failed to parse concepts response"}
                
                concepts = concepts_data.get("concepts", [])
                if not concepts:
                    return {"success": False, "error": "No concepts generated"}
                
                # Validate we have exactly 30 concepts
                if len(concepts) != 30:
                    # Try to adjust to exactly 30
                    if len(concepts) > 30:
                        concepts = concepts[:30]  # Take first 30
                    else:
                        # Pad with generic concepts if less than 30
                        while len(concepts) < 30:
                            concepts.append(f"Related concept {len(concepts) + 1}")
                
            except Exception as e:
                return {"success": False, "error": f"Failed to parse concepts: {str(e)}"}
            
            # Extract topic from user prompt for relationships
            # Use a simple extraction method instead of full LLM call
            central_topic = self._extract_simple_topic(user_prompt)
            
            # Stage 2: Generate relationships
            relationships_prompt_key = f"concept_map_3_stage_relationships_{language}"
            relationships_prompt = self._get_prompt(relationships_prompt_key, 
                                                   central_topic=central_topic, 
                                                   concepts=concepts)
            
            if not relationships_prompt:
                return {"success": False, "error": f"3-stage relationships prompt not found: {relationships_prompt_key}"}
            
            # Get relationships using the existing LLM pattern
            relationships_response = _invoke_llm_prompt(relationships_prompt, {})
            if not relationships_response:
                return {"success": False, "error": "No response from LLM for relationships generation"}
            
            # Parse relationships response
            try:
                relationships_data = self._parse_json_response(relationships_response)
                if not relationships_data:
                    return {"success": False, "error": "Failed to parse relationships response"}
                
                relationships = relationships_data.get("relationships", [])
                if not relationships:
                    return {"success": False, "error": "No relationships generated"}
                
            except Exception as e:
                return {"success": False, "error": f"Failed to parse relationships: {str(e)}"}
            
            # Combine into concept map spec
            concept_map_spec = {
                "topic": central_topic,  # Use extracted central topic
                "concepts": concepts,    # Exactly 30 concepts
                "relationships": relationships,
                "_method": "three_stage",  # Mark for identification
                "_stage_info": {
                    "original_prompt": user_prompt,
                    "extracted_topic": central_topic,
                    "concept_count": len(concepts),
                    "relationship_count": len(relationships)
                }
            }
            
            # Enhance the spec using existing method
            enhanced_spec = self.enhance_spec(concept_map_spec)
            return enhanced_spec
            
        except Exception as e:
            return {"success": False, "error": f"Three-stage concept map generation failed: {str(e)}"}

    def _extract_simple_topic(self, user_prompt: str) -> str:
        """Extract a simple topic from user prompt using basic text processing."""
        import re
        
        # Clean and extract key phrases
        prompt = user_prompt.lower().strip()
        
        # Remove common phrases
        prompt = re.sub(r'\b(i want to|help me|create|generate|make|build|understand|learn about|about)\b', '', prompt)
        prompt = re.sub(r'\b(concept map|mind map|diagram|graph|visualization)\b', '', prompt)
        
        # Extract the main subject
        words = prompt.split()
        # Filter out common words and take meaningful terms
        meaningful_words = [w for w in words if len(w) > 2 and w not in 
                          {'the', 'and', 'for', 'with', 'how', 'what', 'why', 'when', 'where'}]
        
        if meaningful_words:
            # Take first 2-3 meaningful words as topic
            topic = ' '.join(meaningful_words[:3])
            return topic.title()
        else:
            # Fallback to first few words
            return ' '.join(user_prompt.split()[:3]).title()
    
    def generate_network_first(self, user_prompt: str, llm_client, language: str = "en") -> Dict:
        """
        Generate concept map using network-first approach.
        
        Stage 1: Generate comprehensive list of concepts
        Stage 2: Generate relationship matrix between all concepts
        
        This approach ensures rich interconnections between all nodes.
        """
        try:
            # Stage 1: Generate comprehensive concept list using enhanced prompts
            stage1_prompt_key = f"concept_map_enhanced_stage1_{language}"
            stage1_prompt = self._get_prompt(stage1_prompt_key, user_prompt=user_prompt)
            
            # Fallback to network-specific prompts if enhanced not found
            if not stage1_prompt:
                stage1_prompt_key = f"concept_map_network_stage1_{language}"
                stage1_prompt = self._get_prompt(stage1_prompt_key, user_prompt=user_prompt)
            
            if not stage1_prompt:
                # Fallback to English if language-specific prompt not found
                stage1_prompt = self._get_prompt("concept_map_network_stage1_en", user_prompt=user_prompt)
            
            stage1_response = self._get_llm_response(llm_client, stage1_prompt)
            concepts_data = self._parse_json_response(stage1_response)
            
            if not concepts_data or "concepts" not in concepts_data:
                raise ValueError("Failed to parse concepts from stage 1")
            
            concepts = concepts_data["concepts"]
            topic = concepts_data.get("topic", user_prompt)
            
            # Stage 2: Generate relationship matrix
            stage2_prompt_key = f"concept_map_network_stage2_{language}"
            stage2_prompt = self._get_prompt(stage2_prompt_key, 
                                           user_prompt=user_prompt,
                                           concepts=concepts,
                                           topic=topic)
            if not stage2_prompt:
                # Fallback to English if language-specific prompt not found
                stage2_prompt = self._get_prompt("concept_map_network_stage2_en", 
                                               user_prompt=user_prompt,
                                               concepts=concepts,
                                               topic=topic)
            
            print(f"DEBUG: Stage 2 prompt: {stage2_prompt}")
            stage2_response = self._get_llm_response(llm_client, stage2_prompt)
            print(f"DEBUG: Stage 2 response: {stage2_response}")
            relationships_data = self._parse_json_response(stage2_response)
            print(f"DEBUG: Parsed relationships data: {relationships_data}")
            
            if not relationships_data or "relationships" not in relationships_data:
                raise ValueError("Failed to parse relationships from stage 2")
            
            # Combine into concept map spec
            concept_map_spec = {
                "topic": topic,
                "concepts": concepts,
                "relationships": relationships_data["relationships"],
                "_method": "network_first"  # Mark for force-directed layout
            }
            
            # Enhance the spec using existing method
            enhanced_spec = self.enhance_spec(concept_map_spec)
            return enhanced_spec
            
        except Exception as e:
            raise ValueError(f"Network-first concept map generation failed: {str(e)}")

    def _get_prompt(self, prompt_key: str, **kwargs) -> str:
        """Get prompt from the prompts module."""
        try:
            from prompts.concept_maps import CONCEPT_MAP_PROMPTS
            
            # Try to get the language-specific prompt first
            language = kwargs.get('language', 'en')
            if language == 'zh':
                # Try Chinese version first
                zh_key = prompt_key.replace('_en', '_zh')
                prompt_template = CONCEPT_MAP_PROMPTS.get(zh_key)
                if prompt_template:
                    return prompt_template.format(**kwargs)
            
            # Fallback to English version
            prompt_template = CONCEPT_MAP_PROMPTS.get(prompt_key)
            if prompt_template:
                return prompt_template.format(**kwargs)
            
            # If we still don't have a prompt, log the issue
            print(f"Warning: No prompt found for key '{prompt_key}' (language: {language})")
            print(f"Available keys: {list(CONCEPT_MAP_PROMPTS.keys())}")
            return None
        except ImportError as e:
            print(f"Error importing prompts module: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in _get_prompt: {e}")
            return None
    
    def _get_llm_response(self, llm_client, prompt: str) -> str:
        """Get response from LLM client, handling different client types."""
        try:
            # Check if it's a mock client with get_response method
            if hasattr(llm_client, 'get_response'):
                return llm_client.get_response(prompt)
            
            # Check if it's a LangChain LLM client with invoke method
            elif hasattr(llm_client, 'invoke'):
                # Use LangChain's invoke method
                from langchain.prompts import PromptTemplate
                pt = PromptTemplate(input_variables=[], template=prompt)
                result = llm_client.invoke(pt)
                return str(result) if result else ""
            
            # Check if it's an async client with chat_completion method
            elif hasattr(llm_client, 'chat_completion'):
                # For now, return a mock response since we can't easily run async here
                # In production, you'd want to properly handle the async call
                if "concepts" in prompt.lower():
                    return '{"topic": "Test Topic", "concepts": ["Concept 1", "Concept 2", "Concept 3"]}'
                elif "relationships" in prompt.lower():
                    return '{"relationships": [{"from": "Concept 1", "to": "Concept 2", "label": "relates to"}]}'
                else:
                    return '{"result": "mock response"}'
            
            # Fallback for other client types
            else:
                raise ValueError(f"Unsupported LLM client type: {type(llm_client)}")
                
        except Exception as e:
            raise ValueError(f"Failed to get LLM response: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON response from LLM, handling common formatting issues.
        
        This method includes multiple fallback strategies:
        1. Direct JSON parsing
        2. Fix unterminated strings and balance braces
        3. Extract JSON from markdown blocks
        4. Find JSON-like content with regex
        5. Create fallback responses from partial content
        6. Generate generic fallback if all else fails
        """
        try:
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Try to parse as JSON
            import json
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            # Log the original error for debugging
            import logging
            logging.warning(f"JSON parsing failed: {e}")
            logging.debug(f"Original response: {response[:500]}...")  # Log first 500 chars
            
            # Log the full response for debugging (truncated if too long)
            if len(response) > 1000:
                logging.debug(f"Full response (truncated): {response[:1000]}...")
            else:
                logging.debug(f"Full response: {response}")
            
            # Try to fix unterminated strings and other common issues
            try:
                import re
                
                # Fix unterminated strings by finding the last complete quote
                # Look for patterns like "text" where the quote might be missing
                cleaned = re.sub(r'"([^"]*?)(?=\s*[,}\]]|$)', r'"\1"', cleaned)
                
                # Fix unescaped quotes within strings
                # This is tricky, but we can try to balance quotes
                quote_count = cleaned.count('"')
                if quote_count % 2 == 1:  # Odd number of quotes
                    # Find the last quote and see if we can balance it
                    last_quote_pos = cleaned.rfind('"')
                    if last_quote_pos > 0:
                        # Check if this looks like an unterminated string
                        before_quote = cleaned[:last_quote_pos]
                        if before_quote.rstrip().endswith(':'):
                            # This looks like a key without a value, remove it
                            cleaned = cleaned[:last_quote_pos].rstrip().rstrip(':').rstrip()
                            cleaned += '}'
                
                # Additional fix for unterminated strings at the end
                # Look for patterns like "key": "value where the closing quote is missing
                cleaned = re.sub(r'"([^"]*?)(?=\s*[,}\]]|$)', r'"\1"', cleaned)
                
                # Try to balance braces if they're mismatched
                open_braces = cleaned.count('{')
                close_braces = cleaned.count('}')
                if open_braces > close_braces:
                    cleaned += '}' * (open_braces - close_braces)
                elif close_braces > open_braces:
                    # Remove extra closing braces from the end
                    cleaned = cleaned.rstrip('}')
                    # Add back the right number
                    cleaned += '}' * open_braces
                
                logging.info(f"Attempting to parse cleaned JSON after fixes")
                # Try to parse the cleaned JSON
                result = json.loads(cleaned)
                logging.info(f"Successfully parsed JSON after applying fixes")
                return result
                
            except json.JSONDecodeError as e2:
                logging.warning(f"Cleaned JSON parsing also failed: {e2}")
                pass
            
            # Try to find JSON-like content
            try:
                import re
                json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
            
            # Try to fix common issues
            try:
                # Remove any leading/trailing whitespace and newlines
                cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)
                # Try to find the start and end of JSON
                start = cleaned.find('{')
                end = cleaned.rfind('}') + 1
                if start >= 0 and end > start:
                    json_content = cleaned[start:end]
                    return json.loads(json_content)
            except json.JSONDecodeError:
                pass
            
            # Try to extract whatever concepts we can find from the response
            topic_match = re.search(r'"topic"\s*:\s*"([^"]+)"', cleaned)
            topic = topic_match.group(1) if topic_match else "Unknown Topic"
            
            # Extract concepts using multiple patterns - take whatever we can find
            concepts = []
            
            # Pattern 1: Look for concepts array
            concepts_match = re.search(r'"concepts"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
            if concepts_match:
                concepts_str = concepts_match.group(1)
                concepts = [c.strip().strip('"') for c in concepts_str.split(',') if c.strip()]
                logging.info(f"Extracted concepts using Pattern 1 (concepts array): {concepts}")
            
            # Pattern 2: Look for keys array (for two-stage approach)
            if not concepts:
                keys_match = re.search(r'"keys"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
                if keys_match:
                    keys_str = keys_match.group(1)
                    # Extract names from key objects
                    key_names = re.findall(r'"name"\s*:\s*"([^"]+)"', keys_str)
                    concepts.extend(key_names)
                    logging.info(f"Extracted concepts using Pattern 2 (keys array): {concepts}")
            
            # Pattern 3: Look for individual concept-like strings in the response
            if not concepts:
                # Find all quoted strings that look like concept names
                concept_candidates = re.findall(r'"([^"]{2,20})"', cleaned)
                # Filter out common JSON keys and short strings
                json_keys = {'topic', 'concepts', 'keys', 'key_parts', 'relationships', 'from', 'to', 'label'}
                concepts = [c for c in concept_candidates if c not in json_keys and len(c) > 1]
                if concepts:
                    logging.info(f"Extracted concepts using Pattern 3 (quoted strings): {concepts}")
            
            # Pattern 4: Look for unquoted concept names in the response
            if not concepts:
                # Find Chinese characters that might be concept names
                chinese_concepts = re.findall(r'[\u4e00-\u9fff]{2,6}', cleaned)
                # Filter out common words and keep meaningful concepts
                common_words = {'概念', '主题', '包含', '相关', '应用', '原理', '特点', '方法', '工具', '技术'}
                concepts = [c for c in chinese_concepts if c not in common_words and len(c) >= 2]
                # Remove duplicates while preserving order
                seen = set()
                unique_concepts = []
                for c in concepts:
                    if c not in seen:
                        seen.add(c)
                        unique_concepts.append(c)
                concepts = unique_concepts[:6]  # Limit to 6 concepts
                if concepts:
                    logging.info(f"Extracted concepts using Pattern 4 (Chinese characters): {concepts}")
            
            # Return whatever we found, even if incomplete
            if concepts:
                logging.info(f"Extracted partial concepts from malformed JSON: {concepts}")
                return {"topic": topic, "concepts": concepts}
            else:
                # If we found absolutely nothing, just return the topic
                logging.warning(f"Could not extract any concepts from response, returning topic only: {topic}")
                return {"topic": topic, "concepts": []}

    def _clean_text(self, text: str, max_len: int) -> str:
        if not isinstance(text, str):
            return ""
        cleaned = " ".join(text.split())
        if len(cleaned) > max_len:
            cleaned = cleaned[: max_len - 1].rstrip() + "…"
        return cleaned

    def _generate_layout(self, topic: str, concepts: List[str], relationships: List[Dict[str, str]]) -> Dict:
        if not concepts:
            return {}

        # Undirected adjacency for degree and components
        adjacency: Dict[str, Set[str]] = {c: set() for c in concepts}
        for rel in relationships:
            frm = rel.get("from")
            to = rel.get("to")
            if frm in adjacency and to in adjacency:
                adjacency[frm].add(to)
                adjacency[to].add(frm)

        degree = {c: len(neigh) for c, neigh in adjacency.items()}
        ordered = sorted(concepts, key=lambda c: (-degree.get(c, 0), c))

        n = len(concepts)
        ring1_count = max(2, min(6, round(0.3 * n)))
        ring2_count = max(2, min(10, round(0.4 * n)))
        rings: Dict[str, int] = {}
        for i, c in enumerate(ordered):
            if i < ring1_count:
                rings[c] = 1
            elif i < ring1_count + ring2_count:
                rings[c] = 2
            else:
                rings[c] = 3

        # Connected components as clusters
        clusters: Dict[str, str] = {}
        visited: Set[str] = set()
        cluster_id = 0
        for c in concepts:
            if c in visited:
                continue
            stack = [c]
            visited.add(c)
            comp = []
            while stack:
                node = stack.pop()
                comp.append(node)
                for nb in adjacency.get(node, ()):  
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            cid = f"cluster_{cluster_id}"
            for node in comp:
                clusters[node] = cid
            cluster_id += 1

        # Angle hints by cluster sector
        cluster_to_nodes: Dict[str, List[str]] = {}
        for node, cid in clusters.items():
            cluster_to_nodes.setdefault(cid, []).append(node)
        total = float(sum(len(v) for v in cluster_to_nodes.values())) or 1.0
        angle_hints: Dict[str, float] = {}
        import math
        current_angle = -math.pi / 2
        two_pi = 2 * math.pi
        for cid, nodes_in_cluster in sorted(cluster_to_nodes.items()):
            span = two_pi * (len(nodes_in_cluster) / total)
            nodes_in_cluster.sort(key=lambda x: (-degree.get(x, 0), x))
            step = span / max(1, len(nodes_in_cluster))
            angle = current_angle
            for node in nodes_in_cluster:
                angle_hints[node] = angle
                angle += step
            current_angle += span

        # Even-spread positions and curvature hints
        positions, edge_curvatures = self._compute_positions_even_spread(
            concepts=concepts,
            angle_hints=angle_hints,
        )

        params = {"ringRadius": 220, "ringGap": 120, "angleOffset": 0.0, "nodeSpacing": 1.2}
        return {
            "rings": rings,
            "clusters": clusters,
            "angleHints": angle_hints,
            "positions": positions,
            "edgeCurvatures": edge_curvatures,
            "params": params,
        }

    def _generate_layout_sugiyama(self, topic: str, concepts: List[str], relationships: List[Dict[str, str]]) -> Dict:
        """Compute Sugiyama layered layout positions normalized to [-1,1].

        Steps:
        - Build undirected graph; BFS layers from topic -> layer indices
        - Break ties by degree centrality
        - Crossing minimization via barycenter ordering sweeps (few iterations)
        - Assign x positions per layer using approximate node widths
        - Normalize to [-1,1] coordinates
        """
        import math
        from collections import deque, defaultdict

        if not concepts:
            return {"algorithm": "sugiyama", "positions": {}}

        # Build undirected adjacency to determine layers
        nodes = [topic] + concepts
        node_set = set(nodes)
        adj = {n: set() for n in nodes}
        for rel in relationships:
            a = rel.get("from"); b = rel.get("to")
            if a in node_set and b in node_set:
                adj[a].add(b); adj[b].add(a)

        # BFS from topic to get layer indices
        layer = {n: math.inf for n in nodes}
        layer[topic] = 0
        q = deque([topic])
        while q:
            cur = q.popleft()
            for nb in adj[cur]:
                if layer[nb] is math.inf:
                    layer[nb] = layer[cur] + 1
                    q.append(nb)
        # For disconnected nodes, set to max layer + 1
        finite_layers = [v for v in layer.values() if v is not math.inf]
        max_layer = max(finite_layers) if finite_layers else 0
        for n in nodes:
            if layer[n] is math.inf:
                layer[n] = max_layer + 1
        max_layer = max(layer.values())

        # Degree centrality for ordering tie-breaks
        degree = {n: len(adj.get(n, ())) for n in nodes}

        # Group nodes by layer
        layers = defaultdict(list)
        for n in nodes:
            layers[layer[n]].append(n)

        # Initialize ordering within layers by degree (desc)
        for L in range(max_layer + 1):
            layers[L].sort(key=lambda n: (-degree.get(n, 0), n))

        # Build directed edges for barycenter (from lower to higher layer)
        dir_edges = []
        for rel in relationships:
            a = rel.get("from"); b = rel.get("to")
            if a not in node_set or b not in node_set: continue
            if layer[a] == layer[b]:
                # keep parallel layer links for crossing metric minimally; skip for direction
                continue
            if layer[a] < layer[b]:
                dir_edges.append((a, b))
            else:
                dir_edges.append((b, a))

        # Barycenter sweeps (down then up) to reduce crossings
        def barycenter_order(current_layer_nodes, neighbor_layer_nodes, edges_from_lower_to_upper, lower_to_upper=True):
            index_of = {n: i for i, n in enumerate(neighbor_layer_nodes)}
            bc = []
            for n in current_layer_nodes:
                neighbors = []
                if lower_to_upper:
                    neighbors = [v for u, v in edges_from_lower_to_upper if u == n]
                else:
                    neighbors = [u for u, v in edges_from_lower_to_upper if v == n]
                if neighbors:
                    bc_val = sum(index_of.get(nb, 0) for nb in neighbors) / len(neighbors)
                else:
                    bc_val = float('inf')
                bc.append((bc_val, -degree.get(n, 0), n))
            bc.sort()
            return [n for _, __, n in bc]

        sweeps = 4
        for _ in range(sweeps):
            # downward sweep
            for L in range(1, max_layer + 1):
                above = layers[L - 1]
                cur = layers[L]
                layers[L] = barycenter_order(cur, above, dir_edges, lower_to_upper=False)
            # upward sweep
            for L in range(max_layer - 1, -1, -1):
                below = layers[L + 1] if L + 1 <= max_layer else []
                cur = layers[L]
                layers[L] = barycenter_order(cur, below, dir_edges, lower_to_upper=True)

        # Approximate node widths by label length
        def approx_width(label: str, is_topic=False):
            base = 9.0  # px per char approx
            max_text = 220 if not is_topic else 260
            text_w = min(max_text, base * max(1, len(label)))
            padding = 32
            return text_w + padding

        # Assign x positions per layer with gaps
        layer_positions = {}
        max_span = 0.0
        for L in range(0, max_layer + 1):
            nodes_in_layer = layers[L]
            total_w = 0.0
            widths = []
            for n in nodes_in_layer:
                w = approx_width(n, is_topic=(n == topic))
                widths.append(w)
                total_w += w
            gap = 40.0
            span = total_w + gap * max(0, len(nodes_in_layer) - 1)
            max_span = max(max_span, span)
            # center at 0: start x = -span/2 + widths[0]/2
            x = -span / 2.0
            positions_in_layer = []
            for i, n in enumerate(nodes_in_layer):
                w = widths[i]
                cx = x + w / 2.0
                positions_in_layer.append((n, cx))
                x += w + gap
            layer_positions[L] = positions_in_layer

        # Normalize to [-1,1] with topic at y=0 and layers alternating above/below
        pos_norm = {}
        # Compute a per-layer normalized vertical offset so that layers spread around 0
        # Layer 0 (topic) -> y = 0
        # Layer 1 -> +d, Layer 2 -> -2d, Layer 3 -> +3d, etc.
        # Choose d so that the furthest layer stays within [-0.9, 0.9]
        d = 0.9 / max(1, max_layer)
        for L in range(0, max_layer + 1):
            if L == 0:
                y = 0.0
            else:
                sign = 1 if (L % 2 == 1) else -1
                y = sign * (L * d)
            for n, cx in layer_positions[L]:
                xn = 0.0 if max_span == 0 else (cx / (max_span / 2.0))
                # Clamp x within [-0.95, 0.95]
                xn = max(-0.95, min(0.95, xn))
                pos_norm[n] = {"x": xn, "y": max(-0.95, min(0.95, y))}

        # Slight curvature hints alternating by layer index order
        curv = {}
        for L in range(0, max_layer + 1):
            for idx, (n, _) in enumerate(layer_positions[L]):
                curv[n] = [0.0, 12.0, -12.0, 24.0, -24.0][idx % 5]

        return {
            "algorithm": "sugiyama",
            "layers": {str(L): layers[L] for L in range(0, max_layer + 1)},
            "positions": pos_norm,
            "edgeCurvatures": curv,
            "params": {"angleOffset": 0},
        }

    def _generate_layout_sectors(self, topic: str, concepts: List[str], relationships: List[Dict[str, str]]) -> Dict:
        """Divide canvas into sectors by key concepts and place sub-concepts within their sector.

        - Keys: direct neighbors of topic (by any direction). If none, pick top-K by degree.
        - Assign remaining concepts to their closest key by connectivity; else distribute round-robin.
        - Positions are normalized to [-1,1]. Topic at (0,0). Keys on inner ring; parts spread within sector.
        """
        import math
        from collections import defaultdict

        if not concepts:
            return {"algorithm": "sectors", "positions": {}}

        nodes = [topic] + concepts
        node_set = set(nodes)
        # Build undirected adjacency
        adj = {n: set() for n in nodes}
        for rel in relationships:
            a = rel.get("from"); b = rel.get("to")
            if a in node_set and b in node_set:
                adj[a].add(b); adj[b].add(a)

        # Identify keys as direct neighbors of topic
        keys = list(adj.get(topic, []))
        # Degree centrality
        degree = {n: len(adj.get(n, ())) for n in nodes}
        if not keys:
            # Pick top 4-6 by degree (excluding topic)
            candidates = sorted(concepts, key=lambda n: (-degree.get(n, 0), n))
            keys = candidates[: max(4, min(6, len(candidates)))]
        else:
            # Limit keys to 4-8 for readability
            keys = sorted(keys, key=lambda n: (-degree.get(n, 0), n))[: max(4, min(8, len(keys)))]

        # Assign parts to keys
        remaining = [c for c in concepts if c not in keys]
        key_parts: Dict[str, List[str]] = {k: [] for k in keys}
        for c in remaining:
            # choose key with edge to c; fallback to key with highest degree or round robin
            linked_keys = [k for k in keys if c in adj.get(k, set())]
            if linked_keys:
                # pick the strongest (by key degree)
                ksel = sorted(linked_keys, key=lambda n: (-degree.get(n, 0), n))[0]
            else:
                # fallback: highest-degree key
                ksel = sorted(keys, key=lambda n: (-degree.get(n, 0), n))[0]
            key_parts[ksel].append(c)

        # Compute positions with natural canvas spread like the endocrine system diagram
        positions = {topic: {"x": 0.0, "y": 0.0}}
        S = max(1, len(keys))
        
        # Create a more natural distribution across the full canvas
        import random
        random.seed(42)  # Consistent positioning
        
        # Position keys in a more distributed pattern across canvas
        if S <= 4:
            # For few keys, spread them in quadrants but not at corners
            key_positions = [
                (0.6, 0.4),    # Upper right area
                (-0.5, 0.5),   # Upper left area  
                (-0.6, -0.4),  # Lower left area
                (0.5, -0.5)    # Lower right area
            ]
        elif S <= 6:
            # For more keys, use a hexagonal-like distribution
            key_positions = [
                (0.7, 0.2),    # Right
                (0.35, 0.6),   # Upper right
                (-0.35, 0.6),  # Upper left
                (-0.7, 0.2),   # Left
                (-0.35, -0.6), # Lower left
                (0.35, -0.6)   # Lower right
            ]
        else:
            # For many keys, use a more distributed circular pattern
            key_positions = []
            for i in range(S):
                angle = (i * 2 * math.pi / S) - math.pi / 2
                # Vary the radius for more natural spread
                radius = 0.5 + 0.2 * math.sin(i * 1.3)  # Varies between 0.3 and 0.7
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                key_positions.append((x, y))
        
        # Position the keys
        for i, k in enumerate(keys):
            if i < len(key_positions):
                kx, ky = key_positions[i]
            else:
                # Fallback for extra keys
                angle = (i * 2 * math.pi / S) - math.pi / 2
                kx = 0.6 * math.cos(angle)
                ky = 0.6 * math.sin(angle)
            
            positions[k] = {"x": kx, "y": ky}
            
        # Position parts in natural clusters around their keys, spread across canvas
        for i, k in enumerate(keys):
            parts = key_parts[k]
            if not parts:
                continue
            
            kx, ky = positions[k]["x"], positions[k]["y"]
            
            # Create natural clusters around each key, not radial sectors
            for idx, p in enumerate(parts):
                # Use multiple placement strategies for natural spread
                if len(parts) <= 3:
                    # Small clusters: tight around key
                    base_distance = 0.15 + 0.1 * idx
                    angle_range = math.pi  # 180 degrees
                else:
                    # Larger clusters: spread further
                    base_distance = 0.2 + 0.15 * (idx // 4)
                    angle_range = 1.5 * math.pi  # 270 degrees
                
                # Random angle within the range, biased away from center
                angle_offset = (idx * 1.618 * math.pi) % angle_range - angle_range/2  # Golden ratio for natural distribution
                angle = math.atan2(ky, kx) + angle_offset
                
                # Variable distance for organic look
                distance = base_distance + random.uniform(-0.05, 0.1)
                
                # Calculate position
                px = kx + distance * math.cos(angle)
                py = ky + distance * math.sin(angle)
                
                # Add natural jitter for organic positioning
                jitter = 0.08
                px += random.uniform(-jitter, jitter)
                py += random.uniform(-jitter, jitter)
                
                # Ensure we use the full canvas space, not just the center
                # Expand positions to fill more of the canvas like the endocrine diagram
                expansion_factor = 1.2
                px *= expansion_factor
                py *= expansion_factor
                
                # Clamp to reasonable bounds (allow closer to edges)
                px = max(-0.9, min(0.9, px))
                py = max(-0.9, min(0.9, py))
                
                positions[p] = {"x": px, "y": py}

        # Curvature hints per node by sector index
        curv = {}
        for i, k in enumerate(keys):
            curv[k] = [0.0, 12.0, -12.0][i % 3]
            for j, p in enumerate(key_parts[k]):
                curv[p] = [0.0, 12.0, -12.0, 24.0, -24.0][j % 5]

        return {
            "algorithm": "sectors",
            "keys": keys,
            "key_parts": key_parts,
            "positions": positions,
            "edgeCurvatures": curv,
            "params": {
                "nodeSpacing": 2.0,  # increased multiplier for better node spacing
                "gapFactor": 0.7,    # reduced sector usage for more spread
                "innerRadius": 0.5,  # increased key concept radius
                "minRadius": 0.7,    # increased minimum part radius
                "maxRadius": 0.95    # maximum part radius
            },
        }

    def _generate_layout_sectors_from_keys_parts(self, topic: str, spec: Dict) -> Dict:
        """Sector layout when 'keys' (and optional per-key 'parts') exist in spec."""
        import math
        keys = [k.get('name') if isinstance(k, dict) else str(k) for k in (spec.get('keys') or [])]
        keys = [k for k in keys if isinstance(k, str) and k.strip()]
        if not keys:
            return self._generate_layout_sectors(topic, spec.get('concepts') or [], spec.get('relationships') or [])
        # Gather parts mapping
        key_parts = {}
        parts_map = spec.get('key_parts') or {}
        for k in keys:
            plist = parts_map.get(k) or []
            # Normalize list of part dicts or names
            out = []
            for p in plist:
                name = p.get('name') if isinstance(p, dict) else str(p)
                if isinstance(name, str) and name.strip():
                    out.append(name)
            key_parts[k] = out
        # Adaptive positioning based on content and canvas
        positions = {topic: {"x": 0.0, "y": 0.0}}
        S = max(1, len(keys))
        sector_span = 2 * math.pi / S
        
        # Calculate adaptive parameters based on content
        total_concepts = sum(len(parts) for parts in key_parts.values())
        max_concepts_per_group = max(len(parts) for parts in key_parts.values()) if key_parts else 1
        
        # Adaptive inner radius - smaller for more groups
        inner_r = max(0.2, min(0.5, 0.8 / S))
        
        # Adaptive canvas utilization - use more space for dense content
        canvas_utilization = min(0.95, 0.7 + (total_concepts / 60))  # Scale with concept count
        
        # Adaptive radial spacing - ensure concepts don't overlap
        radial_layers = max(3, math.ceil(max_concepts_per_group / 4))  # Distribute across layers
        radial_spacing = (canvas_utilization - inner_r - 0.1) / radial_layers
        min_r = inner_r + radial_spacing
        max_r = canvas_utilization
        
        # Adaptive gap factor - reduce overlap for dense sectors
        gap_factor = max(0.6, min(0.9, 1.0 - (max_concepts_per_group - 3) * 0.05))
        for i, k in enumerate(keys):
            # Distribute evenly 360° around central topic (0° = right, 90° = top, 180° = left, 270° = bottom)
            center_ang = i * sector_span
            kx = inner_r * math.cos(center_ang)
            ky = inner_r * math.sin(center_ang)
            positions[k] = {"x": kx, "y": ky}
            parts = key_parts.get(k, [])
            n_parts = len(parts)
            if n_parts == 0:
                continue
                
            # Adaptive angular and radial distribution
            for idx, p in enumerate(parts):
                # Angular distribution within sector
                if n_parts == 1:
                    ang = center_ang  # Single concept at center of sector
                else:
                    # Distribute evenly across available angular space
                    half_span = (sector_span * gap_factor) / 2
                    start_ang = center_ang - half_span
                    end_ang = center_ang + half_span
                    t = idx / (n_parts - 1)  # Even distribution
                    ang = start_ang + t * (end_ang - start_ang)
                
                # Adaptive radial distribution - spread across multiple layers
                layer = idx % radial_layers
                layer_progress = idx // radial_layers
                base_radius = min_r + layer * radial_spacing
                
                # Add slight radial variation to avoid perfect alignment
                radial_offset = (layer_progress * 0.05) if layer_progress > 0 else 0
                rad = min(max_r, base_radius + radial_offset)
                
                # Calculate final position
                px = rad * math.cos(ang)
                py = rad * math.sin(ang)
                
                # Use adaptive bounds instead of hardcoded clamping
                bound = canvas_utilization * 1.05  # Allow slight overflow for natural appearance
                px = max(-bound, min(bound, px))
                py = max(-bound, min(bound, py))
                
                positions[p] = {"x": px, "y": py}
        # Curvature hints
        curv = {}
        for i, k in enumerate(keys):
            curv[k] = [0.0, 12.0, -12.0][i % 3]
            for j, p in enumerate(key_parts.get(k, [])):
                curv[p] = [0.0, 12.0, -12.0, 24.0, -24.0][j % 5]
        return {
            "algorithm": "sectors",
            "keys": keys,
            "key_parts": key_parts,
            "positions": positions,
            "edgeCurvatures": curv,
            "params": {
                "nodeSpacing": 1.2,  # multiplier for node spacing (higher = more spread)
                "gapFactor": 0.9,    # sector usage factor
                "innerRadius": 0.25, # key concept radius
                "minRadius": 0.45,   # minimum part radius
                "maxRadius": 0.95    # maximum part radius
            },
        }

    def _create_grouped_spec_for_enhanced_30(self, spec: Dict, topic: str, concepts: List[str]) -> Dict:
        """Create a grouped spec using intelligent LLM-based categorization."""
        import json
        import re
        
        # If there are no concepts, return basic spec
        if not concepts:
            return spec
        
        # Use LLM to intelligently categorize the concepts
        try:
            categorization = self._categorize_concepts_with_llm(topic, concepts)
            if categorization and 'categories' in categorization:
                keys = list(categorization['categories'].keys())
                key_parts = categorization['categories']
                
                # Ensure all concepts are assigned
                assigned_concepts = set()
                for concept_list in key_parts.values():
                    assigned_concepts.update(concept_list)
                
                # Add any missing concepts to the first category
                missing_concepts = [c for c in concepts if c not in assigned_concepts]
                if missing_concepts and keys:
                    key_parts[keys[0]].extend(missing_concepts)
                
                # Create the grouped spec
                grouped_spec = spec.copy()
                grouped_spec['keys'] = keys
                grouped_spec['key_parts'] = key_parts
                grouped_spec['concepts'] = concepts
                grouped_spec['relationships'] = spec.get('relationships', [])
                
                return grouped_spec
            
        except Exception as e:
            print(f"LLM categorization failed: {e}, falling back to mechanical grouping")
        
        # Fallback to mechanical grouping if LLM fails
        return self._create_mechanical_grouped_spec(spec, topic, concepts)
    
    def _categorize_concepts_with_llm(self, topic: str, concepts: List[str]) -> Dict:
        """Use LLM to intelligently categorize concepts into natural groups."""
        import json
        import re
        
        categorization_prompt = f"""
你是一个领域专家，请分析主题"{topic}"的30个概念，将它们分类到自然的主题组中。

概念列表：
{', '.join(concepts)}

请分析这些概念，识别它们的自然分类模式，然后将它们组织成逻辑相关的组。

要求：
1. 创建3-6个有意义的类别（基于概念的自然关联性）
2. 每个类别应该有清晰的主题焦点
3. 类别名称应该简洁且描述性强
4. 确保所有30个概念都被分配到类别中
5. 优先使用领域特定的分类而不是通用分类

请严格按照以下JSON格式输出：
{{
  "categories": {{
    "类别名称1": ["概念1", "概念2", "概念3"],
    "类别名称2": ["概念4", "概念5", "概念6"],
    "类别名称3": ["概念7", "概念8", "概念9"]
  }}
}}

只输出JSON，不要其他解释。
"""
        
        try:
            # Use logging to show categorization attempt
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Categorizing concepts for topic: {topic}")
            
            # Import the LLM client from agent module  
            from agent import QwenLLM
            llm = QwenLLM()
            
            response = llm._call(categorization_prompt)
            if not response:
                return None
            
            # Clean and parse JSON response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```'):
                response = re.sub(r'^```(?:json)?\s*\n', '', response, flags=re.MULTILINE)
                response = re.sub(r'\n```\s*$', '', response, flags=re.MULTILINE)
            
            # Try to parse JSON
            try:
                categorization = json.loads(response)
                return categorization
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    categorization = json.loads(json_match.group())
                    return categorization
                return None
                
        except Exception as e:
            print(f"LLM categorization error: {e}")
            return None
    
    def _create_mechanical_grouped_spec(self, spec: Dict, topic: str, concepts: List[str]) -> Dict:
        """Fallback mechanical grouping when LLM categorization fails."""
        import math
        
        n_concepts = len(concepts)
        n_groups = min(6, max(4, n_concepts // 6))  # 4-6 groups for optimal visual organization
        concepts_per_group = math.ceil(n_concepts / n_groups)
        
        # Create thematic group names based on common concept map categories
        group_names = [
            "核心概念",      # Core Concepts
            "技术方法",      # Technical Methods  
            "应用领域",      # Application Areas
            "系统组件",      # System Components
            "评估工具",      # Evaluation Tools
            "扩展概念"       # Extended Concepts
        ]
        
        keys = group_names[:n_groups]
        
        # Automatically distribute concepts into groups
        key_parts = {}
        for i, key in enumerate(keys):
            start_idx = i * concepts_per_group
            end_idx = min(start_idx + concepts_per_group, n_concepts)
            key_parts[key] = concepts[start_idx:end_idx]
        
        # Create the grouped spec
        grouped_spec = spec.copy()
        grouped_spec['keys'] = keys
        grouped_spec['key_parts'] = key_parts
        grouped_spec['concepts'] = concepts
        grouped_spec['relationships'] = spec.get('relationships', [])
        
        return grouped_spec

    def _generate_layout_radial(self, topic: str, concepts: List[str], relationships: List[Dict[str, str]]) -> Dict:
        """Generate radial/circular layout with concentric circles around central topic."""
        import math
        import random
        from collections import defaultdict, deque
        
        if not concepts:
            return {"algorithm": "radial", "positions": {topic: {"x": 0.0, "y": 0.0}}}
        
        # Central topic at origin
        positions = {topic: {"x": 0.0, "y": 0.0}}
        
        # Build relationship graph to determine distance from center
        graph = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from")
            to_node = rel.get("to")
            if from_node and to_node:
                graph[from_node].add(to_node)
                graph[to_node].add(from_node)
        
        # Intelligently assign concepts to concentric circles
        concept_layers = {}
        
        # First, try BFS from central topic for direct relationships
        visited = {topic}
        queue = deque([(topic, 0)])
        
        while queue:
            current_node, layer = queue.popleft()
            
            for neighbor in graph[current_node]:
                if neighbor not in visited and neighbor in concepts:
                    visited.add(neighbor)
                    concept_layers[neighbor] = layer + 1
                    queue.append((neighbor, layer + 1))
        
        # For better visual distribution, create multiple concentric circles
        unassigned = [c for c in concepts if c not in concept_layers]
        total_concepts = len(concepts)
        
        if total_concepts <= 10:
            # Small concept maps: 1-2 circles
            target_circles = 2
        elif total_concepts <= 20:
            # Medium concept maps: 2-3 circles  
            target_circles = 3
        else:
            # Large concept maps: 3-4 circles
            target_circles = 4
        
        # Distribute all concepts across target number of circles
        all_concepts = list(concepts)
        concepts_per_circle = total_concepts // target_circles
        
        # Clear and redistribute for better visual appearance
        concept_layers = {}
        
        for i, concept in enumerate(all_concepts):
            # Distribute evenly across circles, with inner circles having fewer nodes
            if i < concepts_per_circle * 0.7:  # Inner circle (smaller)
                layer = 1
            elif i < concepts_per_circle * 1.8:  # Middle circle
                layer = 2
            elif i < concepts_per_circle * 3.0:  # Outer circle
                layer = 3
            else:  # Outermost circle
                layer = min(4, target_circles)
            
            concept_layers[concept] = layer
        
        # Group concepts by layer
        layers = defaultdict(list)
        for concept, layer in concept_layers.items():
            layers[layer].append(concept)
        
        # Calculate adaptive radii for concentric circles with maximum spacing
        max_layer = max(layers.keys()) if layers else 1
        base_radius = 1.8  # Start radius for first circle (even larger from 1.2)
        radius_increment = min(1.2, 3.5 / max_layer)  # Maximum spacing (even larger from 0.8 and 2.5)
        
        # Position concepts in each concentric circle
        for layer_num, layer_concepts in layers.items():
            n_concepts = len(layer_concepts)
            if n_concepts == 0:
                continue
            
            # Calculate radius for this layer
            radius = base_radius + (layer_num - 1) * radius_increment
            radius = min(radius, 5.0)  # Allow maximum expansion for ultimate spacing (increased from 3.5)
            
            # Distribute concepts evenly around the circle
            for i, concept in enumerate(layer_concepts):
                # Calculate angle for even distribution
                angle = (2 * math.pi * i) / n_concepts
                
                # Add slight randomization to avoid perfect alignment
                angle_offset = random.uniform(-0.1, 0.1) if n_concepts > 1 else 0
                final_angle = angle + angle_offset
                
                # Calculate position
                x = radius * math.cos(final_angle)
                y = radius * math.sin(final_angle)
                
                positions[concept] = {"x": x, "y": y}
        
        # Generate edge curvatures for radial connections
        edge_curvatures = {}
        for i, concept in enumerate(concepts):
            # Vary curvature to reduce overlapping edges
            edge_curvatures[concept] = [0.0, 8.0, -8.0, 16.0, -16.0][i % 5]
        
        return {
            "algorithm": "radial",
            "positions": positions,
            "edgeCurvatures": edge_curvatures,
            "layers": dict(layers),  # For debugging/analysis
            "params": {
                "nodeSpacing": 1.0,
                "baseRadius": base_radius,
                "radiusIncrement": radius_increment,
                "maxLayers": max_layer,
                "canvasBounds": 0.95
            }
        }

    def _compute_positions_even_spread(
        self,
        concepts: List[str],
        angle_hints: Dict[str, float] | None = None,
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
        import math
        import random

        if angle_hints is None:
            angle_hints = {}

        n = max(1, len(concepts))
        side = 2.0
        margin = 0.05  # reduce margin to spread nodes more
        cols = int(math.ceil(math.sqrt(n)))
        rows = int(math.ceil(n / cols))

        ordered = sorted(concepts, key=lambda c: angle_hints.get(c, 0.0))
        pos: Dict[str, Tuple[float, float]] = {}
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= n:
                    break
                label = ordered[idx]
                x = -1.0 + (c + 0.5) * (side / cols)
                y = -1.0 + (r + 0.5) * (side / rows)
                jitter = 0.15 * (side / max(cols, rows))
                x += random.uniform(-jitter, jitter)
                y += random.uniform(-jitter, jitter)
                x = max(-1 + margin, min(1 - margin, x))
                y = max(-1 + margin, min(1 - margin, y))
                pos[label] = (x, y)
                idx += 1

        # Lightweight repulsion + radial spring
        target_r = 0.85  # increase target radius for better spread
        rep = 0.035      # increase repulsion force
        spring = 0.025   # reduce spring force to allow more spread
        step = 0.18      # increase step size for faster convergence
        iters = 250      # more iterations for better positioning
        labels = concepts
        for _ in range(iters):
            for i in range(n):
                xi, yi = pos[labels[i]]
                fx = fy = 0.0
                for j in range(n):
                    if i == j:
                        continue
                    xj, yj = pos[labels[j]]
                    dx = xi - xj
                    dy = yi - yj
                    d2 = dx * dx + dy * dy + 1e-6
                    f = rep / d2
                    fx += dx * f
                    fy += dy * f
                r = math.hypot(xi, yi) + 1e-6
                if r > 0:
                    dxn = xi / r
                    dyn = yi / r
                else:
                    ang = angle_hints.get(labels[i], -math.pi / 2)
                    dxn = math.cos(ang)
                    dyn = math.sin(ang)
                fr = spring * (target_r - r)
                fx += dxn * fr
                fy += dyn * fr
                xi += step * fx
                yi += step * fy
                xi = max(-1 + margin, min(1 - margin, xi))
                yi = max(-1 + margin, min(1 - margin, yi))
                pos[labels[i]] = (xi, yi)

        # Curvature hints per node by angle order
        ang_list = sorted(((math.atan2(y, x), label) for label, (x, y) in pos.items()))
        offsets = [0.0, 12.0, -12.0, 24.0, -24.0, 36.0, -36.0]
        curv: Dict[str, float] = {}
        for k, (_, label) in enumerate(ang_list):
            curv[label] = offsets[k % len(offsets)]

        return (
            {label: {"x": pos[label][0], "y": pos[label][1]} for label in concepts},
            curv,
        )

    def _compute_recommended_dimensions_from_layout(
        self,
        layout: Dict,
        topic: str,
        concepts: List[str],
    ) -> Dict[str, int]:
        """Calculate canvas size based on actual SVG element dimensions like D3.js does.

        This simulates the D3.js drawBox() function to predict real space requirements.
        """
        positions = layout.get("positions") or {}
        if not positions:
            # Minimal fallback sizing for empty layouts
            return {"baseWidth": 800, "baseHeight": 600, "width": 800, "height": 600, "padding": 100}

        # Simulate D3.js text measurement and box sizing
        def estimate_text_box(text: str, is_topic: bool = False) -> tuple:
            """Estimate text box dimensions like D3.js drawBox() function."""
            font_size = 26 if is_topic else 22  # Even larger font sizes for maximum readability (was 22/18)
            max_text_width = 350 if is_topic else 300  # Even larger max width for bigger text (was 300/260)
            
            # Estimate character width (approximate for common fonts)
            char_width = font_size * 0.6  # Rough estimate for common fonts
            text_width = len(text) * char_width
            
            # Handle text wrapping
            if text_width > max_text_width:
                lines = max(1, int(text_width / max_text_width) + 1)
                actual_text_width = min(text_width, max_text_width)
            else:
                lines = 1
                actual_text_width = text_width
                
            # Add padding like D3.js drawBox()
            padding_x = 16
            padding_y = 10
            line_height = int(font_size * 1.2)
            
            box_w = int(actual_text_width + padding_x * 2)
            box_h = int(lines * line_height + padding_y * 2)
            
            return box_w, box_h
        
        # Calculate actual node dimensions
        topic_w, topic_h = estimate_text_box(topic, True)
        
        concept_boxes = []
        for concept in concepts:
            w, h = estimate_text_box(concept, False)
            concept_boxes.append((w, h))
        
        # Find the coordinate bounds
        xs = [positions[c]["x"] for c in positions if "x" in positions[c]]
        ys = [positions[c]["y"] for c in positions if "y" in positions[c]]
        if not xs or not ys:
            return {"baseWidth": 800, "baseHeight": 600, "width": 800, "height": 600, "padding": 100}

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        
        # Calculate the scale factor D3.js uses: scaleX = (width - 2*padding) / 6
        # We need to reverse this: width = spanx * pixels_per_unit + 2*padding + node_sizes
        
        # Coordinate span in the normalized space
        coord_span_x = max(0.4, xmax - xmin)
        coord_span_y = max(0.4, ymax - ymin)
        
        # We want the diagram to be readable, so use a scale that accommodates larger text and more spacing
        # Increased scale to handle larger text and maximum node spacing
        target_scale = 180  # Optimized for larger text and maximum spacing (reduced from 200 to balance size)  
        
        # Calculate content area needed for positions
        content_area_x = coord_span_x * target_scale
        content_area_y = coord_span_y * target_scale
        
        # Add space for the largest nodes (half extends on each side)
        max_concept_w = max([w for w, h in concept_boxes], default=100)
        max_concept_h = max([h for w, h in concept_boxes], default=40)
        
        node_margin_x = max(topic_w, max_concept_w) // 2
        node_margin_y = max(topic_h, max_concept_h) // 2
        
        # Calculate total required space
        base_padding = 80  # Reasonable padding
        total_width = content_area_x + (2 * node_margin_x) + (2 * base_padding)
        total_height = content_area_y + (2 * node_margin_y) + (2 * base_padding)
        
        # Apply reasonable bounds
        num_concepts = len(concepts)
        min_width = max(600, 400 + num_concepts * 10)   # Increased for larger text and spacing
        min_height = max(500, 350 + num_concepts * 8)
        max_width = 1400   # Increased maximum to accommodate larger text and spacing (was 1200)
        max_height = 1200  # Increased maximum to accommodate larger text and spacing (was 1000)
        
        width_px = int(max(min_width, min(max_width, total_width)))
        height_px = int(max(min_height, min(max_height, total_height)))

        return {
            "baseWidth": width_px, 
            "baseHeight": height_px, 
            "width": width_px, 
            "height": height_px, 
            "padding": base_padding
        }


__all__ = ["ConceptMapAgent"]


