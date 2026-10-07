"""Tools & Function Calling Module for Competitive Programming & DSA Coach.

Provides callable action tools for the AI coach:
1. suggest_problem(topic: str) -> Problem suggestion with difficulty
2. get_weak_topics() -> Analysis of chat history & submission errors to identify weak areas
3. log_submission(problem: str, topic: str, verdict: str) -> Logs submission to SQLite
"""

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Enable flexible imports whether running from root or from within backend/
try:
    from backend import db
except ImportError:
    import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])

# ============================================================================
# 1. Curated Problem Lookup Catalog
# ============================================================================

CURATED_PROBLEMS: Dict[str, List[Dict[str, str]]] = {
    "dynamic_programming": [
        {
            "name": "0/1 Knapsack",
            "difficulty": "Medium",
            "pattern": "Subset Selection with Capacity Constraint",
            "summary": "Determine maximum value attainable with item weights and values under capacity W.",
        },
        {
            "name": "Coin Change",
            "difficulty": "Medium",
            "pattern": "Unbounded Knapsack / Minimum Transitions",
            "summary": "Find fewest coins needed to make up a given amount, or -1 if impossible.",
        },
        {
            "name": "Longest Common Subsequence",
            "difficulty": "Medium",
            "pattern": "2D Grid DP on Two Sequences",
            "summary": "Find the length of the longest subsequence present in both strings.",
        },
        {
            "name": "Climbing Stairs",
            "difficulty": "Easy",
            "pattern": "Fibonacci / 1D State Transition",
            "summary": "Count distinct ways to reach top taking 1 or 2 steps at a time.",
        },
    ],
    "graphs": [
        {
            "name": "Number of Islands",
            "difficulty": "Medium",
            "pattern": "Grid Traversal / Connected Components (BFS/DFS)",
            "summary": "Count islands formed by horizontally/vertically adjacent lands in a 2D binary grid.",
        },
        {
            "name": "Course Schedule",
            "difficulty": "Medium",
            "pattern": "Cycle Detection & Topological Sort (Kahn's Algorithm)",
            "summary": "Determine if all courses can be finished given prerequisite dependency pairs.",
        },
        {
            "name": "Network Delay Time",
            "difficulty": "Medium",
            "pattern": "Single-Source Shortest Path (Dijkstra's Algorithm)",
            "summary": "Calculate minimum time for signal to reach all nodes from starting node.",
        },
        {
            "name": "Rotting Oranges",
            "difficulty": "Medium",
            "pattern": "Multi-Source BFS / Layer-by-Layer Propagation",
            "summary": "Find minimum minutes until no fresh orange remains in the grid.",
        },
    ],
    "binary_search": [
        {
            "name": "Search in Rotated Sorted Array",
            "difficulty": "Medium",
            "pattern": "Modified Binary Search with Pivot Discontinuity",
            "summary": "Locate target index in O(log N) within array rotated at unknown pivot.",
        },
        {
            "name": "Koko Eating Bananas",
            "difficulty": "Medium",
            "pattern": "Binary Search on Answer / Monotonic Predicate",
            "summary": "Find minimum integer eating speed k to eat all bananas within h hours.",
        },
        {
            "name": "Find Minimum in Rotated Sorted Array",
            "difficulty": "Medium",
            "pattern": "Inflection Point Search / Boundary Condition",
            "summary": "Find minimum element in sorted array rotated between 1 and n times.",
        },
        {
            "name": "Binary Search (Classic)",
            "difficulty": "Easy",
            "pattern": "Standard Binary Search / Strict Invariant",
            "summary": "Find target in sorted array in O(log N) time with low <= high invariant.",
        },
    ],
    "trees_and_heaps": [
        {
            "name": "Invert Binary Tree",
            "difficulty": "Easy",
            "pattern": "Recursive Tree Traversal / Subtree Swap",
            "summary": "Invert binary tree by swapping left and right child pointers recursively.",
        },
        {
            "name": "Lowest Common Ancestor of a Binary Tree",
            "difficulty": "Medium",
            "pattern": "Post-Order DFS / Ancestor Bubble-Up",
            "summary": "Find lowest node having both p and q as descendants.",
        },
        {
            "name": "Top K Frequent Elements",
            "difficulty": "Medium",
            "pattern": "Min-Heap of Size K / Bucket Sort",
            "summary": "Return k most frequent elements in array in better than O(N log N) time.",
        },
        {
            "name": "Find Median from Data Stream",
            "difficulty": "Hard",
            "pattern": "Dual Heap Balancing (Max-Heap + Min-Heap)",
            "summary": "Maintain continuous stream median in O(log N) insertion and O(1) retrieval.",
        },
    ],
}

