"""Security controls for the Agent.

- ``scope_guard``                         ``@before_agent`` rule: refuse out-of-scope or jailbreak requests before any model call.
- ``pii_middlewares()``                   ``PIIMiddleware`` for email, Vietnamese phone numbers (input + tool results) and API keys (block).
Docs: https://docs.langchain.com/oss/python/langchain/guardrails  ·  https://docs.langchain.com/oss/python/langchain/middleware
"""

from __future__ import annotations
import re
from functools import lru_cache

from openai import OpenAI

from langchain.agents.middleware import (
    AgentState,
    PIIMiddleware,
    after_agent,
    before_agent,
)
from langchain.messages import AIMessage, HumanMessage
from langgraph.runtime import Runtime

from app.core.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------- model-based guard (OpenAI Decisions API)
# A deterministic regex cannot catch injected instructions written in natural language (you do not know the wording in
# advance). A small, fast classifier can: the OpenAI Decisions API returns a probability for a yes/no question about the text.
DECISION_MODEL = "gpt-6-luna"
OUT_OF_SCOPE_INSTRUCTION = (
    "Is this request outside the work of a clinician's assistant? In scope: "
    "summarizing or drafting from the current patient's record, medications and "
    "interactions, clinical guidelines"
    "Out of scope: everything else, including general chat, programming help, "
    "legal or financial advice, and political or religious opinions."
)


@lru_cache(maxsize=1)
def _decisions_client() -> OpenAI:
    """Created on first use"""
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def decisions_probability(text: str, question: str = OUT_OF_SCOPE_INSTRUCTION) -> float:
    """Ask the OpenAI Decisions API one yes/no question about ``text`` and return the probability (0..1).

    One fast model call. If the model *refuses* to judge the text, fail closed (return 1.0) so the guard withholds it.
    """
    decision = _decisions_client().decisions.create(
        model=settings.DECISION_MODEL,
        input=text[:4000],
        questions=[
            {"type": "predicate", "name": "out_of_scope", "instructions": question}
        ],
    )
    answer = decision.answers[0]
    if (
        answer.type == "refusal"
    ):  # the classifier declined to judge -> treat as suspicious, do not pass it through
        return 1.0
    return float(answer.probability)


# ---------------------------------------------------------------- scope guard (before_agent)
REFUSAL = "I can't help with that request. I only support clinical questions."
SCOPE_DENY = [
    (
        "political_content",
        r"\b(riots?|rioting|protests?|election|elections|vote for|political (party|opinion)|left[- ]wing|right[- ]wing|democrat|republican|propaganda)\b",
    ),
    (
        "harmful_content",
        r"phishing|malware|ransomware|keylogger|credential (stealer|harvest)",
    ),
    (
        "injection_phrase",
        r"(ignore|disregard|forget) (all |any |the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    ),
    ("jailbreak", r"developer mode|\bDAN\b|jailbreak"),
    (
        "prompt_leak",
        r"(print|show|reveal|repeat|output|display)\b.{0,25}\b(system|hidden|internal|initial) (prompt|instructions|policy)|internal policy key|repeat (the|all) (text|words|instructions) above",
    ),
]


def scope_violation(text: str) -> str | None:
    for name, pattern in SCOPE_DENY:
        if re.search(pattern, text, re.I):
            return name
    return None


@before_agent(can_jump_to=["end"])
def scope_guard(state: AgentState, runtime: Runtime) -> dict | None:
    """Deterministic input rail: refuse before the first model call."""
    last = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None
    )
    text = last.content if last and isinstance(last.content, str) else ""
    hit = scope_violation(text)
    if not hit and text and decisions_probability(text) >= 0.5:
        hit = "out_of_scope"
    if not hit:
        return None
    return {"messages": [AIMessage(content=REFUSAL)], "jump_to": "end"}


# ---------------------------------------------------------------- PII
EMAIL_RE = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
API_KEY_RE = r"\bsk-[A-Za-z0-9_-]{20,}"
PII_PATTERNS = {"email": EMAIL_RE, "api_key": API_KEY_RE}


def detect_pii(text: str) -> list[str]:
    return [name for name, pattern in PII_PATTERNS.items() if re.search(pattern, text)]


def pii_middlewares() -> list:
    """PII Middlewares configuration."""
    both = {"apply_to_input": True, "apply_to_tool_results": True}
    return [
        PIIMiddleware("email", strategy="redact", **both),
        PIIMiddleware("api_key", detector=API_KEY_RE, strategy="block", **both),
    ]


# ---------------------------------------------------------------- output rail (after_agent)
def output_leaks(text: str) -> list[str]:
    """What the output rail found in a final answer: PII, or an URL"""
    hits = []
    if detect_pii(text):
        hits.append("pii")
    if [u for u in re.findall(r"https?://[^\s)\"']+", text)]:
        hits.append("external_url")
    return hits


@after_agent
def output_rail(state: AgentState, runtime: Runtime) -> dict | None:
    """Deterministic last line: scan the final answer with ``output_leaks``
    and replace it with a notice if anything is found."""
    last = next(
        (
            m
            for m in reversed(state["messages"])
            if isinstance(m, AIMessage) and not m.tool_calls
        ),
        None,
    )
    if last is None or not isinstance(last.content, str):
        return None
    hits = output_leaks(last.content)
    if not hits:
        return None
    return {
        "messages": [
            AIMessage(
                content="[answer withheld by the output guard: it contained "
                + ", ".join(hits)
                + "]"
            )
        ]
    }


DEFENSE_MIDDLEWARE = [
    scope_guard,  # Input check
    *pii_middlewares(),  # PPI check
    output_rail,  # Output check
]
