# ============================================================================
# CONCEPT MAP GENERATION APPROACHES
# ============================================================================

# Choose your preferred approach:
# 1. "simplified_two_stage" - RECOMMENDED: Simple, reliable, two LLM calls
# 2. "hierarchical_three_stage" - Structured, three LLM calls, good for complex topics
# 3. "network_first" - Focus on connections, two LLM calls
# 4. "template_based" - Consistent structure, two LLM calls
# 5. "unified" - Original complex approach (may have parsing issues)

CONCEPT_MAP_APPROACH = "simplified_two_stage"

# Language preference
CONCEPT_MAP_LANGUAGE = "en"  # "en" or "zh"

# ============================================================================
# LAYOUT CONFIGURATION
# ============================================================================

# Node spacing and positioning
NODE_SPACING = 2.0  # Increased for better spread
CANVAS_PADDING = 80
MIN_NODE_DISTANCE = 120

# Radial layout parameters
INNER_RADIUS = 0.5   # Increased for better spread
MIN_RADIUS = 0.7     # Increased for better spread
MAX_RADIUS = 0.95
GAP_FACTOR = 0.7     # Reduced for more spread
TARGET_RADIUS = 0.85 # Increased for better spread

# Force simulation parameters
REPULSION_FORCE = 0.035  # Increased for better spread
SPRING_FORCE = 0.025     # Reduced for more spread
STEP_SIZE = 0.18         # Increased for faster convergence
ITERATIONS = 250         # More iterations for better positioning

# ============================================================================
# CONCEPT MAP GENERATION PARAMETERS
# ============================================================================

# Target concept counts for different approaches
SIMPLIFIED_TWO_STAGE = {
    "min_concepts": 20,
    "max_concepts": 30,
    "min_relationships": 30,  # topic→concepts + concept→concept
    "max_relationships": 50
}

HIERARCHICAL_THREE_STAGE = {
    "min_categories": 5,
    "max_categories": 8,
    "min_sub_concepts_per_category": 3,
    "max_sub_concepts_per_category": 5,
    "min_relationships": 40,
    "max_relationships": 80
}

NETWORK_FIRST = {
    "min_concepts": 25,
    "max_concepts": 30,
    "min_relationships": 35,
    "max_relationships": 60
}

TEMPLATE_BASED = {
    "min_concepts": 20,
    "max_concepts": 30,
    "relationship_templates": [
        "causes", "includes", "requires", "results_in", 
        "is_type_of", "located_in", "part_of", "influences"
    ],
    "min_relationships": 30,
    "max_relationships": 50
}

# ============================================================================
# QUALITY CONTROL
# ============================================================================

# Maximum text lengths
MAX_TOPIC_LENGTH = 60
MAX_CONCEPT_LENGTH = 40
MAX_RELATIONSHIP_LABEL_LENGTH = 30

# Validation rules
ENFORCE_UNIQUE_CONCEPTS = True
ENFORCE_UNIQUE_RELATIONSHIPS = True
ALLOW_SELF_LOOPS = False
REQUIRE_TOPIC_CONNECTIONS = True

# ============================================================================
# DEBUGGING AND LOGGING
# ============================================================================

# Enable detailed logging for debugging
DEBUG_MODE = False
LOG_LLM_RESPONSES = False
LOG_PARSING_ATTEMPTS = False

# Fallback behavior
ENABLE_FALLBACK_PARSING = True
MAX_PARSING_ATTEMPTS = 3
