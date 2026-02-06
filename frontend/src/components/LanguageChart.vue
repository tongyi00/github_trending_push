<script setup>
import { ref, onMounted, watch } from 'vue';
import * as echarts from 'echarts/core';
import { PieChart, BarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

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
let chartInstance = null;

const initChart = () => {
  if (!chartRef.value || props.loading) return;

  if (chartInstance) {
    chartInstance.dispose();
  }

  chartInstance = echarts.init(chartRef.value);

  const option = props.type === 'pie' ? getPieOption() : getBarOption();
  chartInstance.setOption(option);
};

const getPieOption = () => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'right',
    top: 'center',
    textStyle: {
      fontSize: 12
    }
  },
  series: [
    {
      name: 'Languages',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
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
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '10%',
    right: '5%',
    bottom: '10%',
    top: '5%',
    containLabel: true
  },
  xAxis: {
    type: 'value',
    axisLabel: {
      formatter: '{value}%'
    }
  },
  yAxis: {
    type: 'category',
    data: props.data.map(item => item.language || item.name).reverse(),
    axisLabel: {
      fontSize: 12
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
      barWidth: '60%'
    }
  ]
});

const getColorByIndex = (index) => {
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5470c6'
  ];
  return colors[index % colors.length];
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
});

watch(() => [props.data, props.loading], () => {
  initChart();
}, { deep: true });
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
</style>
