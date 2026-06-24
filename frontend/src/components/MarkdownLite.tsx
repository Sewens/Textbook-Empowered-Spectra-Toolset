import { resolveSpectraUrl } from '../api'

type Block = { type: 'paragraph'; text: string } | { type: 'table'; headers: string[]; rows: string[][] } | { type: 'image'; alt: string; src: string }

function cleanMarkdown(text: string) {
  return text
    .replace(/<details>|<\/details>|<summary>.*?<\/summary>/g, '')
    .replaceAll('\[', '[')
    .replaceAll('\]', ']')
    .replaceAll('\,', '')
    .replaceAll('$', '')
    .replace(/cm\s*\^?\{-?1\}/g, 'cm-1')
    .replace(/cm\s*\^-?1/g, 'cm-1')
    .replace(/\s+/g, ' ')
    .trim()
}

function splitCells(line: string) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cleanMarkdown(cell))
}

function isSeparator(line: string) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line)
}

function parseInlineImages(text: string): Block[] {
  const blocks: Block[] = []
  const imagePattern = /!\[([^\]]*)\]\(([^)]+)\)/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = imagePattern.exec(text))) {
    const before = cleanMarkdown(text.slice(lastIndex, match.index))
    if (before) blocks.push({ type: 'paragraph', text: before })
    blocks.push({ type: 'image', alt: match[1] || '谱图资源', src: match[2] })
    lastIndex = match.index + match[0].length
  }
  const rest = cleanMarkdown(text.slice(lastIndex))
  if (rest) blocks.push({ type: 'paragraph', text: rest })
  return blocks
}

function parseBlocks(source: string): Block[] {
  const lines = source.replace(/\r\n/g, '\n').replace(/(<\/details>|<details>|<summary>.*?<\/summary>)/g, '\n').split('\n')
  const result: Block[] = []
  let paragraph: string[] = []
  let i = 0
  const flush = () => {
    const text = paragraph.join(' ').trim()
    paragraph = []
    if (text) result.push(...parseInlineImages(text))
  }
  while (i < lines.length) {
    const line = lines[i]
    const next = lines[i + 1]
    if (line.trim().startsWith('|') && next && isSeparator(next)) {
      flush()
      const headers = splitCells(line)
      const rows: string[][] = []
      i += 2
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        if (!isSeparator(lines[i])) rows.push(splitCells(lines[i]))
        i += 1
      }
      result.push({ type: 'table', headers, rows })
      continue
    }
    if (!line.trim()) flush()
    else paragraph.push(line)
    i += 1
  }
  flush()
  return result
}

export default function MarkdownLite({ source, compact = false }: { source?: string | null; compact?: boolean }) {
  const blocks = parseBlocks(source || '')
  return <div className={'markdown-lite ' + (compact ? 'compact' : '')}>{blocks.map((block, index) => {
    if (block.type === 'paragraph') return <p key={index}>{block.text}</p>
    if (block.type === 'image') return <figure key={index}><img src={resolveSpectraUrl(block.src) || block.src} alt={block.alt} /><figcaption>{block.alt}</figcaption></figure>
    return <div className="md-table-wrap" key={index}><table><thead><tr>{block.headers.map((h) => <th key={h}>{h}</th>)}</tr></thead><tbody>{block.rows.map((row, r) => <tr key={r}>{row.map((cell, c) => <td key={c}>{cell}</td>)}</tr>)}</tbody></table></div>
  })}</div>
}