TOPIC_ALIASES: Dict[str, str] = {
    "dp": "dynamic_programming",
    "dynamic programming": "dynamic_programming",
    "knapsack": "dynamic_programming",
    "memoization": "dynamic_programming",
    "tabulation": "dynamic_programming",
    "graph": "graphs",
    "graphs": "graphs",
    "bfs": "graphs",
    "dfs": "graphs",
    "dijkstra": "graphs",
    "topological": "graphs",
    "binary search": "binary_search",
    "binary_search": "binary_search",
    "bs": "binary_search",
    "tree": "trees_and_heaps",
    "trees": "trees_and_heaps",
    "heap": "trees_and_heaps",
    "heaps": "trees_and_heaps",
    "trees and heaps": "trees_and_heaps",
    "trees_and_heaps": "trees_and_heaps",
    "priority queue": "trees_and_heaps",
    "bst": "trees_and_heaps",
}


def normalize_topic(raw_topic: str) -> str:
    """Normalizes informal topic names or abbreviations into canonical topic keys."""
    cleaned = (raw_topic or "").strip().lower().replace("-", " ").replace("_", " ")
    cleaned_no_spaces = cleaned.replace(" ", "")

    if cleaned in TOPIC_ALIASES:
        return TOPIC_ALIASES[cleaned]

    for alias, canonical in TOPIC_ALIASES.items():
        if alias in cleaned or alias.replace(" ", "") in cleaned_no_spaces:
            return canonical

    return "dynamic_programming"


# ============================================================================
# Tool 1: suggest_problem
# ============================================================================


def suggest_problem(topic: str) -> Dict[str, Any]:
    """Returns a suggested competitive programming / DSA problem for a topic."""
    canonical_topic = normalize_topic(topic)
    logger.info("Executing tool 'suggest_problem' for topic '%s' (normalized: '%s')", topic, canonical_topic)
    problems = CURATED_PROBLEMS.get(canonical_topic, CURATED_PROBLEMS["dynamic_programming"])

    # Highlight primary suggested problem and provide all available options
    primary_suggestion = problems[0]

    return {
        "status": "success",
        "topic": canonical_topic,
        "suggested_problem": f"{primary_suggestion['name']} - {primary_suggestion['difficulty']}",
        "problem_name": primary_suggestion["name"],
        "difficulty": primary_suggestion["difficulty"],
        "pattern": primary_suggestion["pattern"],
        "summary": primary_suggestion["summary"],
        "curated_options": [
            f"{p['name']} ({p['difficulty']}) — {p['pattern']}" for p in problems
        ],
    }


# ============================================================================
# Tool 2: get_weak_topics
# ============================================================================

STRUGGLE_KEYWORDS = [
    "confused",
    "don't understand",
    "dont understand",
    "stuck",
    "struggling",
    "hard",
    "wrong answer",
    "wa",
    "tle",
    "time limit",
    "runtime error",
    "fail",
    "difficult",
    "help",
    "lost",
]

TOPIC_KEYWORDS = {
    "dynamic_programming": ["dp", "knapsack", "dynamic programming", "memoization", "tabulation", "subproblem"],
    "graphs": ["graph", "bfs", "dfs", "dijkstra", "cycle", "topological", "edges", "vertices"],
    "binary_search": ["binary search", "search range", "bsearch", "monotonic", "log n"],
    "trees_and_heaps": ["tree", "trees", "heap", "heaps", "priority queue", "bst", "root", "ancestor"],
}


