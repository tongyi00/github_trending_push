<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createSSEConnection, SSEError } from '@/utils/sse';
import { getAuthToken } from '@/utils/auth';

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const statusMessage = ref('Connecting...');
const streamContent = ref('');
const reportData = ref(null);
const error = ref(null);
let sseConnection = null;

const projectName = computed(() => route.params.name || '');
const projectOwner = computed(() => route.params.owner || '');
const fullName = computed(() => `${projectOwner.value}/${projectName.value}`);

const fetchAnalysisReport = () => {
  loading.value = true;
  error.value = null;
  statusMessage.value = 'Connecting...';
  streamContent.value = '';

  // Close existing connection if any
  if (sseConnection) {
    sseConnection.abort();
  }

  const streamUrl = `/api/analysis/${projectOwner.value}/${projectName.value}/stream`;

  // 获取认证 token（使用安全的 Token 管理工具）
  const token = getAuthToken();
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

  sseConnection = createSSEConnection(streamUrl, {
    headers,
    handlers: {
      thinking: (data) => {
        statusMessage.value = data.message || 'Analyzing...';
      },
      partial: (data) => {
        streamContent.value += data.content || '';
      },
      complete: (data) => {
        if (data.success) {
          const report = data.report;
          reportData.value = {
            project: {
              name: fullName.value,
              url: `https://github.com/${fullName.value}`,
              description: route.query.description || '',
              language: route.query.language || 'Unknown',
              stars: parseInt(route.query.stars) || 0,
            },
            analysis: {
              summary: report.executive_summary,
              keyFeatures: report.key_features,
              technicalInsights: formatScores(report.scores),
              techStack: report.tech_stack,
              useCases: report.use_cases,
              limitations: report.limitations,
              learningResources: report.learning_resources,
              integrationExamples: report.integration_examples || [],
              faq: report.faq || []
            },
            meta: {
              modelUsed: data.model_used,
              generatedAt: data.generated_at
            }
          };
        } else {
          error.value = data.error || 'Failed to generate analysis';
        }
        loading.value = false;
      },
      error: (data) => {
        error.value = data.message || 'Analysis generation failed';
        loading.value = false;
      }
    },
    onOpen: () => {
      statusMessage.value = 'Connected. Analyzing...';
    },
    onError: (err) => {
      // 使用 SSEError 类的 status 属性进行准确判断
      if (err instanceof SSEError) {
        if (err.status === 401) {
          error.value = 'Authentication required. Please log in.';
        } else if (err.status === 404) {
          error.value = 'Repository not found in database';
        } else if (err.status === 429) {
          error.value = 'Rate limit exceeded. Please try again later.';
        } else {
          error.value = `Server error (${err.status}): ${err.message}`;
        }
      } else {
        error.value = `Connection error: ${err.message}`;
      }
      loading.value = false;
    }
  });
};

const formatScores = (scores) => {
  const categoryNames = {
    architecture: 'Architecture',
    code_quality: 'Code Quality',
    documentation: 'Documentation',
    community: 'Community',
    innovation: 'Innovation'
  };

  return Object.entries(scores).map(([key, value]) => ({
    category: categoryNames[key] || key,
    score: value.score,
    description: value.reason
  }));
};

onMounted(() => {
  fetchAnalysisReport();
});

onUnmounted(() => {
  if (sseConnection) {
    sseConnection.abort();
    sseConnection = null;
  }
});

const goBack = () => {
  router.back();
};

const formatNumber = (num) => {
  return new Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'short' }).format(num);
};

const formatDate = (isoString) => {
  if (!isoString) return '';
  return new Date(isoString).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};
</script>

