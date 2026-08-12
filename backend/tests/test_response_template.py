"""Batch 6 tests — the internal response-formatting template.

The prompt is what makes answers consistently structured and grounded, so its
load-bearing instructions are pinned here. These are contract tests on the
template text plus a behavioral check that composition is unchanged: the
Phase 11 grounding fix must not be re-opened by the formatting work.
"""
import re

from app.agent import agent_service
from app.agent.agent_service import SYSTEM_PROMPT
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call

# The prompt is hard-wrapped for readability, so assertions on sentences that
# span a line break are made against a whitespace-normalized copy.
FLAT_PROMPT = re.sub(r"\s+", " ", SYSTEM_PROMPT)


# --- Structure guidance ----------------------------------------------------


def test_prompt_defines_a_response_composition_section():
    assert "## Composing your final answer" in SYSTEM_PROMPT


def test_prompt_answers_the_question_first():
    assert "Answer the user's actual question first" in FLAT_PROMPT


def test_prompt_offers_the_analytical_structure():
    for heading in ("**Key finding**", "**What the data shows**", "**Takeaway**"):
        assert heading in SYSTEM_PROMPT


def test_prompt_does_not_force_headings_on_simple_questions():
    assert "Scale the structure to the question" in FLAT_PROMPT
    assert "no headings" in FLAT_PROMPT


def test_prompt_requests_markdown_and_readable_numbers():
    assert "Markdown" in SYSTEM_PROMPT
    assert "thousands separators" in FLAT_PROMPT


def test_prompt_preserves_numerical_accuracy():
    assert "Never alter a value's actual magnitude or precision" in FLAT_PROMPT


# --- Grounding / anti-fabrication -----------------------------------------


def test_prompt_forbids_inventing_data():
    assert "Never invent, estimate, or extrapolate data that was not returned" in FLAT_PROMPT


def test_prompt_forbids_mental_arithmetic():
    """A live run answered a "difference between highest and lowest" question
    with a wrong figure computed in-head; derived numbers must come from SQL."""
    assert "Do not do arithmetic in your head" in FLAT_PROMPT
    assert "run a query that computes it" in FLAT_PROMPT


def test_prompt_requires_intent_on_generate_chart():
    """Chart type is derived from `intent`; omitting it produced no chart."""
    assert "pass the user's original question as `intent`" in FLAT_PROMPT


def test_prompt_forbids_claiming_an_ungenerated_chart():
    assert "Do not claim a chart exists unless" in FLAT_PROMPT


def test_prompt_forbids_claiming_an_ungenerated_explanation():
    assert "Do not claim an explanation exists unless" in FLAT_PROMPT


def test_prompt_requires_answering_from_the_last_successful_result():
    """Reinforces the Phase 11 fix from the prompt side as well as in code."""
    assert "LAST successful result" in FLAT_PROMPT


def test_prompt_forbids_restating_sql_and_pasting_the_table():
    assert "never paste the table" in FLAT_PROMPT
    assert "restate the SQL query in prose" in FLAT_PROMPT


def test_prompt_forbids_exposing_internal_reasoning():
    assert "Do not expose your internal reasoning" in FLAT_PROMPT


def test_prompt_keeps_read_only_guidance():
    assert "The system is read-only." in SYSTEM_PROMPT


# --- Behavior is unchanged by the formatting work -------------------------


def test_single_query_answer_still_uses_the_models_own_text():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "SELECT 1 AS value"}, "c1"),
            final_answer("**Key finding**\n\nThe value is 1."),
        ]
    )
    response = agent_service.run_agent("tmpl-single", "one query", model=model)
    assert response.error is None
    # Structured markdown passes through untouched for the frontend to render.
    assert response.message == "**Key finding**\n\nThe value is 1."


def test_multi_query_grounding_fix_still_holds_after_template_change():
    """Phase 11 regression guard, re-asserted from the Batch 6 side."""
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "SELECT 111 AS value"}, "c1"),
            tool_call("execute_query", {"sql": "SELECT 999 AS value"}, "c2"),
            final_answer("The value is 111, from the first query."),
        ]
    )
    response = agent_service.run_agent("tmpl-multi", "two queries", model=model)
    assert response.sql == "SELECT 999 AS value"
    assert response.rows == [[999]]
    assert "111" not in response.message