def get_weak_topics() -> Dict[str, Any]:
    """Analyzes message history & submission errors to identify weak topics."""
    messages = db.get_all_messages_content()
    submissions = db.list_submissions(limit=100)
    logger.info(
        "Executing tool 'get_weak_topics': analyzing %d message(s) and %d submission(s)",
        len(messages),
        len(submissions),
    )

    # Initialize statistics
    topic_stats: Dict[str, Dict[str, int]] = {
        topic: {"mentions": 0, "struggles": 0, "failed_submissions": 0, "accepted_submissions": 0}
        for topic in CURATED_PROBLEMS.keys()
    }

    # 1. Analyze historical chat messages
    for msg in messages:
        msg_lower = msg.lower()
        has_struggle = any(k in msg_lower for k in STRUGGLE_KEYWORDS)

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", msg_lower) for kw in keywords):
                topic_stats[topic]["mentions"] += 1
                if has_struggle:
                    topic_stats[topic]["struggles"] += 1

    # 2. Analyze recorded submissions
    for sub in submissions:
        sub_topic = normalize_topic(sub.get("topic", ""))
        verdict = (sub.get("verdict") or "").lower()
        if sub_topic in topic_stats:
            if "accept" in verdict or "ac" == verdict:
                topic_stats[sub_topic]["accepted_submissions"] += 1
            else:
                topic_stats[sub_topic]["failed_submissions"] += 1

    # 3. Score and rank weak topics
    ranked_weakness = []
    for topic, stats in topic_stats.items():
        score = (
            (stats["struggles"] * 3.0)
            + (stats["failed_submissions"] * 4.0)
            - (stats["accepted_submissions"] * 2.0)
        )
        ranked_weakness.append((score, stats["mentions"], topic))

    # Sort: highest weakness score first, then least mentions
    ranked_weakness.sort(key=lambda x: (x[0], -x[1]), reverse=True)

    weak_topics_list = []
    for score, mentions, topic in ranked_weakness:
        stats = topic_stats[topic]
        reason_parts = []
        if stats["struggles"] > 0:
            reason_parts.append(f"{stats['struggles']} struggle/confusion mention(s)")
        if stats["failed_submissions"] > 0:
            reason_parts.append(f"{stats['failed_submissions']} failed submission(s)")
        if mentions == 0:
            reason_parts.append("Never practiced or discussed yet (Least Practiced)")
        elif mentions <= 1 and stats["struggles"] == 0:
            reason_parts.append("Very low practice volume")

        reason = ", ".join(reason_parts) if reason_parts else "Moderate confidence"
        weak_topics_list.append({
            "topic": topic,
            "weakness_score": round(score, 2),
            "reason": reason,
            "stats": stats,
        })

    primary_weak_topic = weak_topics_list[0]["topic"] if weak_topics_list else "dynamic_programming"

    return {
        "status": "success",
        "primary_weak_topic": primary_weak_topic,
        "weak_topics": weak_topics_list,
        "topic_stats": topic_stats,
        "total_messages_analyzed": len(messages),
        "total_submissions_analyzed": len(submissions),
        "recommendation": f"Focus practice on '{primary_weak_topic}' to solidify algorithmic fundamentals.",
    }


# ============================================================================
# Tool 3: log_submission
# ============================================================================


def log_submission(problem: str, topic: str, verdict: str) -> Dict[str, Any]:
    """Logs a problem submission record into SQLite database."""
    clean_problem = (problem or "").strip()
    if not clean_problem:
        raise ValueError("Problem name must be specified.")

    clean_topic = normalize_topic(topic)
    raw_verdict = (verdict or "").strip()

    # Standardize verdict casing
    v_lower = raw_verdict.lower()
    if "accept" in v_lower or v_lower in ("ac", "pass", "passed", "solved"):
        standard_verdict = "Accepted"
    elif "wrong" in v_lower or v_lower in ("wa", "fail", "failed"):
        standard_verdict = "Wrong Answer"
    elif "time" in v_lower or "tle" in v_lower:
        standard_verdict = "Time Limit Exceeded"
    elif "memory" in v_lower or "mle" in v_lower:
        standard_verdict = "Memory Limit Exceeded"
    elif "runtime" in v_lower or "re" in v_lower or "error" in v_lower:
        standard_verdict = "Runtime Error"
    else:
        standard_verdict = raw_verdict.title() if raw_verdict else "Accepted"

    submission = db.add_submission(
        problem=clean_problem,
        topic=clean_topic,
        verdict=standard_verdict,
    )

    logger.info(
        "Logged submission: ID=%s, Problem='%s', Topic='%s', Verdict='%s'",
        submission["id"],
        submission["problem"],
        submission["topic"],
        submission["verdict"],
    )

    return {
        "status": "success",
        "id": submission["id"],
        "problem": submission["problem"],
        "topic": submission["topic"],
        "verdict": submission["verdict"],
        "created_at": submission["created_at"],
        "message": f"Successfully logged submission for '{submission['problem']}' ({submission['topic']}) with verdict '{submission['verdict']}'.",
    }


