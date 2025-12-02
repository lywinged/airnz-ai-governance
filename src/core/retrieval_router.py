"""
Retrieval Router: Multi-strategy RAG with Intent Detection

Routes queries to appropriate retrieval strategy:
- Policy/Procedure: Hybrid (keyword + vector) + rerank
- Real-time Truth: Tool-RAG (authoritative systems)
- Relationship: Graph-RAG (component → fault → work card)
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Available retrieval strategies"""
    HYBRID_RAG = "hybrid_rag"           # Keyword + vector + rerank
    TOOL_RAG = "tool_rag"               # Authoritative system tools
    GRAPH_RAG = "graph_rag"             # Knowledge graph traversal
    SQL_RAG = "sql_rag"                 # Structured data queries
    FALLBACK = "fallback"               # When no strategy matches


class QueryIntent(Enum):
    """Detected query intent"""
    POLICY_LOOKUP = "policy_lookup"           # "What is the baggage policy?"
    PROCEDURE_LOOKUP = "procedure_lookup"     # "How do I perform MEL check?"
    REAL_TIME_STATUS = "real_time_status"     # "What's the status of NZ1?"
    TROUBLESHOOTING = "troubleshooting"       # "Engine fault code 1234"
    HISTORICAL_LOOKUP = "historical_lookup"   # "Previous maintenance on ZK-ABC"
    CALCULATION = "calculation"               # "Calculate fuel for AKL-SYD"
    GENERAL_KNOWLEDGE = "general_knowledge"   # General questions


@dataclass
class QueryContext:
    """Context for query routing"""
    query: str
    user_id: str
    role: str
    business_domain: str
    risk_tier: str
    session_id: str
    timestamp: datetime


@dataclass
class RetrievalResult:
    """Result from retrieval operation"""
    strategy: RetrievalStrategy
    intent: QueryIntent
    results: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime


class IntentDetector:
    """
    Detect query intent to route to appropriate retrieval strategy.

    Uses a combination of:
    - Keyword patterns
    - Question type analysis
    - Domain-specific indicators
    """

    def __init__(self):
        self.intent_patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[QueryIntent, List[str]]:
        """Initialize intent detection patterns"""
        return {
            QueryIntent.POLICY_LOOKUP: [
                "policy", "rule", "regulation", "allowed", "permitted",
                "baggage", "fare", "cancellation", "refund"
            ],
            QueryIntent.PROCEDURE_LOOKUP: [
                "how to", "procedure", "step", "process", "checklist",
                "perform", "execute", "carry out"
            ],
            QueryIntent.REAL_TIME_STATUS: [
                "status", "current", "now", "today", "flight",
                "gate", "departure", "arrival", "delay"
            ],
            QueryIntent.TROUBLESHOOTING: [
                "fault", "error", "code", "troubleshoot", "diagnose",
                "issue", "problem", "not working"
            ],
            QueryIntent.HISTORICAL_LOOKUP: [
                "history", "previous", "past", "last time", "when did",
                "maintenance history", "work order"
            ],
            QueryIntent.CALCULATION: [
                "calculate", "compute", "how much", "how many",
                "fuel", "weight", "balance"
            ],
        }

    def detect_intent(self, query: str) -> QueryIntent:
        """
        Detect intent from query text.

        Args:
            query: User query

        Returns:
            Detected QueryIntent
        """
        query_lower = query.lower()
        scores = {}

        # Score each intent based on pattern matches
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            scores[intent] = score

        # Return highest scoring intent
        if max(scores.values()) > 0:
            detected_intent = max(scores, key=scores.get)
            logger.info(f"Intent detected: {detected_intent.value} for query: {query[:100]}")
            return detected_intent

        # Default to general knowledge
        logger.info(f"No specific intent detected, defaulting to general_knowledge")
        return QueryIntent.GENERAL_KNOWLEDGE


