export interface CitationNode {
  type: 'text' | 'citation';
  content: string;
  sourceId?: number;
}

export function parseCitations(text: string): CitationNode[] {
  const nodes: CitationNode[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      nodes.push({
        type: 'text',
        content: text.slice(lastIndex, match.index),
      });
    }

    // Add citation
    nodes.push({
      type: 'citation',
      content: match[0],
      sourceId: parseInt(match[1]),
    });

    lastIndex = regex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    nodes.push({
      type: 'text',
      content: text.slice(lastIndex),
    });
  }

  return nodes;
}

export function extractSourceIds(text: string): number[] {
  const regex = /\[(\d+)\]/g;
  const numbers: number[] = [];
  let match;

  while ((match = regex.exec(text)) !== null) {
    numbers.push(parseInt(match[1]));
  }

  return numbers;
}
