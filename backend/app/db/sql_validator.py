"""Read-only SQL guard (04_AGENT_TOOLS.md Tool 2 §8, TRD §5).

Deliberately a lightweight keyword/regex guard, NOT a full SQL parser
(Clarification 2). Its two hard requirements beyond rejecting destructive
statements are the false-positive cases:

  * `SELECT updated_at FROM orders`  must NOT trip the UPDATE rule
    (word-boundary matching, not substring search).
  * `SELECT 'delete' AS status`      must NOT trip the DELETE rule
    (quoted spans are masked before keywords are scanned).

This module is pure and deterministic: it performs no database I/O and
never calls an LLM, so it is unit-testable in isolation.
"""
import re
from dataclasses import dataclass

FORBIDDEN_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "REPLACE",
    "CREATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "GRANT",
    "REVOKE",
)

_LINE_COMMENT = re.compile(r"--[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


class SqlValidationError(ValueError):
    """Raised when a statement fails the read-only guard. User/agent-safe."""


@dataclass
class ValidatedSql:
    sql: str          # comment-stripped, trimmed, trailing semicolon removed
    has_limit: bool   # whether the statement already carries its own LIMIT


def strip_comments(sql: str) -> str:
    """Removes line and block comments. Comment markers inside quoted spans
    are preserved by masking quotes first, then mapping removals back."""
    masked = mask_quoted_spans(sql)

    removals: list[tuple[int, int]] = []
    for pattern in (_BLOCK_COMMENT, _LINE_COMMENT):
        for match in pattern.finditer(masked):
            removals.append((match.start(), match.end()))

    if not removals:
        return sql

    result = []
    cursor = 0
    for start, end in sorted(removals):
        if start < cursor:
            continue
        result.append(sql[cursor:start])
        result.append(" ")
        cursor = end
    result.append(sql[cursor:])
    return "".join(result)


def mask_quoted_spans(sql: str) -> str:
    """Replaces the *contents* of single-quoted literals, double-quoted
    identifiers, and backtick/bracket identifiers with a neutral filler,
    preserving the original string length and the quote delimiters.

    Length preservation lets callers map offsets in the masked string back
    onto the original. SQL's doubled-quote escape ('' inside a literal) is
    handled naturally: the escape closes and reopens a span, leaving the
    masked output still quote-balanced.
    """
    out = list(sql)
    index = 0
    length = len(sql)

    closing = {"'": "'", '"': '"', "`": "`", "[": "]"}

    while index < length:
        char = sql[index]
        if char in closing:
            terminator = closing[char]
            index += 1
            while index < length:
                if sql[index] == terminator:
                    # A doubled delimiter is an escaped literal quote.
                    if terminator != "]" and index + 1 < length and sql[index + 1] == terminator:
                        out[index] = "x"
                        out[index + 1] = "x"
                        index += 2
                        continue
                    break
                out[index] = "x"
                index += 1
        index += 1

    return "".join(out)


def split_statements(sql: str) -> list[str]:
    """Splits on semicolons that are outside quoted spans."""
    masked = mask_quoted_spans(sql)
    statements = []
    start = 0
    for index, char in enumerate(masked):
        if char == ";":
            statements.append(sql[start:index])
            start = index + 1
    statements.append(sql[start:])
    return [statement for statement in statements if statement.strip()]


def validate(sql: str) -> ValidatedSql:
    """Validates a statement as single, read-only, and non-destructive.

    Raises SqlValidationError with a specific message naming the failed rule.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise SqlValidationError("No SQL statement was provided.")

    stripped = strip_comments(sql).strip()
    if not stripped:
        raise SqlValidationError("No SQL statement was provided.")

    statements = split_statements(stripped)
    if len(statements) > 1:
        raise SqlValidationError(
            "Only a single statement may be executed; multiple statements were detected."
        )
    if not statements:
        raise SqlValidationError("No SQL statement was provided.")

    statement = statements[0].strip()
    masked = mask_quoted_spans(statement)

    first_word_match = re.match(r"\s*([A-Za-z_]+)", masked)
    if not first_word_match:
        raise SqlValidationError("No SQL statement was provided.")
    first_word = first_word_match.group(1).upper()
    if first_word not in ("SELECT", "WITH"):
        raise SqlValidationError(
            "Only single, read-only SELECT/WITH statements are permitted; "
            f"statement begins with {first_word}."
        )

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", masked, re.IGNORECASE):
            raise SqlValidationError(
                "Only single, read-only SELECT/WITH statements are permitted; "
                f"detected keyword: {keyword}."
            )

    normalized = statement.rstrip().rstrip(";").rstrip()
    has_limit = bool(re.search(r"\bLIMIT\b", mask_quoted_spans(normalized), re.IGNORECASE))
    return ValidatedSql(sql=normalized, has_limit=has_limit)
