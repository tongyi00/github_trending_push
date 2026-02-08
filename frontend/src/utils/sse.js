/**
 * SSE (Server-Sent Events) 解析器
 * 支持自定义请求头（用于 JWT 认证）
 */

/**
 * 自定义 SSE 错误类
 */
export class SSEError extends Error {
  constructor(message, status = null, originalError = null) {
    super(message);
    this.name = 'SSEError';
    this.status = status;
    this.originalError = originalError;
  }
}

/**
 * 解析 SSE 数据流
 * @param {ReadableStream} stream - fetch 响应的 body stream
 * @param {Object} handlers - 事件处理器映射 { eventName: handler }
 * @returns {Promise<void>}
 */
export async function parseSSEStream(stream, handlers = {}) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last incomplete line
      buffer = lines.pop() || '';

      let currentEvent = 'message';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          // Accumulate multi-line data fields (SSE spec compliant)
          currentData += (currentData ? '\n' : '') + line.slice(5).trim();
        } else if (line === '') {
          // Empty line indicates a complete message
          if (currentData && handlers[currentEvent]) {
            try {
              const data = JSON.parse(currentData);
              handlers[currentEvent](data);
            } catch (e) {
              console.error(`Failed to parse SSE data for event "${currentEvent}":`, e);
            }
          }
          currentEvent = 'message';
          currentData = '';
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Calculate exponential backoff delay with jitter
 * @param {number} attempt - Current retry attempt (1-based)
 * @param {number} baseDelay - Base delay in milliseconds
 * @param {number} maxDelay - Maximum delay in milliseconds
 * @returns {number} Delay in milliseconds
 */
function calculateBackoffDelay(attempt, baseDelay = 1000, maxDelay = 30000) {
  // Exponential backoff: baseDelay * 2^(attempt-1)
  const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
  // Add jitter (0-25% of delay) to prevent thundering herd
  const jitter = exponentialDelay * Math.random() * 0.25;
  // Cap at maxDelay
  return Math.min(exponentialDelay + jitter, maxDelay);
}

/**
 * 创建支持认证的 SSE 连接
 * @param {string} url - SSE 端点 URL
 * @param {Object} options - 配置选项
 * @param {Object} options.headers - 自定义请求头（如 Authorization）
 * @param {Object} options.handlers - 事件处理器 { thinking, partial, complete, error }
 * @param {Function} options.onOpen - 连接打开回调
 * @param {Function} options.onError - 错误回调
 * @param {number} options.maxRetries - 最大重试次数（默认 5）
 * @param {number} options.baseDelay - 基础重试延迟毫秒数（默认 1000）
 * @param {number} options.maxDelay - 最大重试延迟毫秒数（默认 30000）
 * @returns {Object} 控制对象 { abort: Function }
 */
export function createSSEConnection(url, options = {}) {
  const {
    headers = {},
    handlers = {},
    onOpen,
    onError,
    maxRetries = 5,
    baseDelay = 1000,
    maxDelay = 30000
  } = options;

  const controller = new AbortController();
  let retryCount = 0;
  let retryTimeout = null;

  const connect = async () => {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          ...headers
        },
        signal: controller.signal
      });

      if (!response.ok) {
        throw new SSEError(`HTTP ${response.status}: ${response.statusText}`, response.status);
      }

      if (!response.body) {
        throw new SSEError('Response body is null', response.status);
      }

      // Connection successful, reset retry count
      retryCount = 0;

      if (onOpen) {
        onOpen();
      }

      await parseSSEStream(response.body, handlers);
    } catch (error) {
      if (error.name === 'AbortError') {
        // User-initiated cancellation, don't retry
        return;
      }

      // Retry only for network errors, not for 4xx/5xx HTTP errors
      const shouldRetry = !(error instanceof SSEError) && retryCount < maxRetries;

      if (shouldRetry) {
        retryCount++;
        const delay = calculateBackoffDelay(retryCount, baseDelay, maxDelay);
        console.warn(`SSE connection failed, retrying in ${Math.round(delay)}ms (${retryCount}/${maxRetries})...`);
        retryTimeout = setTimeout(connect, delay);
      } else {
        // Exceeded retry limit or non-retryable error
        if (onError) {
          onError(error);
        }
      }
    }
  };

  connect();

  return {
    abort: () => {
      if (retryTimeout) {
        clearTimeout(retryTimeout);
      }
      controller.abort();
    }
  };
}
