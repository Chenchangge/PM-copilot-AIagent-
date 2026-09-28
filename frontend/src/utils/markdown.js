// Markdown 渲染：核心内容等受控 Markdown 文本 → HTML。
// 使用 markdown-it 且 html:false（默认），源码中的原始 HTML/script 会被转义，不执行。
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, breaks: false })

export function renderMarkdown(text) {
  return md.render(text || '')
}