<template>
  <div class="analysis-page">
    <!-- Navigation Bar -->
    <nav class="nav-bar">
      <button @click="goBack" class="back-button">
        <span class="back-arrow">←</span>
        <span class="back-text">Back to Dashboard</span>
      </button>
      <div class="nav-accent"></div>
    </nav>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">{{ statusMessage }}</p>
      <p v-if="streamContent" class="stream-preview">{{ streamContent.slice(-200) }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <h2>⚠️ Error</h2>
      <p>{{ error }}</p>
      <button @click="fetchAnalysisReport" class="retry-button">Retry</button>
    </div>

    <!-- Report Content -->
    <article v-else class="report-content">
      <!-- Hero Section -->
      <header class="report-hero">
        <div class="hero-meta">
          <span class="meta-badge">AI Analysis Report</span>
          <span class="meta-divider">•</span>
          <span class="meta-date">{{ new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) }}</span>
        </div>

        <h1 class="hero-title">{{ reportData.project.name }}</h1>

        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-icon">★</span>
            <span class="stat-value">{{ formatNumber(reportData.project.stars) }}</span>
            <span class="stat-label">Stars</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-icon">◆</span>
            <span class="stat-value">{{ reportData.project.language }}</span>
            <span class="stat-label">Language</span>
          </div>
        </div>

        <a :href="reportData.project.url" target="_blank" class="hero-link">
          View on GitHub →
        </a>
      </header>

      <!-- Summary Section -->
      <section class="report-section summary-section">
        <div class="section-number">01</div>
        <h2 class="section-title">Executive Summary</h2>
        <div class="section-content">
          <p class="summary-text">{{ reportData.analysis.summary }}</p>
          <p class="project-description">{{ reportData.project.description }}</p>
        </div>
      </section>

      <!-- Key Features -->
      <section class="report-section features-section">
        <div class="section-number">02</div>
        <h2 class="section-title">Key Features</h2>
        <div class="section-content">
          <ul class="features-list">
            <li v-for="(feature, index) in reportData.analysis.keyFeatures" :key="index" class="feature-item">
              <span class="feature-marker"></span>
              <span class="feature-text">{{ feature }}</span>
            </li>
          </ul>
        </div>
      </section>

      <!-- Technical Insights -->
      <section class="report-section insights-section">
        <div class="section-number">03</div>
        <h2 class="section-title">Technical Assessment</h2>
        <div class="section-content">
          <div class="insights-grid">
            <div v-for="insight in reportData.analysis.technicalInsights" :key="insight.category" class="insight-card">
              <div class="insight-header">
                <h3 class="insight-category">{{ insight.category }}</h3>
                <div class="insight-score">
                  <span class="score-value">{{ insight.score }}</span>
                  <span class="score-max">/10</span>
                </div>
              </div>
              <div class="insight-bar">
                <div class="insight-bar-fill" :style="{ width: `${insight.score * 10}%` }"></div>
              </div>
              <p class="insight-description">{{ insight.description }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Tech Stack -->
      <section v-if="reportData.analysis.techStack?.length" class="report-section techstack-section">
        <div class="section-number">04</div>
        <h2 class="section-title">Technology Stack</h2>
        <div class="section-content">
          <div class="techstack-tags">
            <span v-for="tech in reportData.analysis.techStack" :key="tech" class="tech-tag">{{ tech }}</span>
          </div>
        </div>
      </section>

      <!-- Use Cases -->
      <section v-if="reportData.analysis.useCases?.length" class="report-section usecases-section">
        <div class="section-number">05</div>
        <h2 class="section-title">Use Cases</h2>
        <div class="section-content">
          <ul class="usecases-list">
            <li v-for="(useCase, index) in reportData.analysis.useCases" :key="index" class="usecase-item">
              <span class="usecase-icon">✓</span>
              <span class="usecase-text">{{ useCase }}</span>
            </li>
          </ul>
        </div>
      </section>

      <!-- Limitations -->
      <section v-if="reportData.analysis.limitations?.length" class="report-section limitations-section">
        <div class="section-number">06</div>
        <h2 class="section-title">Limitations & Considerations</h2>
        <div class="section-content">
          <div class="limitations-list">
            <div v-for="(limitation, index) in reportData.analysis.limitations" :key="index" class="limitation-item">
              <span class="limitation-icon">⚠</span>
              <span class="limitation-text">{{ limitation }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Learning Resources -->
      <section v-if="reportData.analysis.learningResources?.length" class="report-section resources-section">
        <div class="section-number">07</div>
        <h2 class="section-title">Learning Resources</h2>
        <div class="section-content">
          <ul class="resources-list">
            <li v-for="(resource, index) in reportData.analysis.learningResources" :key="index" class="resource-item">
              <span class="resource-icon">📚</span>
              <span class="resource-text">{{ resource }}</span>
            </li>
          </ul>
        </div>
      </section>

      <!-- Footer -->
      <footer class="report-footer">
        <div class="footer-divider"></div>
        <div class="footer-meta" v-if="reportData.meta">
          <span class="meta-item">Model: <strong>{{ reportData.meta.modelUsed }}</strong></span>
          <span class="meta-divider">•</span>
          <span class="meta-item">Generated: <strong>{{ formatDate(reportData.meta.generatedAt) }}</strong></span>
        </div>
        <p class="footer-text">
          Generated by <span class="footer-highlight">GitHub Trending AI</span>
        </p>
      </footer>
    </article>
  </div>
</template>

<style scoped>
/* ===== COLOR PALETTE ===== */
:root {
  --color-ink: #1a1a1a;
  --color-charcoal: #2d2d2d;
  --color-slate: #5a5a5a;
  --color-stone: #8a8a8a;
  --color-silver: #d4d4d4;
  --color-paper: #fafafa;
  --color-gold: #d4a574;
  --color-gold-dark: #b8935f;
}

/* ===== PAGE LAYOUT ===== */
.analysis-page {
  min-height: 100vh;
  background: linear-gradient(to bottom, #ffffff 0%, var(--color-paper) 100%);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  color: var(--color-ink);
}

/* ===== NAVIGATION ===== */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-silver);
  padding: 1.5rem 3rem;
  animation: slideDown 0.5s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  font-family: inherit;
  font-size: 0.95rem;
  color: var(--color-charcoal);
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0.5rem 0;
}

.back-button:hover {
  color: var(--color-gold);
}

.back-button:hover .back-arrow {
  transform: translateX(-4px);
}

.back-arrow {
  font-size: 1.5rem;
  transition: transform 0.3s ease;
}

.back-text {
  font-weight: 500;
  letter-spacing: 0.02em;
}

.nav-accent {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--color-gold) 0%, transparent 100%);
}

