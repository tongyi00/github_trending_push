<script setup>
import { ref, computed } from 'vue';
import * as echarts from 'echarts/core';
import { PieChart, BarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { useChart } from '../composables/useChart';
import { CLAUDE_COLORS, getColorByIndex, CHART_TOOLTIP_STYLE } from '../utils/theme';

echarts.use([PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer]);

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'pie' // 'pie' or 'bar'
  }
});

const chartRef = ref(null);
const loadingRef = computed(() => props.loading);

const getPieOption = () => ({
  color: CLAUDE_COLORS,
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)',
    ...CHART_TOOLTIP_STYLE
  },
  legend: {
    orient: 'vertical',
    right: '1%',
    top: '0%',
    itemGap: 14,
    icon: 'circle',
    textStyle: {
      fontSize: 14,
      color: 'inherit'
    }
  },
  grid: {
    top: 0,
    bottom: 20,
    containLabel: true
  },
  series: [
    {
      name: 'Languages',
      type: 'pie',
      radius: ['40%', '60%'],
      center: ['40%', '33%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      labelLine: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold',
          color: 'inherit',
          formatter: '{b}\n{d}%'
        },
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.1)'
        }
      },
      data: props.data.map((item, index) => ({
        value: item.count || item.percentage,
        name: item.language || item.name,
        itemStyle: {
          color: getColorByIndex(index)
        }
      }))
    }
  ]
});

const getBarOption = () => ({
  color: CLAUDE_COLORS,
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    },
    ...CHART_TOOLTIP_STYLE
  },
  grid: {
    left: '5%',
    right: '5%',
    bottom: '5%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'value',
    axisLabel: {
      formatter: '{value}%',
      color: '#6B6B6B'
    },
    splitLine: {
      lineStyle: {
        color: '#E8E6DC',
        type: 'dashed'
      }
    }
  },
  yAxis: {
    type: 'category',
    data: props.data.map(item => item.language || item.name).reverse(),
    axisLabel: {
      fontSize: 12,
      color: '#6B6B6B'
    },
    axisLine: {
      lineStyle: {
        color: '#E8E6DC'
      }
    }
  },
  series: [
    {
      type: 'bar',
      data: props.data.map((item, index) => ({
        value: item.percentage || item.count,
        itemStyle: {
          color: getColorByIndex(props.data.length - 1 - index),
          borderRadius: [0, 4, 4, 0]
        }
      })).reverse(),
      barWidth: '50%'
    }
  ]
});

const chartOption = computed(() => {
  return props.type === 'pie' ? getPieOption() : getBarOption();
});

useChart(chartRef, chartOption, loadingRef);
</script>

<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

/* 深色模式下的图表样式适配 */
:global(.dark) .chart-container {
  /* ECharts 内部元素颜色通过 JS 控制，这里主要处理容器 */
}
</style>
