/**
 * 安全的认证 Token 管理工具
 *
 * 优化：
 * 1. 优先使用内存存储 Token
 * 2. 仅在页面刷新/关闭前可选持久化
 * 3. 增强的输入净化
 */

const TOKEN_KEY = 'auth_token';

// 内存中的 token 存储
let memoryToken = null;

/**
 * Sanitize token value to prevent XSS injection
 */
function sanitizeToken(token) {
  if (!token || typeof token !== 'string') return null;
  // Only allow alphanumeric, dots, hyphens, and underscores (typical JWT characters)
  if (!/^[A-Za-z0-9._-]+$/.test(token)) {
    console.warn('Invalid token format detected');
    return null;
  }
  return token;
}

/**
 * 初始化 Token (从 localStorage 加载)
 * 应在应用启动时调用一次
 */
function initToken() {
  try {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      memoryToken = sanitizeToken(stored);
      // 如果 localStorage 中的 token 无效，清理它
      if (stored && !memoryToken) {
        localStorage.removeItem(TOKEN_KEY);
      }
    }
  } catch (e) {
    console.error('Failed to init token:', e);
  }
}

// 立即初始化
initToken();

/**
 * 获取认证 token
 * @returns {string|null}
 */
export function getAuthToken() {
  return memoryToken;
}

/**
 * 设置认证 token
 * @param {string} token
 * @param {boolean} remember - 是否记住登录 (持久化到 localStorage)
 */
export function setAuthToken(token, remember = true) {
  try {
    if (token) {
      const sanitized = sanitizeToken(token);
      if (sanitized) {
        memoryToken = sanitized;
        if (remember) {
          localStorage.setItem(TOKEN_KEY, sanitized);
        } else {
          localStorage.removeItem(TOKEN_KEY); // 如果不记住，确保本地没有旧的
        }
      } else {
        console.error('Attempted to set invalid token');
      }
    } else {
      memoryToken = null;
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch (e) {
    console.error('Failed to set auth token:', e);
  }
}

/**
 * 清除认证 token
 */
export function clearAuthToken() {
  memoryToken = null;
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    console.error('Failed to clear auth token:', e);
  }
}

/**
 * 检查是否已认证
 * @returns {boolean}
 */
export function isAuthenticated() {
  return !!getAuthToken();
}