/* ===== LOADING STATE ===== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: 2rem;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 3px solid var(--color-silver);
  border-top: 3px solid var(--color-gold);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-family: Georgia, 'Times New Roman', Times, serif;
  font-size: 1.2rem;
  color: var(--color-slate);
  letter-spacing: 0.05em;
}

.stream-preview {
  max-width: 600px;
  margin-top: 1.5rem;
  padding: 1rem 1.5rem;
  background: rgba(212, 165, 116, 0.1);
  border-left: 3px solid var(--color-gold);
  border-radius: 0 8px 8px 0;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--color-slate);
  white-space: pre-wrap;
  word-break: break-word;
  text-align: left;
  animation: fadeIn 0.3s ease-out;
}

/* ===== ERROR STATE ===== */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: 1.5rem;
  padding: 2rem;
}

.error-state h2 {
  font-family: Georgia, 'Times New Roman', Times, serif;
  font-size: 2rem;
  color: var(--color-charcoal);
}

.retry-button {
  padding: 0.75rem 2rem;
  background: var(--color-gold);
  border: none;
  border-radius: 4px;
  font-family: inherit;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-button:hover {
  background: var(--color-gold-dark);
  transform: translateY(-2px);
}

/* ===== REPORT CONTENT ===== */
.report-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 4rem 3rem 6rem;
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== HERO SECTION ===== */
.report-hero {
  margin-bottom: 5rem;
  padding-bottom: 3rem;
  border-bottom: 1px solid var(--color-silver);
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  font-size: 0.85rem;
  color: var(--color-slate);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.meta-badge {
  background: var(--color-gold);
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 2px;
  font-weight: 600;
}

.meta-divider {
  color: var(--color-silver);
}

.hero-title {
  font-family: Georgia, 'Times New Roman', Times, serif;
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 2rem;
  color: var(--color-ink);
  letter-spacing: -0.02em;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-icon {
  font-size: 1.2rem;
  color: var(--color-gold);
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-charcoal);
}

.stat-label {
  font-size: 0.85rem;
  color: var(--color-slate);
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--color-silver);
}

.hero-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: var(--color-charcoal);
  text-decoration: none;
  transition: all 0.3s ease;
  border-bottom: 2px solid var(--color-gold);
  padding-bottom: 0.25rem;
}

.hero-link:hover {
  color: var(--color-gold);
  transform: translateX(4px);
}

/* ===== REPORT SECTIONS ===== */
.report-section {
  margin-bottom: 5rem;
  animation: fadeInUp 0.8s ease-out both;
}

.report-section:nth-child(2) { animation-delay: 0.3s; }
.report-section:nth-child(3) { animation-delay: 0.4s; }
.report-section:nth-child(4) { animation-delay: 0.5s; }
.report-section:nth-child(5) { animation-delay: 0.6s; }

.section-number {
  font-family: Georgia, 'Times New Roman', Times, serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-gold);
  letter-spacing: 0.15em;
  margin-bottom: 0.5rem;
}

.section-title {
  font-family: Georgia, 'Times New Roman', Times, serif;
  font-size: 2.2rem;
  font-weight: 600;
  margin-bottom: 2rem;
  color: var(--color-charcoal);
  letter-spacing: -0.01em;
}

.section-content {
  padding-left: 3rem;
  border-left: 2px solid var(--color-silver);
}

/* Summary Section */
.summary-text {
  font-size: 1.25rem;
  line-height: 1.8;
  color: var(--color-charcoal);
  margin-bottom: 1.5rem;
  font-weight: 300;
}

.project-description {
  font-size: 1rem;
  line-height: 1.7;
  color: var(--color-slate);
  font-style: italic;
}

/* Features Section */
.features-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.feature-marker {
  width: 8px;
  height: 8px;
  background: var(--color-gold);
  border-radius: 50%;
  margin-top: 0.6rem;
  flex-shrink: 0;
}

