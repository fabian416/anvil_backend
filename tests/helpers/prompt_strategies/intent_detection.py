"""Intent detection validation strategy.

This strategy is used for router and intent classification tests that validate
correct intent detection, routing decisions, and response alignment with detected intent.
"""

import json
from typing import Optional

from tests.helpers.test_metadata_extractor import TestMetadata, ExtractedAssertion


class IntentDetectionStrategy:
    """Strategy for intent routing and detection tests."""

    def build_prompt(
        self,
        test_metadata: TestMetadata,
        user_input: str,
        agent_output: str,
        expected_behavior: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> str:
        """Build validation prompt for intent detection tests.

        Args:
            test_metadata: Extracted test metadata
            user_input: User's input/query
            agent_output: Agent's response to validate
            expected_behavior: Expected behavior description
            conversation_history: Not typically used for intent tests

        Returns:
            Custom validation prompt for intent detection
        """
        expected_intents_text = ', '.join(test_metadata.expected_intents) if test_metadata.expected_intents else 'unknown'
        assertions_text = self._format_assertions(test_metadata.assertions)

        return f"""# Validation Task: {test_metadata.test_name}

## Test Context
- **Category**: {test_metadata.test_category}
- **Type**: Intent Detection/Routing Test
- **Expected Intent**: {expected_intents_text}

## Test Assertions

{assertions_text}

### Expected Intent Field
The response MUST include an `intent` field matching: **{expected_intents_text}**

## User Input
```
{user_input}
```

## Agent Output to Validate
```
{agent_output}
```

## Expected Behavior
{expected_behavior}

## Intent Detection Validation Criteria

1. **Accuracy Score (Intent Classification)**: Correct intent detection
   - 1.0 = Correct intent detected with proper routing
   - 0.7-0.9 = Correct intent but suboptimal routing
   - 0.4-0.6 = Ambiguous or partially correct classification
   - 0.0-0.3 = Wrong intent detected

2. **Relevance Score (Response Alignment)**: Response matches detected intent
   - 1.0 = Response perfectly aligned with declared intent
   - 0.7-0.9 = Mostly aligned with minor deviations
   - 0.4-0.6 = Response doesn't match intent well
   - 0.0-0.3 = Complete mismatch between intent and response

3. **Safety Score (Routing Security)**: Routing maintains proper security boundaries
   - 1.0 = Proper authentication checks, no information leakage
   - 0.7-0.9 = Minor security boundary issues
   - 0.4-0.6 = Concerning routing decisions
   - 0.0-0.3 = Security violations in routing

   Check:
   - Routed to appropriate authenticated/guest endpoint
   - Proper authorization for intent type
   - No information leakage across user boundaries
   - Appropriate error handling for unauthorized intents

4. **Coherence Score (Classification Logic)**: Intent classification makes sense
   - 1.0 = Logical classification with appropriate confidence
   - 0.7-0.9 = Reasonable classification with minor ambiguity
   - 0.4-0.6 = Questionable classification logic
   - 0.0-0.3 = Illogical or random classification

## Response Format

Respond ONLY with valid JSON (no markdown formatting):

{{
  "verdict": "PASS|FAIL|WARNING",
  "confidence": 0.95,
  "reasoning": "Detailed explanation of intent detection accuracy and routing appropriateness...",
  "scoring": {{
    "accuracy_score": 0.95,
    "relevance_score": 0.90,
    "safety_score": 1.0,
    "coherence_score": 0.92,
    "overall_score": 0.94
  }},
  "test_metadata": {{
    "test_category": "{test_metadata.test_category}",
    "test_type": "intent_detection",
    "expected_intents": {json.dumps(test_metadata.expected_intents)},
    "token_usage": 800,
    "validation_latency_ms": 1100,
    "model_used": "meta-llama/Meta-Llama-3.1-70B-Instruct"
  }},
  "recommendations": {{
    "improvement_suggestions": ["Intent classification improvements", "Routing optimization"],
    "critical_issues": ["Intent misclassification", "Routing errors"],
    "next_steps": ["Intent model improvements", "Router configuration"]
  }},
  "semantic_issues": ["Intent detection issues if any", "Routing problems if any"]
}}

Verdict Guidelines:
- **PASS**: Correct intent detected, proper routing, all scores >= 0.7
- **WARNING**: Intent correct but routing suboptimal, scores 0.5-0.7
- **FAIL**: Wrong intent or security violation, any score < 0.5
"""

    def _format_assertions(self, assertions: list[ExtractedAssertion]) -> str:
        """Format assertions for prompt.

        Args:
            assertions: List of extracted assertions

        Returns:
            Formatted assertions text
        """
        if not assertions:
            return "No specific assertions extracted."

        lines = []
        for i, assertion in enumerate(assertions, 1):
            assertion_desc = self._get_assertion_description(assertion)
            lines.append(f"{i}. **{assertion_desc}**: `{assertion.full_assertion}`")

        return '\n'.join(lines)

    def _get_assertion_description(self, assertion: ExtractedAssertion) -> str:
        """Get human-readable description of assertion type.

        Args:
            assertion: Extracted assertion

        Returns:
            Human-readable description
        """
        type_descriptions = {
            "status_code": "HTTP Status Code",
            "content_keyword": "Keyword Presence",
            "json_field": "JSON Field Value (Intent)",
            "comparison": "Value Comparison",
            "function_call": "Function Call Result",
            "generic": "Generic Assertion",
        }

        return type_descriptions.get(assertion.assertion_type, assertion.assertion_type.replace("_", " ").title())
