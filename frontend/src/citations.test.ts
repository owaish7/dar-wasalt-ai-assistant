import { expect, test } from 'vitest';
import { citationParts } from './citations';
import type { Source } from './api';

test('only supplied, safe citations become links, including grouped Arabic punctuation', () => {
  const sources = [{id: 1, url: 'https://wasalt.sa/en'}, {id: 2, url: 'javascript:alert(1)'}] as Source[];
  const parts = citationParts('Facts [1، 2] and [99].', sources);
  expect(parts.filter(p => p.url)).toEqual([{text: '[1]', url: 'https://wasalt.sa/en'}]);
  expect(parts.map(p => p.text).join('')).toBe('Facts [1][2] and [99].');
});

test('HTML remains text and lookalike hosts cannot become citation links', () => {
  const parts = citationParts('<script>x</script> [1]', [{id: 1, url: 'https://wasalt.sa.evil.test'}] as Source[]);
  expect(parts.some(p => p.url)).toBe(false);
  expect(parts[0].text).toBe('<script>x</script> ');
});
