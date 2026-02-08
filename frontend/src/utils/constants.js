// Stop words for keyword extraction
export const STOP_WORDS = new Set([
  'the', 'and', 'for', 'with', 'that', 'this', 'from', 'your', 'have', 'are',
  'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out',
  'has', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'way', 'who',
  'did', 'get', 'let', 'put', 'say', 'she', 'too', 'use', 'into', 'just',
  'than', 'them', 'then', 'they', 'what', 'when', 'will', 'more', 'some',
  'time', 'very', 'make', 'like', 'back', 'only', 'come', 'over', 'such',
  'take', 'also', 'been', 'call', 'find', 'long', 'down', 'day', 'made',
  'could', 'people', 'other', 'would', 'their', 'about', 'after', 'which',
  'these', 'being', 'there', 'where', 'should', 'through', 'before',
  'using', 'based', 'built', 'simple', 'easy', 'fast', 'free', 'open',
  'source', 'fully', 'work', 'works', 'written', 'provide', 'provides',
  'support', 'supports', 'powered', 'designed', 'create', 'creating',
  'build', 'building', 'enable', 'enables', 'allows', 'features', 'including'
]);

// Tech keywords for weighting
export const TECH_KEYWORDS = new Set([
  'ai', 'ml', 'llm', 'gpt', 'chatbot', 'neural', 'deep', 'learning', 'model',
  'react', 'vue', 'angular', 'next', 'nuxt', 'svelte', 'typescript', 'javascript',
  'docker', 'kubernetes', 'terraform', 'devops', 'pipeline', 'container',
  'python', 'rust', 'golang', 'java', 'kotlin', 'swift', 'flutter',
  'api', 'rest', 'graphql', 'websocket', 'server', 'client', 'backend', 'frontend',
  'database', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite',
  'blockchain', 'web3', 'crypto', 'ethereum', 'solidity',
  'security', 'encryption', 'authentication', 'oauth', 'token', 'auth',
  'cloud', 'aws', 'azure', 'serverless', 'lambda', 'microservice',
  'testing', 'framework', 'library', 'sdk', 'cli', 'terminal',
  'agent', 'agentic', 'autonomous', 'inference', 'transformer', 'embedding',
  'vector', 'rag', 'async', 'streaming', 'realtime', 'automation',
  'visualization', 'dashboard', 'analytics', 'monitoring', 'metrics'
]);