.feature-text {
  font-size: 1.1rem;
  line-height: 1.7;
  color: var(--color-charcoal);
}

/* Insights Section */
.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.insight-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  border: 1px solid var(--color-silver);
  transition: all 0.3s ease;
}

.insight-card:hover {
  border-color: var(--color-gold);
  box-shadow: 0 8px 24px rgba(212, 165, 116, 0.15);
  transform: translateY(-4px);
}

.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.insight-category {
  font-family: Georgia, 'Times New Roman', Times, serif;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--color-charcoal);
}

.insight-score {
  display: flex;
  align-items: baseline;
  gap: 0.2rem;
}

.score-value {
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--color-gold);
}

.score-max {
  font-size: 1rem;
  color: var(--color-stone);
}

.insight-bar {
  height: 6px;
  background: var(--color-paper);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.insight-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-gold) 0%, var(--color-gold-dark) 100%);
  transition: width 0.8s ease-out;
}

.insight-description {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--color-slate);
}

/* Tech Stack Section */
.techstack-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.tech-tag {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--color-paper) 0%, white 100%);
  border: 1px solid var(--color-silver);
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-charcoal);
  transition: all 0.3s ease;
}

.tech-tag:hover {
  border-color: var(--color-gold);
  background: var(--color-gold);
  color: white;
  transform: translateY(-2px);
}

/* Use Cases Section */
.usecases-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.usecase-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #f8fff8 0%, white 100%);
  border-left: 3px solid #4ade80;
  border-radius: 0 8px 8px 0;
}

.usecase-icon {
  color: #22c55e;
  font-size: 1.1rem;
  font-weight: bold;
}

.usecase-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-charcoal);
}

/* Limitations Section */
.limitations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.limitation-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #fffbeb 0%, white 100%);
  border-left: 3px solid #f59e0b;
  border-radius: 0 8px 8px 0;
}

.limitation-icon {
  color: #f59e0b;
  font-size: 1.1rem;
}

.limitation-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-charcoal);
}

/* Learning Resources Section */
.resources-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.resource-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: white;
  border: 1px solid var(--color-silver);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.resource-item:hover {
  border-color: var(--color-gold);
  box-shadow: 0 4px 12px rgba(212, 165, 116, 0.15);
  transform: translateX(4px);
}

.resource-icon {
  font-size: 1.2rem;
}

.resource-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-charcoal);
}

/* Footer Meta */
.footer-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: var(--color-slate);
}

.footer-meta .meta-item strong {
  color: var(--color-charcoal);
}

.footer-meta .meta-divider {
  color: var(--color-silver);
}

/* Trends Section (kept for backwards compatibility) */
.trends-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.trend-card {
  text-align: center;
  padding: 2rem 1.5rem;
  background: linear-gradient(135deg, var(--color-paper) 0%, white 100%);
  border-radius: 8px;
  border: 1px solid var(--color-silver);
  transition: all 0.3s ease;
}

.trend-card:hover {
  border-color: var(--color-gold);
  transform: translateY(-4px);
}

.trend-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.trend-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin-bottom: 0.5rem;
}

.trend-label {
  font-size: 0.85rem;
  color: var(--color-slate);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* ===== FOOTER ===== */
.report-footer {
  margin-top: 6rem;
  padding-top: 3rem;
}

.footer-divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, var(--color-gold) 0%, transparent 100%);
  margin-bottom: 2rem;
}

.footer-text {
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-stone);
  letter-spacing: 0.02em;
}

.footer-highlight {
  color: var(--color-gold);
  font-weight: 500;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .nav-bar {
    padding: 1rem 1.5rem;
  }

  .report-content {
    padding: 2rem 1.5rem 4rem;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .section-title {
    font-size: 1.8rem;
  }

  .section-content {
    padding-left: 1.5rem;
  }

  .insights-grid,
  .trends-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== DARK MODE ===== */
@media (prefers-color-scheme: dark) {
  .analysis-page {
    background: linear-gradient(to bottom, #1a1a1a 0%, #0f0f0f 100%);
    color: #e0e0e0;
  }

  .nav-bar {
    background: rgba(26, 26, 26, 0.95);
    border-bottom-color: #333;
  }

  .back-button {
    color: #e0e0e0;
  }

  .hero-title,
  .section-title,
  .insight-category,
  .feature-text,
  .trend-value {
    color: #f5f5f5;
  }

  .summary-text {
    color: #d0d0d0;
  }

  .insight-card {
    background: #222;
    border-color: #333;
  }

  .insight-card:hover {
    border-color: var(--color-gold);
  }

  .trend-card {
    background: linear-gradient(135deg, #1f1f1f 0%, #252525 100%);
    border-color: #333;
  }
}
</style>
