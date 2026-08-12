// Lightweight SQL tokenizer for syntax highlighting (frontend batch §Batch 4).
// Dependency-free: a single-pass regex scanner that classifies each token.
// It only colors text — it never executes or interprets the SQL.

const KEYWORDS = new Set([
  'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'LIMIT', 'OFFSET', 'HAVING',
  'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'CROSS', 'ON', 'USING',
  'AS', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'LIKE', 'BETWEEN', 'EXISTS',
  'DISTINCT', 'ALL', 'UNION', 'INTERSECT', 'EXCEPT', 'CASE', 'WHEN', 'THEN',
  'ELSE', 'END', 'ASC', 'DESC', 'WITH', 'RECURSIVE', 'CAST', 'COALESCE',
  'DEFAULT', 'PRIMARY', 'FOREIGN', 'KEY', 'REFERENCES', 'UNIQUE', 'INDEX',
  'CREATE', 'DROP', 'ALTER', 'TABLE', 'VIEW', 'INSERT', 'UPDATE', 'DELETE',
  'INTO', 'VALUES', 'SET', 'TRUNCATE', 'BEGIN', 'COMMIT',
])

// Aggregate/function names we highlight as function calls.
const FUNCTIONS = new Set([
  'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'ABS', 'COALESCE', 'IFNULL',
  'NULLIF', 'CONCAT', 'SUBSTR', 'SUBSTRING', 'LENGTH', 'UPPER', 'LOWER',
  'TRIM', 'REPLACE', 'CAST', 'DATE', 'DATETIME', 'STRFTIME', 'JULIANDAY',
  'TOTAL', 'GROUP_CONCAT', 'RANDOM', 'GLOB',
])

const TOKEN_REGEX = new RegExp(
  [
    /(--[^\n]*)/.source, // line comment
    /(`[^`]*`)/.source, // backtick identifier
    /('(?:[^']|'')*')/.source, // single-quoted string
    /("(?:[^"]|"")*")/.source, // double-quoted string
    /(\b\d+(?:\.\d+)?\b)/.source, // number
    /([A-Za-z_][A-Za-z0-9_]*)/.source, // word
    /(<=|>=|<>|!=|=|<|>|\+|-|\*|\/|%|\(|\)|,|;|\.)/.source, // operator/punct
  ].join('|'),
  'g',
)

/**
 * Tokenize SQL into [{ type, value }] where type is one of:
 * keyword | function | string | number | comment | identifier | operator | text
 */
export function tokenizeSql(sql) {
  const tokens = []
  let lastIndex = 0

  for (const match of sql.matchAll(TOKEN_REGEX)) {
    const index = match.index
    if (index > lastIndex) {
      tokens.push({ type: 'text', value: sql.slice(lastIndex, index) })
    }

    const [full, comment, backtick, sqString, dqString, number, word, operator] = match
    if (comment) tokens.push({ type: 'comment', value: comment })
    else if (backtick) tokens.push({ type: 'identifier', value: backtick })
    else if (sqString || dqString) tokens.push({ type: 'string', value: sqString || dqString })
    else if (number) tokens.push({ type: 'number', value: number })
    else if (word) {
      const upper = word.toUpperCase()
      if (KEYWORDS.has(upper)) tokens.push({ type: 'keyword', value: word })
      else if (FUNCTIONS.has(upper)) tokens.push({ type: 'function', value: word })
      else if (/^\s*\(/.test(sql.slice(index + word.length))) {
        tokens.push({ type: 'function', value: word })
      } else tokens.push({ type: 'identifier', value: word })
    } else if (operator) tokens.push({ type: 'operator', value: operator })

    lastIndex = index + full.length
  }

  if (lastIndex < sql.length) {
    tokens.push({ type: 'text', value: sql.slice(lastIndex) })
  }
  return tokens
}
