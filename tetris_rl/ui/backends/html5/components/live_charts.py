"""
Streamlit实时图表组件
"""

import streamlit.components.v1 as components
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def live_charts(data: Dict[str, List[Tuple[int, float]]],
                config: Optional[Dict[str, Any]] = None,
                key: str = "live_charts", height: int = 400) -> None:
    """
    实时图表组件

    Args:
        data: 图表数据，键为数据系列名称，值为(x, y)坐标列表
        config: 图表配置
        key: 组件唯一键
        height: 组件高度
    """
    if config is None:
        config = {}

    # 加载HTML模板
    html_path = Path(__file__).parent.parent / "static" / "templates" / "charts.html"
    if not html_path.exists():
        # 使用ChartRenderer中的基本模板
        from ..chart_renderer import HTML5ChartRenderer
        from ...core.visualizer import RenderConfig

        render_config = RenderConfig(
            theme=config.get("theme", "dark")
        )

        renderer = HTML5ChartRenderer(render_config)
        renderer.update_data(data)
        html_content = renderer.render()
    else:
        html_content = html_path.read_text(encoding="utf-8")

        config_data = {
            "theme": config.get("theme", "dark"),
            "maxPoints": config.get("max_points", 500),
            "title": config.get("title", "训练曲线")
        }

        # 注入数据
        html_content = html_content.replace(
            "{{CHART_DATA}}",
            json.dumps(data, separators=(',', ':'))
        ).replace(
            "{{CONFIG_DATA}}",
            json.dumps(config_data, separators=(',', ':'))
        )

    # 渲染组件
    components.html(
        html_content,
        height=height,
        width=800,
        key=key
    )


def create_multi_chart(data_sets: Dict[str, Dict[str, List[Tuple[int, float]]]],
                       config: Optional[Dict[str, Any]] = None,
                       key: str = "multi_chart", height: int = 500) -> None:
    """
    多图表组件

    Args:
        data_sets: 多个数据集，键为图表标题，值为数据字典
        config: 图表配置
        key: 组件唯一键
        height: 组件高度
    """
    if config is None:
        config = {}

    # 创建多图表HTML
    html_content = create_multi_chart_html(data_sets, config)

    # 渲染组件
    components.html(
        html_content,
        height=height,
        width=800,
        key=key
    )


