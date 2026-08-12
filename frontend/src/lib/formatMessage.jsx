import { Fragment } from 'react'

// Minimal, safe markdown-ish rendering for agent answers. The agent's response
// template (backend SYSTEM_PROMPT) produces short prose, optional **bold**
// section labels, `inline code`, and bullet/numbered lists — this renders that
// readably without pulling in a full markdown dependency.
// All input is escaped by construction (matched tokens are sliced verbatim).

const INLINE_REGEX = /(\*\*[^*]+\*\*|`[^`]+`)/g
const BULLET_REGEX = /^\s*[-*•]\s+/
const ORDERED_REGEX = /^\s*\d+[.)]\s+/
const ATX_HEADING_REGEX = /^\s*#{1,6}\s+(.*)$/
// A line that is entirely bold, e.g. "**Key finding**" — the response template
// uses these as section labels, so they render as headings rather than a
// paragraph that merely happens to be bold.
const BOLD_HEADING_REGEX = /^\s*\*\*([^*]+)\*\*:?\s*$/

function renderInline(text, keyPrefix) {
  const parts = []
  let last = 0
  for (const match of text.matchAll(INLINE_REGEX)) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    const token = match[0]
    const key = `${keyPrefix}-${match.index}`
    if (token.startsWith('**')) {
      // Recurse so **`code`** (bold wrapping inline code) renders correctly.
      parts.push(
        <strong key={`${key}b`} className="font-semibold text-slate-50">
          {renderInline(token.slice(2, -2), `${key}i`)}
        </strong>,
      )
    } else {
      parts.push(
        <code
          key={`${key}c`}
          className="rounded bg-white/8 px-1.5 py-0.5 font-mono text-[0.9em] text-brand-cyan"
        >
          {token.slice(1, -1)}
        </code>,
      )
    }
    last = match.index + token.length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

function Heading({ children }) {
  return (
    <h4 className="text-[13px] font-semibold tracking-tight text-white">{children}</h4>
  )
}

function ListBlock({ ordered, items, keyPrefix }) {
  const List = ordered ? 'ol' : 'ul'
  return (
    <List className={`space-y-1 pl-5 ${ordered ? 'list-decimal' : 'list-disc'} marker:text-slate-500`}>
      {items.map((item, index) => (
        // eslint-disable-next-line react/no-array-index-key
        <li key={index} className="pl-0.5">
          {renderInline(item, `${keyPrefix}-li${index}`)}
        </li>
      ))}
    </List>
  )
}

// Splits one blank-line-delimited block into ordered runs of headings,
// list items and paragraph text. The agent commonly emits a section label
// immediately followed by its bullets with no blank line between them, so a
// block is not necessarily homogeneous.
function parseBlock(block) {
  const segments = []
  let paragraph = []
  let list = null

  const flushParagraph = () => {
    if (paragraph.length) {
      segments.push({ type: 'p', lines: paragraph })
      paragraph = []
    }
  }
  const flushList = () => {
    if (list) {
      segments.push(list)
      list = null
    }
  }

  for (const line of block.split('\n')) {
    if (!line.trim()) continue

    const atx = line.match(ATX_HEADING_REGEX)
    const boldHeading = line.match(BOLD_HEADING_REGEX)
    if (atx || boldHeading) {
      flushParagraph()
      flushList()
      segments.push({ type: 'h', text: (atx ? atx[1] : boldHeading[1]).trim() })
      continue
    }

    const isBullet = BULLET_REGEX.test(line)
    const isOrdered = !isBullet && ORDERED_REGEX.test(line)
    if (isBullet || isOrdered) {
      flushParagraph()
      const ordered = isOrdered
      if (!list || list.ordered !== ordered) {
        flushList()
        list = { type: 'ul', ordered, items: [] }
      }
      list.items.push(line.replace(isBullet ? BULLET_REGEX : ORDERED_REGEX, ''))
      continue
    }

    flushList()
    paragraph.push(line)
  }

  flushParagraph()
  flushList()
  return segments
}

export default function FormattedMessage({ text }) {
  if (!text) return null

  const blocks = text.split(/\n\s*\n/).filter((block) => block.trim())

  return (
    <div className="space-y-3">
      {blocks.map((block, blockIndex) => {
        const segments = parseBlock(block)
        return (
          <div key={blockIndex} className="space-y-2">
            {segments.map((segment, segmentIndex) => {
              const key = `b${blockIndex}-s${segmentIndex}`
              if (segment.type === 'h') {
                return <Heading key={key}>{renderInline(segment.text, key)}</Heading>
              }
              if (segment.type === 'ul') {
                return (
                  <ListBlock
                    key={key}
                    ordered={segment.ordered}
                    items={segment.items}
                    keyPrefix={key}
                  />
                )
              }
              return (
                <p key={key} className="leading-relaxed">
                  {segment.lines.map((line, lineIndex) => (
                    <Fragment key={lineIndex}>
                      {renderInline(line, `${key}-l${lineIndex}`)}
                      {lineIndex < segment.lines.length - 1 && <br />}
                    </Fragment>
                  ))}
                </p>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