class RetrievalRouter:
    """
    Routes queries to appropriate retrieval strategy based on intent.

    Key principles:
    - Real-time data MUST come from authoritative tools (not stale docs)
    - Policy/procedure answers need version-tracked evidence
    - Troubleshooting benefits from graph relationships
    """

    def __init__(self):
        self.intent_detector = IntentDetector()
        self.strategy_map = self._initialize_strategy_map()

    def _initialize_strategy_map(self) -> Dict[QueryIntent, RetrievalStrategy]:
        """Map intents to retrieval strategies"""
        return {
            QueryIntent.POLICY_LOOKUP: RetrievalStrategy.HYBRID_RAG,
            QueryIntent.PROCEDURE_LOOKUP: RetrievalStrategy.HYBRID_RAG,
            QueryIntent.REAL_TIME_STATUS: RetrievalStrategy.TOOL_RAG,
            QueryIntent.TROUBLESHOOTING: RetrievalStrategy.GRAPH_RAG,
            QueryIntent.HISTORICAL_LOOKUP: RetrievalStrategy.TOOL_RAG,
            QueryIntent.CALCULATION: RetrievalStrategy.TOOL_RAG,
            QueryIntent.GENERAL_KNOWLEDGE: RetrievalStrategy.HYBRID_RAG,
        }

    def route_query(self, context: QueryContext) -> tuple[RetrievalStrategy, QueryIntent]:
        """
        Route query to appropriate retrieval strategy.

        Args:
            context: Query context

        Returns:
            Tuple of (strategy, intent)
        """
        # Detect intent
        intent = self.intent_detector.detect_intent(context.query)

        # Map to strategy
        strategy = self.strategy_map.get(intent, RetrievalStrategy.FALLBACK)

        logger.info(
            f"Query routed: intent={intent.value}, strategy={strategy.value}, "
            f"query='{context.query[:100]}...'"
        )

        return strategy, intent

    def retrieve(
        self,
        context: QueryContext,
        retrievers: Dict[RetrievalStrategy, Any]
    ) -> RetrievalResult:
        """
        Execute retrieval using appropriate strategy.

        Args:
            context: Query context
            retrievers: Dictionary of retriever implementations

        Returns:
            RetrievalResult with results and metadata
        """
        strategy, intent = self.route_query(context)

        # Get appropriate retriever
        retriever = retrievers.get(strategy)
        if not retriever:
            logger.error(f"No retriever available for strategy {strategy.value}")
            return RetrievalResult(
                strategy=RetrievalStrategy.FALLBACK,
                intent=intent,
                results=[],
                confidence=0.0,
                metadata={"error": "No retriever available"},
                timestamp=datetime.now()
            )

        # Execute retrieval
        try:
            results = retriever.retrieve(context.query, context)
            confidence = self._calculate_confidence(results, strategy)

            return RetrievalResult(
                strategy=strategy,
                intent=intent,
                results=results,
                confidence=confidence,
                metadata={
                    "user_id": context.user_id,
                    "business_domain": context.business_domain,
                    "risk_tier": context.risk_tier,
                },
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Retrieval failed for strategy {strategy.value}: {str(e)}")
            return RetrievalResult(
                strategy=RetrievalStrategy.FALLBACK,
                intent=intent,
                results=[],
                confidence=0.0,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )

    def _calculate_confidence(
        self,
        results: List[Dict[str, Any]],
        strategy: RetrievalStrategy
    ) -> float:
        """
        Calculate confidence score for retrieval results.

        Args:
            results: Retrieved results
            strategy: Strategy used

        Returns:
            Confidence score (0-1)
        """
        if not results:
            return 0.0

        # Different strategies have different confidence calculations
        if strategy == RetrievalStrategy.TOOL_RAG:
            # Tool results are authoritative if they exist
            return 1.0 if results else 0.0

        elif strategy == RetrievalStrategy.HYBRID_RAG:
            # Average the scores from hybrid retrieval
            scores = [r.get("score", 0.0) for r in results]
            return sum(scores) / len(scores) if scores else 0.0

        elif strategy == RetrievalStrategy.GRAPH_RAG:
            # Consider path length and relationship strength
            avg_path_length = sum(r.get("path_length", 10) for r in results) / len(results)
            # Shorter paths = higher confidence
            return max(0.0, 1.0 - (avg_path_length / 10.0))

        return 0.5  # Default moderate confidence


class HybridRetriever:
    """
    Hybrid retrieval: keyword + vector + rerank.

    Used for policy, procedure, and manual lookups.
    """

    def __init__(self, vector_store, keyword_index, reranker):
        self.vector_store = vector_store
        self.keyword_index = keyword_index
        self.reranker = reranker

    def retrieve(self, query: str, context: QueryContext) -> List[Dict[str, Any]]:
        """
        Execute hybrid retrieval.

        Args:
            query: User query
            context: Query context

        Returns:
            List of retrieved documents with scores
        """
        # Simulate hybrid retrieval
        # In production, this would:
        # 1. Retrieve from vector store
        # 2. Retrieve from keyword index
        # 3. Merge results with RRF (Reciprocal Rank Fusion)
        # 4. Rerank with cross-encoder

        logger.info(f"Hybrid retrieval for: {query}")

        # Placeholder results
        return [
            {
                "document_id": "POL-001",
                "version": "2.1",
                "title": "Baggage Policy",
                "excerpt": "Passengers are allowed 2 checked bags...",
                "score": 0.85,
                "source": "policy_management"
            }
        ]


class ToolRetriever:
    """
    Tool-based retrieval for authoritative real-time data.

    Examples:
    - Flight status from ops system
    - Work order status from maintenance system
    - Crew availability from rostering system
    """

    def __init__(self, tool_registry):
        self.tool_registry = tool_registry

    def retrieve(self, query: str, context: QueryContext) -> List[Dict[str, Any]]:
        """
        Execute tool-based retrieval.

        Args:
            query: User query
            context: Query context

        Returns:
            Results from authoritative tools
        """
        logger.info(f"Tool retrieval for: {query}")

        # Placeholder - in production would invoke actual tools
        return [
            {
                "tool": "flight_status",
                "flight_number": "NZ1",
                "status": "On Time",
                "departure": "10:30",
                "gate": "23",
                "source": "ops_system",
                "score": 1.0  # Authoritative
            }
        ]


class GraphRetriever:
    """
    Graph-based retrieval for relationship queries.

    Examples:
    - Component → Fault → Work Card → Case History
    - Aircraft → System → Component → Procedure
    """

    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph

    def retrieve(self, query: str, context: QueryContext) -> List[Dict[str, Any]]:
        """
        Execute graph traversal retrieval.

        Args:
            query: User query
            context: Query context

        Returns:
            Related entities and paths from knowledge graph
        """
        logger.info(f"Graph retrieval for: {query}")

        # Placeholder - in production would traverse knowledge graph
        return [
            {
                "entity_type": "fault_code",
                "entity_id": "ENG-1234",
                "related_procedures": ["MEL-34-21", "TSM-76-12"],
                "path_length": 2,
                "source": "knowledge_graph",
                "score": 0.75
            }
        ]