# ============================================================================
# Tool Schemas for Groq / OpenAI Function Calling API
# ============================================================================

TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "suggest_problem",
            "description": "Suggests a curated competitive programming / DSA practice problem for a specified topic (dynamic_programming, graphs, binary_search, trees_and_heaps) along with its difficulty, pattern, and summary. Call this whenever the user asks for a problem recommendation, practice problem, or topic challenge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The DSA topic area. Must be one of: 'dynamic_programming', 'graphs', 'binary_search', 'trees_and_heaps'.",
                        "enum": ["dynamic_programming", "graphs", "binary_search", "trees_and_heaps"],
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weak_topics",
            "description": "Analyzes the student's past conversation history, struggle keywords ('confused', 'stuck', 'don't understand'), and recorded submissions to identify weak topics and least-practiced areas. Call this whenever the user asks about their weaknesses, what to study next, progress review, or personalized practice recommendations.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_submission",
            "description": "Logs a competitive programming submission or problem solving result into the persistent SQLite database. Call this whenever the user mentions solving, attempting, submitting, or getting a verdict (e.g. 'Accepted', 'Wrong Answer', 'TLE') on any problem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "Name or title of the DSA problem (e.g. '0/1 Knapsack', 'Two Sum', 'Course Schedule', 'Coin Change').",
                    },
                    "topic": {
                        "type": "string",
                        "description": "The primary DSA topic (e.g. 'dynamic_programming', 'graphs', 'binary_search', 'trees_and_heaps', 'arrays', 'strings').",
                    },
                    "verdict": {
                        "type": "string",
                        "description": "Submission outcome or verdict (e.g. 'Accepted', 'Wrong Answer', 'Time Limit Exceeded', 'Runtime Error', 'In Progress').",
                    },
                },
                "required": ["problem", "topic", "verdict"],
            },
        },
    },
]

AVAILABLE_TOOLS = {
    "suggest_problem": suggest_problem,
    "get_weak_topics": get_weak_topics,
    "log_submission": log_submission,
}


def execute_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Executes a registered tool by name with provided arguments."""
    clean_name = (name or "").strip()
    args = arguments or {}

    if not clean_name:
        logger.error("Attempted to execute tool with empty name")
        return {"status": "error", "message": "Tool name cannot be empty."}

    if clean_name not in AVAILABLE_TOOLS:
        logger.error("Attempted to execute unknown tool '%s'", clean_name)
        return {
            "status": "error",
            "message": f"Unknown tool '{clean_name}'. Available tools: {list(AVAILABLE_TOOLS.keys())}",
        }

    tool_func = AVAILABLE_TOOLS[clean_name]
    logger.info(">>> TOOL CALLED: '%s' with arguments: %s", clean_name, args)

    try:
        result = tool_func(**args)
        logger.info(">>> TOOL COMPLETED [%s]: status=%s", clean_name, result.get("status", "done"))
        return result
    except Exception as e:
        logger.error(">>> TOOL ERROR: Tool '%s' execution failed: %s", clean_name, e, exc_info=True)
        return {"status": "error", "tool": clean_name, "message": str(e)}


class ToolExecutionRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Registered tool name to execute")
    arguments: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Arguments dictionary passed to the tool function",
    )


@router.get("")
async def list_tools_endpoint():
    """Returns catalog of registered tools and schemas for Day 5 tool calling."""
    return {
        "status": "online",
        "tools": list(AVAILABLE_TOOLS.keys()),
        "schemas": TOOLS_SCHEMA,
    }


@router.post("/execute")
async def execute_tool_endpoint(body: ToolExecutionRequest):
    """Executes a tool by name with provided arguments, returning clean structured results."""
    tool_name = body.name.strip()
    if not tool_name:
        raise HTTPException(status_code=400, detail="Tool name cannot be empty or whitespace.")

    if tool_name not in AVAILABLE_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(AVAILABLE_TOOLS.keys())}",
        )

    result = execute_tool(tool_name, body.arguments)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Tool execution error."))
    return result


