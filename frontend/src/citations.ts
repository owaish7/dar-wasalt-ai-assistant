import type { Source } from './api';

export function citationParts(text: string, sources: Source[]): {text: string; url?: string}[] {
  const parts: {text: string; url?: string}[] = [];
  let offset = 0;
  for (const match of text.matchAll(/\[(\d+(?:\s*[,،]\s*\d+)*)\]/g)) {
    parts.push({text: text.slice(offset, match.index)});
    for (const id of match[1].split(/[,،]/).map(Number)) {
      const source = sources.find(s => s.id === id);
      let url: string | undefined;
      try {
        const parsed = new URL(source?.url ?? '');
        if (parsed.protocol === 'https:' && !parsed.username && !parsed.password && !parsed.port &&
            ['darglobal.co.uk', 'www.darglobal.co.uk', 'wasalt.sa', 'www.wasalt.sa', 'blog.wasalt.sa'].includes(parsed.hostname)) url = parsed.href;
      } catch { /* Invalid source stays plain text. */ }
      parts.push({text: `[${id}]`, url});
    }
    offset = match.index! + match[0].length;
  }
  parts.push({text: text.slice(offset)});
  return parts;
}
