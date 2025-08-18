"""
LangChain Agent Module for MindGraph

This module contains the core LangChain agent functionality for generating
custom graph content using the Qwen LLM. It supports both double bubble maps
(comparison of two topics) and bubble maps (single topic with characteristics).
The agent uses LLM-based prompt analysis to classify the user's intent and
generates the appropriate JSON spec and D3.js code block for the selected
graph type.
"""

import os
import logging
import re
import time
from dotenv import load_dotenv
load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import requests
import yaml
from config import config
from agent_utils import (
    extract_topics_with_agent,
    generate_characteristics_with_agent,
    parse_characteristics_result,
    detect_language
)
# Modular agent for D3.js graph generation
# Provides LLM-based graph type detection and JSON spec generation for D3.js rendering
from graph_specs import (
    validate_double_bubble_map,
    validate_bubble_map,
    validate_circle_map,
    validate_tree_map,
    validate_concept_map,
    validate_mindmap
)
import json
from diagram_styles import parse_style_from_prompt
import re
from prompts import get_prompt

def _salvage_json_string(raw: str) -> str:
    """Attempt to salvage a JSON object from messy LLM output."""
    if not raw:
        return ""
    s = raw.strip().strip('`')
    # Remove code fences if present
    if s.startswith('```'):
        fence_end = s.rfind('```')
        if fence_end > 3:
            s = s[3:fence_end]
    # Find first '{' and balance braces outside strings
    start = s.find('{')
    if start == -1:
        return ""
    buf = []
    depth = 0
    in_str = False
    esc = False
    for ch in s[start:]:
        buf.append(ch)
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
    candidate = ''.join(buf)
    while depth > 0:
        candidate += '}'
        depth -= 1
    # Remove trailing commas before } or ]
    candidate = re.sub(r',\s*(\]|\})', r'\1', candidate)
    return candidate.strip()

# Global timing tracking
llm_timing_stats = {
    'total_calls': 0,
    'total_time': 0.0,
    'call_times': [],
    'last_call_time': 0.0
}

def get_llm_timing_stats():
    """Get current LLM timing statistics."""
    if llm_timing_stats['total_calls'] > 0:
        avg_time = llm_timing_stats['total_time'] / llm_timing_stats['total_calls']
    else:
        avg_time = 0.0
    
    return {
        'total_calls': llm_timing_stats['total_calls'],
        'total_time': llm_timing_stats['total_time'],
        'average_time': avg_time,
        'last_call_time': llm_timing_stats['last_call_time'],
        'call_times': llm_timing_stats['call_times'][-10:]  # Last 10 calls
    }


# ----------------------------------------------------------------------------
# Explicit intent detection helpers (language-aware keyword mapping)
# ----------------------------------------------------------------------------
# Removed helper functions - no longer needed with clean LLM-only classification

# Removed detect_explicit_diagram_intent - redundant with LLM classification


class QwenLLM(LLM):
    """
    Custom LangChain LLM wrapper for Qwen API with timing tracking
    """
    def _call(self, prompt, stop=None):
        start_time = time.time()
        logger.info(f"QwenLLM._call() - Model: {config.QWEN_MODEL}")
        logger.debug(f"Prompt sent to Qwen:\n{prompt[:1000]}{'...' if len(prompt) > 1000 else ''}")

        headers = config.get_qwen_headers()
        data = config.get_qwen_data(prompt)

        logger.info(f"Making request to: {config.QWEN_API_URL}")
        try:
            resp = requests.post(
                config.QWEN_API_URL,
                headers=headers,
                json=data
            )
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            
            # Calculate timing
            call_time = time.time() - start_time
            llm_timing_stats['total_calls'] += 1
            llm_timing_stats['total_time'] += call_time
            llm_timing_stats['last_call_time'] = call_time
            llm_timing_stats['call_times'].append(call_time)
            
            # Keep only last 100 call times to prevent memory bloat
            if len(llm_timing_stats['call_times']) > 100:
                llm_timing_stats['call_times'] = llm_timing_stats['call_times'][-100:]
            
            logger.info(f"QwenLLM response received - Length: {len(content)} characters - Time: {call_time:.3f}s")
            logger.debug(f"Qwen Output:\n{content[:1000]}{'...' if len(content) > 1000 else ''}")
            return content
        except Exception as e:
            # Still track timing even on error
            call_time = time.time() - start_time
            llm_timing_stats['total_calls'] += 1
            llm_timing_stats['total_time'] += call_time
            llm_timing_stats['last_call_time'] = call_time
            llm_timing_stats['call_times'].append(call_time)
            
            logger.error(f"QwenLLM API call failed: {e} - Time: {call_time:.3f}s", exc_info=True)
            raise

    @property
    def _llm_type(self):
        return "qwen"


# Initialize the LLM instance
llm = QwenLLM()


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

# Topic Extraction Prompts
topic_extraction_prompt_en = PromptTemplate(
    input_variables=["user_prompt"],
    template="""
TASK: Extract exactly two topics from the user's request.

User request: {user_prompt}

RULES:
1. Find exactly TWO nouns/concepts that can be compared
2. Ignore words like "compare", "generate", "create", "show", "about", "between"
3. Output ONLY: "topic1 and topic2"
4. NO code blocks, NO explanations, NO additional text

Examples:
Input: "Compare cats and dogs" → Output: "cats and dogs"
Input: "Generate diagram about BMW vs Mercedes" → Output: "BMW and Mercedes"
Input: "Create comparison between apple and orange" → Output: "apple and orange"

Your output (only the two topics):
"""
)

topic_extraction_prompt_zh = PromptTemplate(
    input_variables=["user_prompt"],
    template="""
任务：从用户请求中提取恰好两个主题。

用户请求: {user_prompt}

规则：
1. 找到恰好两个可以比较的名词/概念
2. 忽略"比较"、"生成"、"创建"、"显示"、"关于"、"之间"等词
3. 只输出："主题1和主题2"
4. 不要代码块，不要解释，不要额外文字

示例：
输入："比较猫和狗" → 输出："猫和狗"
输入："生成关于宝马和奔驰的图表" → 输出："宝马和奔驰"
输入："创建苹果和橙子的比较" → 输出："苹果和橙子"

你的输出（只输出两个主题）：
"""
)

