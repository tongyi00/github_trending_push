import { onMounted, onUnmounted, nextTick, watch } from 'vue';
import * as echarts from 'echarts/core';

/**
 * ECharts 组合式函数
 * @param {Ref<HTMLElement>} chartRef - 图表容器的引用
 * @param {Ref<Object>} option - 图表配置项 (响应式)
 * @param {Ref<boolean>} loading - 加载状态 (可选)
 * @returns {Object} 图表实例和方法
 */
export function useChart(chartRef, option, loading) {
  let chartInstance = null;

  const initChart = () => {
    if (!chartRef.value) return;

    // 如果实例已存在，先销毁
    if (chartInstance) {
      chartInstance.dispose();
    }

    // 初始化实例
    chartInstance = echarts.init(chartRef.value);

    // 设置配置项
    if (option.value) {
      chartInstance.setOption(option.value);
    }
  };

  const resize = () => {
    chartInstance?.resize();
  };

  const setOption = (newOption) => {
    if (chartInstance && newOption) {
      chartInstance.setOption(newOption);
    }
  };

  onMounted(() => {
    // 稍微延迟初始化，确保 DOM 已准备好
    nextTick(() => {
      initChart();
      window.addEventListener('resize', resize);
    });
  });

  onUnmounted(() => {
    window.removeEventListener('resize', resize);
    chartInstance?.dispose();
    chartInstance = null;
  });

  // 监听配置项变化
  watch(option, (newOption) => {
    if (!chartInstance) {
      initChart();
    } else {
      setOption(newOption);
    }
  }, { deep: true });

  // 监听加载状态（加载完成后通常需要 resize）
  if (loading) {
    watch(loading, (newVal) => {
      if (!newVal) {
        nextTick(() => {
          resize();
        });
      }
    });
  }

  return {
    getInstance: () => chartInstance,
    resize,
    setOption,
    initChart
  };
}
