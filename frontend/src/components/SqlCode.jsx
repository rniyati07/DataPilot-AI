import { tokenizeSql } from '../lib/sqlHighlight'

// Renders SQL with token colors. Pure presentation — the SQL text itself is
// never modified, only wrapped in styled spans.
const TOKEN_CLASSES = {
  keyword: 'text-violet-300',
  function: 'text-cyan-300',
  string: 'text-emerald-300',
  number: 'text-amber-300',
  comment: 'text-slate-500 italic',
  identifier: 'text-slate-200',
  operator: 'text-slate-400',
  text: 'text-slate-300',
}

export default function SqlCode({ sql }) {
  const tokens = tokenizeSql(sql)
  return (
    <code className="font-mono text-[12.5px] leading-relaxed">
      {tokens.map((token, index) => (
        // eslint-disable-next-line react/no-array-index-key
        <span key={index} className={TOKEN_CLASSES[token.type] || 'text-slate-300'}>
          {token.value}
        </span>
      ))}
    </code>
  )
}