# Characteristics Generation Prompts
characteristics_prompt_en = PromptTemplate(
    input_variables=["topic1", "topic2"],
    template="""
Compare {topic1} and {topic2} with concise keywords for similarities and differences.

Goal: Cultivate students' comparative thinking skills, enabling multi-dimensional analysis of shared traits and unique features.

Requirements:
- 5 common characteristics (shared by both) - use 2-4 words maximum
- 5 unique characteristics for {topic1} - use 2-4 words maximum  
- 5 unique characteristics for {topic2} - use 2-4 words maximum
- CRITICAL: ensure comparability – each difference must represent the same type of attribute directly comparable between {topic1} and {topic2}
- Use single words or very short phrases
- Cover diverse dimensions without repetition
- Focus on core, essential distinctions
- Highly abstract and condensed

Style Guidelines:
- Differences must be parallel: trait 1 for {topic1} matches trait 1 for {topic2}, etc.
- Maximum 4 words per characteristic
- Use nouns, adjectives, or short noun phrases
- Avoid verbs and complex descriptions
- Focus on fundamental, universal traits
- Be concise and memorable


Comparable Categories Examples:
- Geographic: location, terrain, climate
- Economic: industry, economy type, development level
- Cultural: lifestyle, traditions, values
- Physical: size, population, resources
- Temporal: history, age, development stage

Output ONLY the YAML content, no code block markers, no explanations:

similarities:
  - "trait1"
  - "trait2"
  - "trait3"
  - "trait4"
  - "trait5"
left_differences:
  - "feature1"
  - "feature2"
  - "feature3"
  - "feature4"
  - "feature5"
right_differences:
  - "feature1"
  - "feature2"
  - "feature3"
  - "feature4"
  - "feature5"
"""
)

characteristics_prompt_zh = PromptTemplate(
    input_variables=["topic1", "topic2"],
    template="""
对比{topic1}和{topic2}，并用简洁的关键词来概括相同点和不同点。

目的：培养学生的对比思维技能，能够从多个维度分析两个事物的共性与特性。

要求：
- 5个共同特征(两者共有)
- 5个{topic1}的独有特征 
- 5个{topic2}的独有特征
- 关键：使差异具有可比性 - 每个差异应代表可以在{topic1}和{topic2}之间直接比较的相同类型的特征/属性
- 使用关键词或极短短语，高度概括和抽象，保持简洁性
- 对比的维度要丰富，不要重复
- 专注于核心、本质差异

风格指导：
- 不同点要一一对应，确保差异遵循平行类别，如{topic1}的特征1要与{topic2}的特征1相对应，以此类推。
- 避免复杂描述
- 简洁且易记

可比类别示例：
- 地理：位置、地形、气候
- 经济：产业、经济类型、发展水平
- 文化：生活方式、传统、价值观
- 物理：规模、人口、资源
- 时间：历史、年龄、发展阶段

只输出YAML内容，不要代码块标记，不要解释：

similarities:
  - "特征1"
  - "特征2"
  - "特征3"
  - "特征4"
  - "特征5"
left_differences:
  - "特点1"
  - "特点2"
  - "特点3"
  - "特点4"
  - "特点5"
right_differences:
  - "特点1"
  - "特点2"
  - "特点3"
  - "特点4"
  - "特点5"
"""
)


# ============================================================================
# LANGCHAIN CHAINS
# ============================================================================

def create_topic_extraction_chain(language='zh'):
    """
    Create a LangChain RunnableSequence for topic extraction
    Args:
        language (str): Language for the prompt ('zh' or 'en')
    Returns:
        RunnableSequence: Configured sequence for topic extraction
    """
    prompt = topic_extraction_prompt_zh if language == 'zh' else topic_extraction_prompt_en
    # Return a RunnableSequence (prompt | llm)
    return prompt | llm


def create_characteristics_chain(language='zh'):
    """
    Create a LangChain RunnableSequence for characteristics generation
    Args:
        language (str): Language for the prompt ('zh' or 'en')
    Returns:
        RunnableSequence: Configured sequence for characteristics generation
    """
    prompt = characteristics_prompt_zh if language == 'zh' else characteristics_prompt_en
    # Return a RunnableSequence (prompt | llm)
    return prompt | llm


# ============================================================================
# AGENT WORKFLOW FUNCTIONS
# ============================================================================

