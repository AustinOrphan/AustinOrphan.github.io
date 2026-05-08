export function getReadingTime(content: string): string {
  const trimmed = content.trim();
  if (!trimmed) return '< 1 min read';
  const words = trimmed.split(/\s+/).length;
  const minutes = Math.ceil(words / 200);
  return `${minutes} min read`;
}
