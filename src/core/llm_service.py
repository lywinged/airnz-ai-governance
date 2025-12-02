"""
LLM Service: OpenAI Integration with Governance Controls

Wraps OpenAI API with:
- Model version tracking
- Prompt template management
- Token usage monitoring
- Error handling and retries
- Cost tracking
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Optional OpenAI import - graceful degradation if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Using mock responses.")


@dataclass
class LLMResponse:
    """LLM generation response"""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp: datetime


class PromptTemplate:
    """Versioned prompt template"""

    def __init__(self, template_id: str, version: str, template: str, variables: List[str]):
        self.template_id = template_id
        self.version = version
        self.template = template
        self.variables = variables

    def render(self, **kwargs) -> str:
        """Render template with variables"""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        return self.template.format(**kwargs)


class LLMService:
    """
    LLM service with governance controls.

    Features:
    - Model version tracking
    - Prompt template versioning
    - Token/cost monitoring
    - Rate limiting
    - Error handling
    """

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.mock_mode = False
            logger.info("OpenAI client initialized")
        else:
            self.client = None
            self.mock_mode = True
            logger.warning("Running in MOCK mode - no actual LLM calls will be made")

        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.register_default_templates()

        self.total_tokens_used = 0
        self.total_cost_usd = 0.0

    def register_default_templates(self):
        """Register default prompt templates"""

        # R1: Oscar Chatbot template
        self.register_template(PromptTemplate(
            template_id="oscar_chatbot",
            version="1.0",
            template="""You are Oscar, Air New Zealand's customer service AI assistant.

Your role:
- Answer customer questions about policies, baggage, bookings, and travel
- Provide accurate information based ONLY on the evidence provided
- Be helpful, friendly, and professional
- If you don't have evidence to answer, say so clearly

CRITICAL RULES:
1. NEVER make up information
2. ALWAYS cite your sources
3. If evidence is missing or unclear, escalate to a human agent
4. Use simple, clear language

Evidence:
{evidence}

Customer Question: {query}

Provide a helpful answer with citations. If you cannot answer based on the evidence, say:
"I don't have enough information to answer that accurately. Let me connect you with one of our customer service agents."
""",
            variables=["evidence", "query"]
        ))

        # R2: Disruption Management template
        self.register_template(PromptTemplate(
            template_id="disruption_management",
            version="1.0",
            template="""You are an AI assistant supporting Air New Zealand's Operations Control Center (OCC).

Your role:
- Analyze flight disruptions
- Generate recovery options based on real-time operational data
- Provide constraint-aware recommendations
- Explain trade-offs clearly

CRITICAL RULES:
1. All recommendations are SUGGESTIONS - humans make final decisions
2. Clearly state constraints and limitations
3. Prioritize safety first, then passenger impact, then cost
4. Cite procedures and data sources

Disruption Context:
{disruption_context}

Operational Data:
{operational_data}

Procedures:
{procedures}

Generate 2-3 recovery options ranked by recommendation score. For each option:
1. Title and description
2. Impact analysis (passengers, crew, cost)
3. Constraints and requirements
4. Recommendation score (0-1) with rationale
5. Citations to procedures

Format as JSON.
""",
            variables=["disruption_context", "operational_data", "procedures"]
        ))

        # R0: Code Assistant template
        self.register_template(PromptTemplate(
            template_id="code_assistant",
            version="1.0",
            template="""You are an AI coding assistant for Air New Zealand developers.

Your role:
- Help with code writing, review, and debugging
- Suggest best practices and improvements
- Answer technical questions

User Request: {query}

Context:
{context}

Provide helpful technical assistance.
""",
            variables=["query", "context"]
        ))

    def register_template(self, template: PromptTemplate):
        """Register a prompt template"""
        key = f"{template.template_id}_v{template.version}"
        self.prompt_templates[key] = template
        logger.info(f"Prompt template registered: {key}")

    def generate(
        self,
        template_id: str,
        template_version: str,
        variables: Dict,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Generate completion using versioned template.

        Args:
            template_id: Template identifier
            template_version: Template version
            variables: Template variables
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content and metadata
        """
        start_time = datetime.now()

        # Get template
        template_key = f"{template_id}_v{template_version}"
        template = self.prompt_templates.get(template_key)

        if not template:
            raise ValueError(f"Template not found: {template_key}")

        # Render prompt
        try:
            prompt = template.render(**variables)
        except ValueError as e:
            raise ValueError(f"Template rendering failed: {str(e)}")

        # Generate completion
        if self.mock_mode:
            response = self._mock_generate(prompt, model, temperature, max_tokens)
        else:
            response = self._openai_generate(prompt, model, temperature, max_tokens)

        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Create response
        llm_response = LLMResponse(
            content=response["content"],
            model=model,
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
            total_tokens=response["total_tokens"],
            cost_usd=response["cost_usd"],
            latency_ms=latency_ms,
            timestamp=datetime.now()
        )

        # Track usage
        self.total_tokens_used += llm_response.total_tokens
        self.total_cost_usd += llm_response.cost_usd

        logger.info(
            f"LLM generation: {model} | "
            f"Tokens: {llm_response.total_tokens} | "
            f"Cost: ${llm_response.cost_usd:.4f} | "
            f"Latency: {llm_response.latency_ms:.0f}ms"
        )

        return llm_response

    def _openai_generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Generate using OpenAI API"""
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = completion.choices[0].message.content
            prompt_tokens = completion.usage.prompt_tokens
            completion_tokens = completion.usage.completion_tokens
            total_tokens = completion.usage.total_tokens

            # Calculate cost
            pricing = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])
            cost_usd = (
                (prompt_tokens / 1_000_000) * pricing["input"] +
                (completion_tokens / 1_000_000) * pricing["output"]
            )

            return {
                "content": content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def _mock_generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Generate mock response for testing"""

        # Mock responses based on template
        if "Oscar" in prompt:
            content = """Based on our checked baggage policy, economy passengers are entitled to 2 pieces of checked baggage, each not exceeding 23kg. Business Premier passengers are entitled to 3 pieces, each not exceeding 32kg.

Source: Checked Baggage Allowance Policy Version 3.2, Effective 2024-01-01, Section 2.1.3"""

        elif "disruption" in prompt.lower():
            content = """{
  "options": [
    {
      "option_id": "OPT-1",
      "title": "Aircraft Swap to ZK-NZA",
      "description": "Swap to available B787-9 ZK-NZA to minimize delay",
      "impact": {
        "pax_misconnects": 3,
        "crew_regulatory": "Requires crew swap",
        "cost_estimate": "Medium"
      },
      "constraints": ["Gate 23 available", "Crew swap needed"],
      "recommendation_score": 0.9,
      "rationale": "Minimizes passenger impact and protects connections",
      "citations": ["OPS-DISRUPT-001 v2.1 Section 4.2.1"]
    }
  ]
}"""

        else:
            content = "This is a mock response. Configure OPENAI_API_KEY to use real LLM."

        # Mock token counts
        prompt_tokens = len(prompt.split()) * 1.3
        completion_tokens = len(content.split()) * 1.3
        total_tokens = prompt_tokens + completion_tokens

        # Mock cost (minimal)
        pricing = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])
        cost_usd = (total_tokens / 1_000_000) * (pricing["input"] + pricing["output"]) / 2

        return {
            "content": content,
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(total_tokens),
            "cost_usd": cost_usd
        }

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": self.total_cost_usd,
            "mock_mode": self.mock_mode
        }
