"""
HTML5图表渲染器
基于D3.js或Chart.js的图表渲染
"""

from __future__ import annotations
import json
from typing import Any
from pathlib import Path
import streamlit.components.v1 as components

from tetris_rl.ui.core.visualizer import ChartRenderer, RenderConfig


class HTML5ChartRenderer(ChartRenderer):
    """HTML5图表渲染器"""

    def __init__(self, config: RenderConfig):
        self.config = config
        self._data: dict[str, list[tuple[int, float]]] = {}
        self._html_template = self._load_template()

    def _load_template(self) -> str:
        """加载HTML模板"""
        template_path = Path(__file__).parent / "static" / "templates" / "charts.html"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        # 返回基本模板
        return self._get_basic_template()

    def _get_basic_template(self) -> str:
        """获取基本的图表模板"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { margin: 0; padding: 0; background: #0c0c10; }
                .chart-container {
                    padding: 20px;
                }
                .chart-title {
                    color: #fff;
                    margin-bottom: 10px;
                    font-family: sans-serif;
                }
                canvas {
                    background: #1a1a24;
                    border-radius: 8px;
                    padding: 10px;
                }
            </style>
        </head>
        <body>
            <div class="chart-container">
                <div class="chart-title">训练曲线</div>
                <canvas id="training-chart"></canvas>
            </div>
            <script>
                // 图表数据占位符
                const chartData = {{CHART_DATA}};
                const config = {{CONFIG_DATA}};

                // 初始化图表
                const ctx = document.getElementById('training-chart').getContext('2d');

                // 创建图表
                const chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        datasets: []
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: {
                                    color: '#fff'
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    color: '#2b2d3a'
                                },
                                ticks: {
                                    color: '#a0a0b0'
                                }
                            },
                            y: {
                                grid: {
                                    color: '#2b2d3a'
                                },
                                ticks: {
                                    color: '#a0a0b0'
                                }
                            }
                        }
                    }
                });

                // 更新图表数据
                function updateChart(data) {
                    if (!data || Object.keys(data).length === 0) return;

                    const datasets = [];
                    const colors = {
                        'loss': '#ff6b6b',
                        'score': '#4ecdc4',
                        'reward': '#45b7d1',
                        'value': '#96ceb4'
                    };

                    for (const [label, points] of Object.entries(data)) {
                        const color = colors[label] || '#ffffff';

                        datasets.push({
                            label: label,
                            data: points.map(p => ({x: p[0], y: p[1]})),
                            borderColor: color,
                            backgroundColor: color + '20',
                            fill: true,
                            tension: 0.1,
                            pointRadius: 0
                        });
                    }

                    chart.data.datasets = datasets;
                    chart.update('none');
                }

                // 初始更新
                updateChart(chartData);

                // 监听窗口大小变化
                window.addEventListener('resize', function() {
                    chart.resize();
                });
            </script>
        </body>
        </html>
        """

    def update_data(self, data: dict[str, list[tuple[int, float]]]) -> None:
        """更新图表数据"""
        self._data = data

    def render(self) -> str:
        """渲染图表为HTML"""
        config_data = {
            "theme": self.config.theme,
            "maxPoints": 500
        }

        html = self._html_template.replace(
            "{{CHART_DATA}}", json.dumps(self._data)
        ).replace(
            "{{CONFIG_DATA}}", json.dumps(config_data)
        )

        return html