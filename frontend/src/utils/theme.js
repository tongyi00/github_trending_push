export const CLAUDE_COLORS = [
  '#D97757', // 品牌橙红
  '#788C5D', // 橄榄绿
  '#E0B06B', // 暖黄色
  '#6B6B6B', // 中灰色
  '#8E6E53', // 棕褐色
  '#5D7C8C', // 灰蓝色
  '#A65D57', // 砖红色
  '#8C8C5D', // 苔藓绿
  '#D9A057', // 杏黄色
  '#5D5D8C'  // 灰紫色
];

export const getColorByIndex = (index) => {
  return CLAUDE_COLORS[index % CLAUDE_COLORS.length];
};

export const CHART_TOOLTIP_STYLE = {
  backgroundColor: 'rgba(255, 255, 255, 0.95)',
  borderColor: '#E8E6DC',
  textStyle: {
    color: '#1D1D1D'
  },
  extraCssText: 'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-radius: 8px;'
};