def extract_yaml_from_code_block(text):
    """Extract content from fenced code blocks, robust to minor formatting.

    - Handles ```json, ```yaml, ```yml, ```js, or bare ```
    - Closing fence may or may not be preceded by a newline
    - If multiple blocks exist, returns the first
    - If no fences are found, returns stripped text
    """
    s = (text or "").strip()
    # Regex-based extraction first
    match = re.search(r"```(?:json|yaml|yml|javascript|js)?\s*\r?\n([\s\S]*?)\r?\n?```", s, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: manual slicing if starts with a fence but regex failed
    if s.startswith("```"):
        # Drop first line (```lang)
        first_nl = s.find("\n")
        content = s[first_nl + 1:] if first_nl != -1 else s[3:]
        last_fence = content.rfind("```")
        if last_fence != -1:
            content = content[:last_fence]
        return content.strip()

    return s

# Legacy function removed - using extract_topics_and_styles_from_prompt_qwen instead


def generate_graph_spec(user_prompt: str, graph_type: str, language: str = 'zh') -> dict:
    """
    Use the LLM to generate a JSON spec for the given graph type.
    
    Args:
        user_prompt: The user's input prompt
        graph_type: Type of graph to generate ('double_bubble_map', 'bubble_map', etc.)
        language: Language for processing ('zh' or 'en')
    
    Returns:
        dict: JSON serializable graph specification
    """
    # Use centralized prompt registry
    try:
        from prompts import get_prompt
        
        # Get the appropriate prompt template
        prompt_text = get_prompt(graph_type, language, 'generation')
        
        if not prompt_text:
            logger.error(f"Agent: No prompt found for graph type: {graph_type}")
            return {"error": f"No prompt template found for {graph_type}"}
        
        # Sanitize template to ensure only {user_prompt} is a variable; all other braces become literal
        def _sanitize_prompt_template_for_langchain(template: str) -> str:
            placeholder = "<<USER_PROMPT_PLACEHOLDER>>"
            temp = template.replace("{user_prompt}", placeholder)
            temp = temp.replace("{", "{{").replace("}", "}}")
            return temp.replace(placeholder, "{user_prompt}")

        safe_template = _sanitize_prompt_template_for_langchain(prompt_text)
        prompt = PromptTemplate(
            input_variables=["user_prompt"],
            template=safe_template
        )
        yaml_text = (prompt | llm).invoke({"user_prompt": user_prompt})
        # Some LLM clients return dict-like objects; ensure string
        try:
            raw_text = yaml_text if isinstance(yaml_text, str) else str(yaml_text)
        except Exception:
            raw_text = f"{yaml_text}"
        yaml_text_clean = extract_yaml_from_code_block(raw_text)
        
        # Debug logging
        logger.debug(f"Raw LLM response for {graph_type}: {yaml_text}")
        logger.debug(f"Cleaned response: {yaml_text_clean}")
        
        try:
            # Try JSON first, then YAML; if that fails, attempt to salvage JSON by stripping trailing backticks
            try:
                spec = json.loads(yaml_text_clean)
            except json.JSONDecodeError:
                # Try to remove accidental trailing fences in the cleaned text
                cleaned = yaml_text_clean.strip().rstrip('`').strip()
                try:
                    spec = json.loads(cleaned)
                except Exception:
                    # Attempt to salvage a JSON object from messy output
                    salvaged = _salvage_json_string(raw_text)
                    if salvaged:
                        try:
                            spec = json.loads(salvaged)
                        except Exception:
                            spec = yaml.safe_load(yaml_text_clean)
                    else:
                        spec = yaml.safe_load(yaml_text_clean)
        
            if not spec:
                raise Exception("JSON/YAML parse failed")
            
            # Validate the generated spec
            from graph_specs import DIAGRAM_VALIDATORS
            if graph_type in DIAGRAM_VALIDATORS:
                validator = DIAGRAM_VALIDATORS[graph_type]
                valid, msg = validator(spec)
                if not valid:
                    raise Exception(f"Generated JSON does not match {graph_type} schema: {msg}")
            
            logger.info(f"Agent: Successfully generated {graph_type} specification")
            return spec
            
        except Exception as e:
            logger.error(f"Agent: {graph_type} JSON generation failed: {e}")
            return {"error": f"Failed to generate valid {graph_type} JSON"}
            
    except ImportError:
        logger.error("Agent: Failed to import centralized prompt registry")
        return {"error": "Prompt registry not available"}
    except Exception as e:
        logger.error(f"Agent: Unexpected error in generate_graph_spec: {e}")
        return {"error": f"Unexpected error generating {graph_type}"}


# Legacy function removed - using agent_graph_workflow_with_styles instead


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

def get_agent_config():
    """
    Get current agent configuration
    
    Returns:
        dict: Agent configuration
    """
    return {
        "llm_model": config.QWEN_MODEL,
        "llm_url": config.QWEN_API_URL,
        "temperature": config.QWEN_TEMPERATURE,
        "max_tokens": config.QWEN_MAX_TOKENS,
        "default_language": config.GRAPH_LANGUAGE
    }


import threading
import time

def validate_agent_setup():
    """
    Validate that the agent is properly configured with cross-platform timeout
    
    Returns:
        bool: True if agent is ready, False otherwise
    """
    def timeout_handler():
        raise TimeoutError("LLM validation timed out")
    
    timer = threading.Timer(config.QWEN_TIMEOUT, timeout_handler)
    timer.start()
    
    try:
        # Test LLM connection
        test_prompt = "Test"
        llm._call(test_prompt)
        logger.info("Agent: LLM connection validated")
        return True
    except TimeoutError:
        logger.error("Agent: LLM validation timed out")
        return False
    except Exception as e:
        logger.error(f"Agent: LLM connection failed: {e}")
        return False
    finally:
        timer.cancel() 


def extract_topics_and_styles_from_prompt_qwen(user_prompt: str, language: str = 'en') -> dict:
    """
    Use Qwen to extract both topics and style preferences from user prompt in a single pass.
    Fallback to hardcoded parser if extraction fails.
    Returns a dict with 'topics', 'style_preferences', and 'diagram_type'.
    """
    from langchain.prompts import PromptTemplate
    def get_default_result():
        return {
            "topics": [],
            "style_preferences": {},
            "diagram_type": "bubble_map"
        }
    def clean_llm_response(result):
        cleaned = result.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        return cleaned.strip()
    def validate_and_parse_json(json_str):
        try:
            parsed = json.loads(json_str)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except (json.JSONDecodeError, TypeError):
            return None
    
    # Input validation
    if not isinstance(user_prompt, str) or not user_prompt.strip():
        return get_default_result()
    if language not in ['zh', 'en']:
        language = 'en'
    
    if language == 'zh':
        prompt_text = f"""
你是一个智能图表助手，用于从用户需求中同时提取主题内容和样式偏好。
请分析以下用户需求，并提取：
1. 主要主题和子主题
2. 样式偏好（颜色、字体、布局等）
3. 最适合的图表类型

可用图表类型：
# 思维导图 (Thinking Maps)
- double_bubble_map: 比较和对比两个主题
- bubble_map: 描述单个主题的特征
- circle_map: 在上下文中定义主题
- flow_map: 序列事件或过程
- brace_map: 显示整体/部分关系
- tree_map: 分类和归类信息
- multi_flow_map: 显示因果关系
- bridge_map: 桥形图 - 显示类比和相似性

# 概念图 (Concept Maps)
- concept_map: 显示概念之间的关系
- semantic_web: 创建相关概念的网络

# 思维导图 (Mind Maps)
- mindmap: 围绕中心主题组织想法



重要区分：
- 比较/对比 (compare/contrast): 使用 double_bubble_map
- 类比 (analogy): 使用 bridge_map
- 概念关系 (concept relationships): 使用 concept_map
- 思维组织 (idea organization): 使用 mindmap

关键示例：
- 比较猫和狗 → double_bubble_map
- 描述太阳系特征 → bubble_map
- 定义地球在宇宙中的圆圈图 → circle_map
- 展示水循环过程 → flow_map
- 分析酒精灯爆炸的复流程图 → multi_flow_map
- 生成山东师范大学的括号图 → brace_map
- 动物分类的树形图 → tree_map
- 心脏像泵一样的桥形图 → bridge_map
- 教育系统的概念图 → concept_map
- 创建语义网络 → semantic_web
- 制作思维导图 → mindmap


样式偏好包括：
- colorTheme: 颜色主题 (classic, innovation, colorful, monochromatic, dark, light, print, display)
- primaryColor: 主色调 (颜色名称或十六进制)
- fontSize: 字体大小
- importance: 重要性级别 (center, main, sub, detail)
- backgroundTheme: 背景主题 (dark, light)

请以JSON格式输出：
{{{{"topics": ["主题1", "主题2"],
    "style_preferences": {{{{
        "colorTheme": "主题名称",
        "primaryColor": "颜色",
        "fontSize": 数字,
        "importance": "重要性级别",
        "backgroundTheme": "背景主题"
    }}}},
    "diagram_type": "图表类型"
}}}}

用户需求：{{user_prompt}}
"""
    else:
        prompt_text = f"""
You are an intelligent diagram assistant that extracts both topic content and style preferences from user requirements.
Please analyze the following user request and extract:
1. Main topics and subtopics
2. Style preferences (colors, fonts, layout, etc.)
3. Most suitable diagram type

Available diagram types:
# Thinking Maps
- double_bubble_map: Compare and contrast two topics
- bubble_map: Describe attributes of a single topic
- circle_map: Define a topic in context
- flow_map: Sequence events or processes
- brace_map: Show whole/part relationships
- tree_map: Categorize and classify information
- multi_flow_map: Show cause and effect relationships
- bridge_map: Show analogies and similarities

# Concept Maps
- concept_map: Show relationships between concepts
- semantic_web: Create a web of related concepts

# Mind Maps
- mindmap: Organize ideas around a central topic




Important distinctions:
- Compare/contrast: use double_bubble_map
- Analogy: use bridge_map
- Concept relationships: use concept_map
- Idea organization: use mindmap

Key Examples:
- Compare cats and dogs → double_bubble_map
- Describe solar system → bubble_map
- Define Earth in context → circle_map
- Show water cycle → flow_map
- Analyze causes and effects of pollution → multi_flow_map
- Break down university structure → brace_map
- Classify animal species → tree_map
- Heart is like a pump analogy → bridge_map
- Map education concepts → concept_map
- Create semantic network → semantic_web
- Make mind map → mindmap


Style preferences include:
- colorTheme: Color theme (classic, innovation, colorful, monochromatic, dark, light, print, display)
- primaryColor: Primary color (color name or hex)
- fontSize: Font size
- importance: Importance level (center, main, sub, detail)
- backgroundTheme: Background theme (dark, light)

Please output in JSON format:
{{{{"topics": ["topic1", "topic2"],
    "style_preferences": {{{{
        "colorTheme": "theme_name",
        "primaryColor": "color",
        "fontSize": number,
        "importance": "importance_level",
        "backgroundTheme": "background_theme"
    }}}},
    "diagram_type": "diagram_type"
}}}}

User request: {{user_prompt}}
"""
    
    prompt = PromptTemplate(
        input_variables=["user_prompt"],
        template=prompt_text
    )
    
    try:
        result = (prompt | llm).invoke({"user_prompt": user_prompt})
        cleaned_result = clean_llm_response(result)
        parsed_result = validate_and_parse_json(cleaned_result)
        
        # Process LLM response without fallback overrides
        if parsed_result:
            topics = parsed_result.get('topics', [])
            if not isinstance(topics, list):
                topics = []
            style_preferences = parsed_result.get('style_preferences', {})
            if not isinstance(style_preferences, dict):
                style_preferences = {}
            diagram_type = parsed_result.get('diagram_type', 'bubble_map')
            if not isinstance(diagram_type, str):
                diagram_type = 'bubble_map'
            return {
                "topics": topics,
                "style_preferences": style_preferences,
                "diagram_type": diagram_type
            }
    except Exception as e:
        logger.error(f"Qwen style extraction failed: {e}")
    
    # Fallback to simple style extraction with default diagram type
    try:
        from diagram_styles import parse_style_from_prompt
        style_preferences = parse_style_from_prompt(user_prompt)
        
        # If LLM fails, default to bubble_map (most versatile thinking map)
        # No hardcoded keyword logic - keep it clean and professional
        return {
            "topics": [],
            "style_preferences": style_preferences,
            "diagram_type": "bubble_map"
        }
    except Exception as e:
        logger.error(f"Fallback style extraction failed: {e}")
        return get_default_result()


def generate_graph_spec_with_styles(user_prompt: str, graph_type: str, language: str = 'zh', style_preferences: dict = None) -> dict:
    """
    Generate graph specification with integrated style system.
    
    Args:
        user_prompt: User's input prompt
        graph_type: Type of diagram to generate
        language: Language for processing
        style_preferences: User's style preferences
    
    Returns:
        dict: JSON specification with integrated styles for D3.js rendering
    """
    logger.info(f"Agent: Generating graph spec with styles for type: {graph_type}")
    
    # Detect concept map generation method from user prompt
    concept_map_method = 'auto'  # Now defaults to 3-stage approach!
    if graph_type == 'concept_map':
        user_prompt_lower = user_prompt.lower()
        if any(word in user_prompt_lower for word in ['three-stage', 'three stage', '3-stage', '3 stage', 'extract topic', 'topic extraction']):
            concept_map_method = 'three_stage'
            logger.info("Agent: Detected three-stage approach for concept map")
        elif any(word in user_prompt_lower for word in ['network', 'matrix', 'relationship matrix', 'network-first', 'network first']):
            concept_map_method = 'network_first'
            logger.info("Agent: Detected network-first approach for concept map")
        elif any(word in user_prompt_lower for word in ['two-stage', 'two stage', 'staged', 'step by step']):
            concept_map_method = 'two_stage'
            logger.info("Agent: Detected two-stage approach for concept map")
        elif any(word in user_prompt_lower for word in ['unified', 'one-shot', 'single step']):
            concept_map_method = 'unified'
            logger.info("Agent: Detected unified approach for concept map")
    
    # Generate the base specification
    if graph_type == 'concept_map':
        spec = generate_concept_map_robust(user_prompt, language, concept_map_method)
    else:
        spec = generate_graph_spec(user_prompt, graph_type, language)
    
    if not spec or isinstance(spec, dict) and spec.get('error'):
        logger.error(f"Agent: Failed to generate base spec for {graph_type}")
        return spec
    
    # Integrate style system
    try:
        from diagram_styles import get_style, parse_style_from_prompt
        
        # Parse additional styles from prompt if not provided
        if not style_preferences:
            style_preferences = parse_style_from_prompt(user_prompt)
        
        # Get the complete style configuration
        color_theme = style_preferences.get('colorTheme', 'classic')
        variation = 'colorful'  # Default variation
        if 'dark' in style_preferences.get('backgroundTheme', '').lower():
            variation = 'dark'
        elif 'light' in style_preferences.get('backgroundTheme', '').lower():
            variation = 'light'
        
        complete_style = get_style(graph_type, style_preferences, color_theme, variation)
        
        # Add style information to the spec
        spec['_style'] = complete_style
        spec['_style_metadata'] = {
            'color_theme': color_theme,
            'variation': variation,
            'user_preferences': style_preferences
        }
        
        logger.info(f"Agent: Successfully integrated styles for {graph_type}")
        
    except Exception as e:
        logger.error(f"Agent: Style integration failed: {e}")
        # Continue without styles if integration fails
        spec['_style'] = {}
        spec['_style_metadata'] = {}
    
    return spec


def _invoke_llm_prompt(prompt_template: str, variables: dict) -> str:
    """Invoke LLM with a specific prompt template and variables, and return raw string."""
    safe_template = prompt_template
    # Sanitize braces except for placeholders present in variables
    for k in variables.keys():
        placeholder = f"<<{k.upper()}>>"
        safe_template = safe_template.replace(f"{{{k}}}", placeholder)
    safe_template = safe_template.replace("{", "{{").replace("}", "}}")
    for k in variables.keys():
        placeholder = f"<<{k.upper()}>>"
        safe_template = safe_template.replace(placeholder, f"{{{k}}}")
    pt = PromptTemplate(input_variables=list(variables.keys()), template=safe_template)
    raw = (pt | llm).invoke(variables)
    return raw if isinstance(raw, str) else str(raw)


def _parse_strict_json(text: str) -> dict:
    """Parse JSON with robust extraction and salvage; raise on failure."""
    cleaned = extract_yaml_from_code_block(text)
    # Normalize unicode quotes and remove non-JSON noise
    cleaned = cleaned.strip().strip('`')
    # Replace smart quotes with ASCII equivalents
    cleaned = cleaned.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    cleaned = cleaned.replace('"', '"').replace('"', '"').replace('"', '"').replace('"', '"')
    # Remove zero-width and control characters
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", cleaned)
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", cleaned)
    # Remove JS-style comments if present
    cleaned = re.sub(r"//.*?$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    # Remove trailing commas before ] or }
    cleaned = re.sub(r",\s*(\]|\})", r"\1", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        # Try salvage
        candidate = _salvage_json_string(cleaned)
        if candidate:
            candidate = re.sub(r",\s*(\]|\})", r"\1", candidate)
            return json.loads(candidate)
        raise


def generate_concept_map_two_stage(user_prompt: str, language: str) -> dict:
    """Deterministic two-stage generation for concept maps (no fallback parsing errors)."""
    # Stage 1: keys
    key_prompt = get_prompt('concept_map_keys', language, 'generation')
    raw_keys = _invoke_llm_prompt(key_prompt, { 'user_prompt': user_prompt })
    
    # Use improved parsing for better error handling
    try:
        from concept_map_agent import ConceptMapAgent
        agent = ConceptMapAgent()
        keys_obj = agent._parse_json_response(raw_keys)
        logger.info("Used ConceptMapAgent improved parsing for keys generation")
    except Exception as e:
        logger.warning(f"ConceptMapAgent parsing failed for keys, falling back to strict parsing: {e}")
        # Fallback to strict parsing if ConceptMapAgent is not available
        keys_obj = _parse_strict_json(raw_keys)
        logger.info("Used strict parsing fallback for keys generation")
    topic = (keys_obj.get('topic') or user_prompt).strip()
    keys_raw = keys_obj.get('keys') or []
    keys = []
    seen_keys = set()
    for k in keys_raw:
        name = k.get('name') if isinstance(k, dict) else k
        if isinstance(name, str):
            name = name.strip()
            if name and name.lower() not in seen_keys:
                keys.append(name)
                seen_keys.add(name.lower())
    # Cap keys to 4–8 for readability
    max_keys = 8
    min_keys = 4
    keys = keys[:max_keys]
    if len(keys) < min_keys and len(keys_raw) > 0:
        # Best-effort: keep as is; downstream will handle layout even with fewer keys
        pass

    # Stage 2: parts for each key
    from concurrent.futures import ThreadPoolExecutor, as_completed
    parts_prompt = get_prompt('concept_map_parts', language, 'generation')

    # Budget total concepts <= 30
    max_concepts_total = 30
    remaining_budget = max(0, max_concepts_total - len(keys))
    per_key_cap = max(2, remaining_budget // max(1, len(keys))) if keys else 0

    def fetch_parts(k: str) -> tuple:
        try:
            raw = _invoke_llm_prompt(parts_prompt, { 'topic': topic, 'key': k })
            
            # Use improved parsing for better error handling
            try:
                from concept_map_agent import ConceptMapAgent
                agent = ConceptMapAgent()
                obj = agent._parse_json_response(raw)
                logger.debug(f"Used ConceptMapAgent improved parsing for parts of key '{k}'")
            except Exception as e:
                logger.debug(f"ConceptMapAgent parsing failed for parts of key '{k}', using strict parsing fallback")
                # Fallback to strict parsing if ConceptMapAgent is not available
                obj = _parse_strict_json(raw)
            plist = obj.get('parts') or []
            parts_collected = []
            seen = set()
            for p in plist:
                name = p.get('name') if isinstance(p, dict) else p
                label = p.get('label') if isinstance(p, dict) else None
                if isinstance(name, str):
                    name = name.strip()
                    if name and name.lower() not in seen:
                        parts_collected.append({'name': name, 'label': (label or '').strip()[:60]})
                        seen.add(name.lower())
                if len(parts_collected) >= per_key_cap:
                    break
            return (k, parts_collected)
        except Exception:
            return (k, [])

    parts_results = { k: [] for k in keys }
    # Run in parallel to save time
    max_workers = min(6, len(keys)) or 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_parts, k) for k in keys]
    for fut in as_completed(futures):
            k, plist = fut.result()
            parts_results[k] = plist

    # Merge into standard concept map spec
    concepts = []
    seen_concepts = set()
    for name in keys + [p.get('name') for arr in parts_results.values() for p in arr]:
        low = name.lower()
        if low not in seen_concepts and len(concepts) < max_concepts_total:
            concepts.append(name)
            seen_concepts.add(low)
    relationships = []
    # topic -> key relationships (use label if present)
    for k in (keys_obj.get('keys') or []):
        name = k.get('name') if isinstance(k, dict) else None
        label = k.get('label') if isinstance(k, dict) else 'related to'
        if isinstance(name, str) and name.strip():
            if name in concepts:
                relationships.append({ 'from': topic, 'to': name, 'label': label or 'related to' })
    # key -> part relationships
    for key, plist in parts_results.items():
        for p in plist:
            if p.get('name') in concepts:
                relationships.append({ 'from': key, 'to': p.get('name'), 'label': (p.get('label') or 'includes') })

    # Final trim to satisfy validator (<= 30 concepts)
    if len(concepts) > max_concepts_total:
        concepts = concepts[:max_concepts_total]
    allowed = set(concepts)
    relationships = [r for r in relationships if r.get('from') in allowed.union({topic}) and r.get('to') in allowed.union({topic})]
    # Prune keys and parts to allowed concepts
    keys = [k for k in keys if k in allowed]
    parts_results = { k: [p for p in (parts_results.get(k, []) or []) if p.get('name') in allowed] for k in keys }

    # Include keys and parts for sector layout
    spec = { 'topic': topic, 'concepts': concepts, 'relationships': relationships, 'keys': [{'name': k} for k in keys], 'key_parts': { k: parts_results.get(k, []) for k in keys } }
    return spec


def generate_concept_map_unified(user_prompt: str, language: str) -> dict:
    """One-shot concept map generation with keys, parts, and relationships together."""
    prompt_key = 'concept_map_unified_generation_zh' if language == 'zh' else 'concept_map_unified_generation_en'
    unified_prompt = get_prompt('concept_map_unified', language, 'generation')
    raw = _invoke_llm_prompt(unified_prompt, { 'user_prompt': user_prompt })
    
    # Use the improved ConceptMapAgent parsing for better error handling
    try:
        from concept_map_agent import ConceptMapAgent
        agent = ConceptMapAgent()
        obj = agent._parse_json_response(raw)
        logger.info("Used ConceptMapAgent improved parsing for unified generation")
    except Exception as e:
        logger.warning(f"ConceptMapAgent parsing failed, falling back to strict parsing: {e}")
        # Fallback to strict parsing if ConceptMapAgent is not available
        try:
            obj = _parse_strict_json(raw)
            logger.info("Used strict parsing fallback for unified generation")
        except Exception as e2:
            logger.error(f"All parsing methods failed for unified generation: {e2}")
            return { 'error': f'Concept map parsing failed: {e2}' }
    # Extract - prioritize concepts from ConceptMapAgent parsing
    topic = (obj.get('topic') or user_prompt).strip()
    concepts_raw = obj.get('concepts') or []
    keys_raw = obj.get('keys') or []
    key_parts_raw = obj.get('key_parts') or {}
    rels_raw = obj.get('relationships') or []
    
    # First, use concepts if they were successfully extracted
    if concepts_raw and isinstance(concepts_raw, list):
        concepts = []
        seen_all = set()
        for concept in concepts_raw:
            if isinstance(concept, str) and concept.strip():
                name = concept.strip()
                low = name.lower()
                if low not in seen_all and len(concepts) < 30:
                    concepts.append(name)
                    seen_all.add(low)
        allowed = set(concepts)
        logger.info(f"Using concepts extracted by ConceptMapAgent: {concepts}")
    else:
        # Fallback: build concepts from keys and parts (original logic)
        # Normalize keys
        keys = []
        seen_k = set()
        for k in keys_raw:
            name = k.get('name') if isinstance(k, dict) else k
            if isinstance(name, str):
                name = name.strip()
                if name and name.lower() not in seen_k:
                    keys.append(name)
                    seen_k.add(name.lower())
        # Normalize parts
        parts_results = {}
        seen_parts_global = set()
        for k in keys:
            plist = key_parts_raw.get(k) or []
            out = []
            seen_local = set()
            for p in plist:
                name = p.get('name') if isinstance(k, dict) else p
                if isinstance(name, str):
                    name = name.strip()
                    low = name.lower()
                    if name and low not in seen_local and low not in seen_parts_global:
                        out.append(name)
                        seen_local.add(low)
                        seen_parts_global.add(low)
            parts_results[k] = out
        # Build concepts within cap
        max_concepts_total = 30
        concepts = []
        seen_all = set()
        for name in keys + [p for arr in parts_results.values() for p in arr]:
            low = name.lower()
            if low not in seen_all and len(concepts) < max_concepts_total:
                concepts.append(name)
                seen_all.add(low)
        allowed = set(concepts)
        logger.info(f"Built concepts from keys/parts: {concepts}")
    # Relationships
    relationships = []
    pair_seen = set()
    def add_rel(frm, to, label):
        if not isinstance(frm, str) or not isinstance(to, str):
            return
        if frm == to:
            return
        if frm not in allowed and frm != topic:
            return
        if to not in allowed and to != topic:
            return
        key = tuple(sorted((frm.lower(), to.lower())))
        if key in pair_seen:
            return
        pair_seen.add(key)
        relationships.append({ 'from': frm, 'to': to, 'label': (label or 'related to')[:60] })
    # Add mandatory topic->key and key->part
    for k in keys_raw:
        name = k.get('name') if isinstance(k, dict) else None
        label = (k.get('label') if isinstance(k, dict) else 'related to')
        if isinstance(name, str) and name.strip() and name in allowed:
            add_rel(topic, name, label)
    for key, plist in parts_results.items():
        for p in plist:
            add_rel(key, p, 'includes')
    # Add extra from rels_raw (deduped, within allowed)
    for r in rels_raw:
        add_rel(r.get('from'), r.get('to'), r.get('label'))
    return {
        'topic': topic,
        'concepts': list(allowed),
        'relationships': relationships,
        'keys': [{'name': k} for k in keys if k in allowed],
        'key_parts': { k: [{'name': p} for p in parts_results.get(k, []) if p in allowed] for k in keys if k in allowed }
    }


def generate_concept_map_enhanced_30(user_prompt: str, language: str) -> dict:
    """
    Enhanced concept map generation that produces exactly 30 concepts.
    
    This integrates with existing topic extraction and uses optimized prompts
    to generate exactly 30 concepts + relationships, matching the desired workflow.
    """
    try:
        # Use existing topic extraction (already works!)
        extraction = extract_topics_and_styles_from_prompt_qwen(user_prompt, language)
        topics = extraction.get('topics', [])
        central_topic = topics[0] if topics else user_prompt.split()[:3]  # Use first topic or fallback
        
        if isinstance(central_topic, list):
            central_topic = ' '.join(central_topic)
        
        logger.info(f"Agent: Using central topic for 30-concept generation: {central_topic}")
        
        # Generate exactly 30 concepts using improved prompts
        if language == 'zh':
            concept_prompt = f"""
请为主题"{central_topic}"生成恰好30个相关的关键概念。

主题分析策略：
1. 核心组成部分 - 有哪些基本要素？
2. 重要过程 - 涉及哪些关键流程？
3. 类型分类 - 有哪些不同类别？
4. 工具方法 - 使用什么工具和方法？
5. 相关人员 - 涉及哪些角色？
6. 应用领域 - 在哪些方面应用？
7. 特征属性 - 有什么特点？
8. 发展历程 - 重要的发展阶段？

输出JSON格式：
{{
  "concepts": ["概念1", "概念2", ..., "概念30"]
}}

要求：
- 恰好30个概念，不多不少
- 每个概念2-4个字
- 覆盖上述8个方面
- 具体且有意义，避免抽象术语
- 确保与"{central_topic}"直接相关
"""
        else:
            concept_prompt = f"""
Generate exactly 30 specific and meaningful concepts related to: {central_topic}

Analysis Strategy - Cover these aspects:
1. CORE COMPONENTS: What are the fundamental parts?
2. KEY PROCESSES: What important procedures or actions?
3. TYPES/CATEGORIES: What different forms exist?
4. TOOLS/METHODS: What tools, techniques, or approaches?
5. PEOPLE/ROLES: Who is involved or affected?
6. APPLICATIONS: Where and how is it used?
7. CHARACTERISTICS: What are the key properties?
8. DEVELOPMENT: Important stages or evolution?

Output JSON format:
{{
  "concepts": ["concept1", "concept2", ..., "concept30"]
}}

Requirements:
- EXACTLY 30 concepts, no more, no less
- Each concept should be 2-4 words
- Be SPECIFIC and domain-relevant (not generic terms)
- Cover the 8 aspects above
- Directly related to "{central_topic}"
- Output ONLY valid JSON, no other text
"""
        
        concepts_response = _invoke_llm_prompt(concept_prompt, {'central_topic': central_topic})
        logger.info(f"Agent: LLM concepts response length: {len(concepts_response)} chars")
        
        # Parse concepts with better error handling
        concepts = []
        try:
            import json
            # Clean the response first
            cleaned_response = concepts_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            logger.info(f"Agent: Parsing concepts response: {cleaned_response[:200]}...")
            concepts_data = json.loads(cleaned_response)
            concepts = concepts_data.get('concepts', [])
            logger.info(f"Agent: Successfully parsed {len(concepts)} concepts from LLM")
            
            # Ensure exactly 30 concepts
            if len(concepts) > 30:
                concepts = concepts[:30]
            elif len(concepts) < 30:
                logger.warning(f"Agent: Only got {len(concepts)} concepts, padding to 30")
                # Use topic-specific padding instead of generic
                topic_base = str(central_topic).lower()
                padding_concepts = [
                    f"{central_topic}相关技术", f"{central_topic}发展", f"{central_topic}应用",
                    f"{central_topic}特点", f"{central_topic}优势", f"{central_topic}挑战",
                    f"{central_topic}未来", f"{central_topic}标准", f"{central_topic}管理"
                ]
                base_count = len(concepts)
                for i in range(30 - base_count):
                    if i < len(padding_concepts):
                        concepts.append(padding_concepts[i])
                    else:
                        concepts.append(f"{central_topic}方面{i+1}")
                        
        except json.JSONDecodeError as e:
            logger.error(f"Agent: JSON parsing failed: {e}")
            logger.error(f"Agent: Raw response: {concepts_response[:500]}...")
            # Better fallback with topic-specific concepts
            if language == 'zh' and '计算机' in str(central_topic):
                concepts = [
                    "硬件", "软件", "操作系统", "处理器", "内存", "存储器",
                    "显卡", "主板", "网络", "安全", "编程", "算法",
                    "数据库", "人工智能", "机器学习", "云计算", "大数据", "物联网",
                    "网络协议", "编程语言", "开发工具", "用户界面", "系统架构", "数据结构",
                    "网络安全", "软件工程", "计算机图形", "多媒体", "游戏开发", "移动应用"
                ]
            else:
                # Generic fallback (should rarely be used now)
                concepts = [
                    "Core components", "Basic principles", "Key processes", "Main features",
                    "Essential tools", "Important methods", "Primary functions", "Basic structure",
                    "Fundamental concepts", "Key relationships", "Main categories", "Core elements",
                    "Essential aspects", "Important factors", "Basic requirements", "Key characteristics",
                    "Main applications", "Primary uses", "Core benefits", "Essential properties",
                    "Key advantages", "Main challenges", "Important considerations", "Basic limitations",
                    "Essential requirements", "Key dependencies", "Main outcomes", "Important results",
                    "Core objectives", "Essential goals"
                ]
            concepts = concepts[:30]  # Ensure exactly 30
        
        # Generate relationships using LLM
        logger.info(f"Agent: Generating relationships using LLM for {len(concepts)} concepts")
        
        if language == 'zh':
            relationships_prompt = f"""
你是一个领域专家，请分析主题"{central_topic}"与以下30个概念之间的精确关系，以及概念之间的具体联系。

概念列表：
{', '.join(concepts)}

请生成关系网络，包括：
1. 主题与每个概念的关系（必须包含所有30个概念）
2. 概念之间的重要关系（选择最有意义的15-25个关系）

关系标签要求：
- 使用领域特定的精确关系词汇，例如：
  * 软件：继承、调用、编译、部署、封装、重构、编译、序列化
  * 生物：进化、变异、选择、适应、遗传、分化、共生、捕食  
  * 物理：相互作用、量子化、测量、干涉、衰变、激发、辐射、吸收
  * 经济：供给、需求、投资、流动、调节、竞争、创新、交换
- 严格避免过度使用通用词汇：包含、使用、基于、相关、涉及、实现、支持
- 每个关系标签应该体现具体的因果、依赖、转换、影响等机制
- 优先使用动词形式的关系描述

输出JSON格式：
{{
  "relationships": [
    {{"from": "源概念", "to": "目标概念", "label": "精确关系"}},
    {{"from": "{central_topic}", "to": "概念1", "label": "定义"}},
    {{"from": "概念A", "to": "概念B", "label": "触发"}}
  ]
}}

要求：
- 关系标签必须具体、准确，体现真实的语义机制
- 避免重复使用相同的关系类型，追求多样性
- 每个关系都应该传达明确的因果或依赖信息
- 关系标签简洁（1-3个字）
- 确保包含主题到所有30个概念的关系
- 概念间关系要体现真实的逻辑联系和机制
- 输出纯JSON格式
"""
        else:
            relationships_prompt = f"""
You are a domain expert. Please analyze the precise relationships between the topic "{central_topic}" and the following 30 concepts, as well as specific connections between concepts.

Concepts:
{', '.join(concepts)}

Generate a relationship network including:
1. Topic to each concept relationships (must include all 30 concepts)
2. Important concept-to-concept relationships (select the most meaningful 15-25 relationships)

Relationship label requirements:
- Use domain-specific precise relationship vocabulary, examples:
  * Software: inherits, invokes, compiles, deploys, encapsulates, refactors, serializes
  * Biology: evolves, mutates, selects, adapts, inherits, differentiates, symbioses, predates  
  * Physics: interacts, quantizes, measures, interferes, decays, excites, radiates, absorbs
  * Economics: supplies, demands, invests, flows, regulates, competes, innovates, exchanges
- Strictly avoid overusing generic terms: includes, uses, based on, relates, involves, implements, supports
- Each relationship label should reflect specific causal, dependency, transformation, or influence mechanisms
- Prefer verb forms for relationship descriptions

Output JSON format:
{{
  "relationships": [
    {{"from": "source", "to": "target", "label": "precise_relationship"}},
    {{"from": "{central_topic}", "to": "concept1", "label": "defines"}},
    {{"from": "conceptA", "to": "conceptB", "label": "triggers"}}
  ]
}}

Requirements:
- Relationship labels must be specific and accurate, reflecting real semantic mechanisms
- Avoid repeating the same relationship types, pursue diversity
- Each relationship should convey clear causal or dependency information
- Relationship labels should be concise (1-3 words)
- Ensure topic-to-concept relationships for all 30 concepts
- Concept-to-concept relationships should reflect real logical connections and mechanisms
- Output pure JSON format only
"""
        
        relationships_response = _invoke_llm_prompt(relationships_prompt, {'central_topic': central_topic})
        logger.info(f"Agent: LLM relationships response length: {len(relationships_response)} chars")
        
        # Parse relationships with robust error handling
        relationships = []
        try:
            import json
            # Clean the response
            cleaned_response = relationships_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            logger.info(f"Agent: Parsing relationships response: {cleaned_response[:200]}...")
            relationships_data = json.loads(cleaned_response)
            relationships = relationships_data.get('relationships', [])
            logger.info(f"Agent: Successfully parsed {len(relationships)} relationships from LLM")
            
            # Validate that we have topic->concept relationships for most concepts
            topic_rels = [r for r in relationships if r.get('from') == str(central_topic)]
            logger.info(f"Agent: Found {len(topic_rels)} topic-to-concept relationships")
            
            # If we're missing many topic relationships, add them
            covered_concepts = set(r.get('to') for r in topic_rels)
            missing_concepts = [c for c in concepts if c not in covered_concepts]
            
            if missing_concepts:
                logger.warning(f"Agent: Adding missing topic relationships for {len(missing_concepts)} concepts")
                basic_labels = ["包含", "涉及", "使用"] if language == 'zh' else ["includes", "involves", "uses"]
                for i, concept in enumerate(missing_concepts):
                    relationships.append({
                        "from": str(central_topic),
                        "to": concept,
                        "label": basic_labels[i % len(basic_labels)]
                    })
                    
        except json.JSONDecodeError as e:
            logger.error(f"Agent: Relationships JSON parsing failed: {e}")
            logger.error(f"Agent: Raw relationships response: {relationships_response[:500]}...")
            
            # Try to extract partial relationships from malformed JSON
            logger.info(f"Agent: Attempting to extract partial relationships")
            relationships = []
            
            try:
                import re
                # Find all relationship patterns in the response
                rel_pattern = r'\{"from":\s*"([^"]+)",\s*"to":\s*"([^"]+)",\s*"label":\s*"([^"]+)"\}'
                matches = re.findall(rel_pattern, relationships_response)
                
                for from_node, to_node, label in matches:
                    relationships.append({
                        "from": from_node,
                        "to": to_node, 
                        "label": label
                    })
                
                logger.info(f"Agent: Extracted {len(relationships)} relationships from partial JSON")
                
                # Ensure we have topic relationships for all concepts
                topic_rels = [r for r in relationships if r.get('from') == str(central_topic)]
                covered_concepts = set(r.get('to') for r in topic_rels)
                missing_concepts = [c for c in concepts if c not in covered_concepts]
                
                if missing_concepts:
                    logger.info(f"Agent: Adding missing topic relationships for {len(missing_concepts)} concepts")
                    basic_labels = ["包含", "涉及", "使用", "需要", "支持"] if language == 'zh' else ["includes", "involves", "uses", "requires", "supports"]
                    for i, concept in enumerate(missing_concepts):
                        relationships.append({
                            "from": str(central_topic),
                            "to": concept,
                            "label": basic_labels[i % len(basic_labels)]
                        })
                
            except Exception as parse_error:
                logger.error(f"Agent: Partial extraction also failed: {parse_error}")
                
                # Ultimate fallback: create basic meaningful relationships
                logger.info(f"Agent: Using ultimate fallback relationship generation")
                relationships = []
                
                # Basic topic -> concept relationships
                basic_labels = ["包含", "涉及", "使用", "需要", "支持"] if language == 'zh' else ["includes", "involves", "uses", "requires", "supports"]
                for i, concept in enumerate(concepts):
                    relationships.append({
                        "from": str(central_topic),
                        "to": concept,
                        "label": basic_labels[i % len(basic_labels)]
                    })
                
                # Basic concept -> concept relationships (fewer, but meaningful)
                concept_labels = ["依赖", "支持", "连接"] if language == 'zh' else ["depends on", "supports", "connects to"]
                for i in range(0, min(10, len(concepts)-1)):
                    if i+1 < len(concepts):
                        relationships.append({
                            "from": concepts[i],
                            "to": concepts[i+1],
                            "label": concept_labels[i % len(concept_labels)]
                        })
        
        # Create the spec
        spec = {
            'topic': str(central_topic),
            'concepts': concepts[:30],  # Ensure exactly 30
            'relationships': relationships,
            '_method': 'enhanced_30',
            '_concept_count': len(concepts[:30])
        }
        
        logger.info(f"Agent: Generated {len(spec['concepts'])} concepts and {len(spec['relationships'])} relationships")
        
        # Enhance the spec with layout and positioning using ConceptMapAgent
        try:
            from concept_map_agent import ConceptMapAgent
            agent = ConceptMapAgent()
            enhanced_result = agent.enhance_spec(spec)
            
            if enhanced_result.get('success'):
                enhanced_spec = enhanced_result.get('spec', spec)
                logger.info(f"Agent: Successfully enhanced spec with layout: {enhanced_spec.get('_layout', {}).get('algorithm', 'unknown')}")
                return enhanced_spec
            else:
                logger.warning(f"Agent: ConceptMapAgent enhancement failed: {enhanced_result.get('error')}")
                return spec
                
        except Exception as e:
            logger.error(f"Agent: ConceptMapAgent enhancement failed: {e}")
            return spec
        
    except Exception as e:
        logger.error(f"Agent: Enhanced 30-concept generation failed: {e}")
        # Fallback to original method
        return generate_concept_map_unified(user_prompt, language)


def generate_concept_map_robust(user_prompt: str, language: str, method: str = 'auto') -> dict:
    """Robust concept map generation with multiple approaches.
    
    Args:
        user_prompt: User's input prompt
        language: Language for processing
        method: Generation method ('auto', 'unified', 'two_stage', 'network_first', 'three_stage')
    
    Returns:
        dict: Concept map specification
    """
    # NEW: Try the enhanced concept-first method (RECOMMENDED)
    if method in ['auto', 'three_stage']:
        try:
            # Use existing topic extraction + enhanced 30-concept generation
            return generate_concept_map_enhanced_30(user_prompt, language)
        except Exception as e:
            logger.warning(f"Enhanced 30-concept generation failed: {e}")
    
    # If method is specified, try that first
    if method == 'network_first':
        try:
            from concept_map_agent import ConceptMapAgent
            agent = ConceptMapAgent()
            # Use the global LLM client
            result = agent.generate_network_first(user_prompt, llm, language)
            if isinstance(result, dict) and result.get('success'):
                return result.get('spec', {})
            else:
                logger.warning(f"Network-first generation failed: {result.get('error')}")
        except Exception as e:
            logger.warning(f"Network-first generation failed: {e}")
    
    # Fallback to original methods
    if method in ['auto', 'unified']:
        unified = generate_concept_map_unified(user_prompt, language)
        if isinstance(unified, dict) and not unified.get('error'):
            return unified
        logger.warning(f"Unified concept map generation failed: {unified.get('error') if isinstance(unified, dict) else 'unknown'}")
    
    if method in ['auto', 'two_stage']:
        try:
            two_stage = generate_concept_map_two_stage(user_prompt, language)
            if isinstance(two_stage, dict) and not two_stage.get('error'):
                return two_stage
            logger.warning("Two-stage concept map generation failed")
        except Exception as e:
            logger.warning(f"Two-stage concept map generation failed: {e}")
    
    return { 'error': 'All concept map generation methods failed' }


def agent_graph_workflow_with_styles(user_prompt, language='zh'):
    """
    Enhanced agent workflow with integrated style system.
    
    Args:
        user_prompt (str): User's input prompt
        language (str): Language for processing ('zh' or 'en')
    
    Returns:
        dict: JSON specification with integrated styles for D3.js rendering
    """
    logger.info(f"Agent: Starting enhanced graph workflow for: {user_prompt}")
    
    try:
        # Extract topics, styles, and diagram type
        extraction = extract_topics_and_styles_from_prompt_qwen(user_prompt, language)
        topics = extraction.get('topics', [])
        style_preferences = extraction.get('style_preferences', {})
        diagram_type = extraction.get('diagram_type', 'bubble_map')
        
        logger.info(f"Agent: Extracted - topics: {topics}, diagram_type: {diagram_type}")
        logger.info(f"Agent: Style preferences: {style_preferences}")
        
        # Generate specification with integrated styles
        spec = generate_graph_spec_with_styles(user_prompt, diagram_type, language, style_preferences)
        
        # Add metadata to the result
        result = {
            'spec': spec,
            'diagram_type': diagram_type,
            'topics': topics,
            'style_preferences': style_preferences,
            'language': language
        }
        
        logger.info(f"Agent: Enhanced workflow completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Agent: Enhanced workflow failed: {e}")
        # Do not fallback to a different diagram type; surface the error with intended type
        return {
            'spec': { 'error': f'Generation failed: {str(e)}' },
            'diagram_type': 'concept_map',
            'topics': [],
            'style_preferences': {},
            'language': language
        }