def create_multi_chart_html(data_sets: Dict[str, Dict[str, List[Tuple[int, float]]]],
                            config: Dict[str, Any]) -> str:
    """创建多图表HTML"""
    data_json = json.dumps(data_sets, separators=(',', ':'))
    config_json = json.dumps(config, separators=(',', ':'))

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background: #0c0c10;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            .chart-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
            }}
            .chart-container {{
                background: #1a1a24;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }}
            .chart-title {{
                color: #fff;
                margin: 0 0 15px 0;
                font-size: 16px;
                font-weight: 600;
            }}
            canvas {{
                width: 100% !important;
                height: 300px !important;
            }}
            .no-data {{
                color: #a0a0b0;
                text-align: center;
                padding: 40px;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="chart-grid" id="chart-grid">
            <!-- 图表将在这里动态创建 -->
        </div>

        <script>
            const dataSets = {data_json};
            const config = {config_json};

            // 颜色调色板
            const colorPalette = [
                '#4ecdc4', '#ff6b6b', '#45b7d1', '#96ceb4',
                '#ffd166', '#118ab2', '#ef476f', '#06d6a0'
            ];

            // 初始化所有图表
            function initCharts() {{
                const grid = document.getElementById('chart-grid');
                grid.innerHTML = '';

                let chartIndex = 0;
                const charts = {{}};

                for (const [title, data] of Object.entries(dataSets)) {{
                    // 创建图表容器
                    const container = document.createElement('div');
                    container.className = 'chart-container';

                    const titleEl = document.createElement('div');
                    titleEl.className = 'chart-title';
                    titleEl.textContent = title;
                    container.appendChild(titleEl);

                    const canvas = document.createElement('canvas');
                    container.appendChild(canvas);

                    grid.appendChild(container);

                    // 创建图表
                    const ctx = canvas.getContext('2d');
                    charts[title] = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            datasets: createDatasets(data, chartIndex)
                        }},
                        options: getChartOptions(title)
                    }});

                    chartIndex++;
                }}

                // 存储图表引用
                window.charts = charts;

                // 监听窗口大小变化
                window.addEventListener('resize', function() {{
                    for (const chart of Object.values(charts)) {{
                        chart.resize();
                    }}
                }});
            }}

            // 创建数据集
            function createDatasets(data, startColorIndex) {{
                const datasets = [];
                let colorIndex = startColorIndex;

                for (const [label, points] of Object.entries(data)) {{
                    const color = colorPalette[colorIndex % colorPalette.length];
                    colorIndex++;

                    datasets.push({{
                        label: label,
                        data: points.map(p => ({{x: p[0], y: p[1]}})),
                        borderColor: color,
                        backgroundColor: color + '20',
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2
                    }});
                }}

                return datasets;
            }}

            // 获取图表选项
            function getChartOptions(title) {{
                return {{
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {{
                        duration: 0
                    }},
                    plugins: {{
                        legend: {{
                            labels: {{
                                color: '#fff',
                                font: {{
                                    size: 12
                                }}
                            }}
                        }},
                        title: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{
                                color: '#2b2d3a',
                                drawBorder: false
                            }},
                            ticks: {{
                                color: '#a0a0b0',
                                maxTicksLimit: 8
                            }},
                            title: {{
                                display: true,
                                text: '更新次数',
                                color: '#a0a0b0'
                            }}
                        }},
                        y: {{
                            grid: {{
                                color: '#2b2d3a',
                                drawBorder: false
                            }},
                            ticks: {{
                                color: '#a0a0b0',
                                maxTicksLimit: 6
                            }},
                            title: {{
                                display: true,
                                text: getYAxisLabel(title),
                                color: '#a0a0b0'
                            }}
                        }}
                    }}
                }};
            }}

            // 获取Y轴标签
            function getYAxisLabel(title) {{
                const lowerTitle = title.toLowerCase();
                if (lowerTitle.includes('loss')) return '损失值';
                if (lowerTitle.includes('score')) return '得分';
                if (lowerTitle.includes('reward')) return '奖励';
                if (lowerTitle.includes('value')) return '价值';
                return '数值';
            }}

            // 更新图表数据
            function updateChartData(title, newData) {{
                if (!window.charts || !window.charts[title]) return;

                const chart = window.charts[title];
                const datasets = chart.data.datasets;

                // 更新现有数据集或添加新数据集
                for (const [label, points] of Object.entries(newData)) {{
                    const existingIndex = datasets.findIndex(ds => ds.label === label);
                    if (existingIndex >= 0) {{
                        // 合并数据（限制最大点数）
                        const existingPoints = datasets[existingIndex].data;
                        const newPoints = points.map(p => ({{x: p[0], y: p[1]}}));
                        const combined = [...existingPoints, ...newPoints];

                        // 限制数据点数量
                        const maxPoints = config.maxPoints || 500;
                        if (combined.length > maxPoints) {{
                            combined.splice(0, combined.length - maxPoints);
                        }}

                        datasets[existingIndex].data = combined;
                    }} else {{
                        // 添加新数据集
                        const colorIndex = datasets.length;
                        const color = colorPalette[colorIndex % colorPalette.length];

                        datasets.push({{
                            label: label,
                            data: points.map(p => ({{x: p[0], y: p[1]}})),
                            borderColor: color,
                            backgroundColor: color + '20',
                            fill: true,
                            tension: 0.1,
                            pointRadius: 0,
                            borderWidth: 2
                        }});
                    }}
                }}

                chart.update('none');
            }}

            // 页面加载完成后初始化
            window.addEventListener('load', initCharts);

            // 暴露更新函数给父页面
            window.updateChartData = updateChartData;
        </script>
    </body>
    </html>
    """