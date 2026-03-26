"""
Chart Generator with Template Colors
"""

import io
from typing import Dict, Optional
import plotly.graph_objects as go


class ChartGenerator:
    """Generates charts matching template colors"""
    
    def __init__(self, color_scheme: Optional[Dict] = None):
        default_colors = ['#6366F1', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#EF4444', '#06B6D4', '#84CC16']
        
        if color_scheme and 'colors' in color_scheme:
            self.colors = color_scheme['colors']
        else:
            self.colors = default_colors
        
        # Background color from template
        self.bg_color = 'rgba(15, 23, 42, 0.8)'  # Semi-transparent dark
        self.text_color = '#F8FAFC'
    
    def set_template_colors(self, template_data: Dict):
        """Update colors from template"""
        colors = template_data.get('colors', {})
        
        self.colors = [
            colors.get('primary', '#6366F1'),
            colors.get('secondary', '#8B5CF6'),
            colors.get('accent', '#EC4899'),
            '#10B981', '#F59E0B', '#EF4444', '#06B6D4', '#84CC16'
        ]
        
        self.text_color = colors.get('text_primary', '#F8FAFC')
    
    def create_bar_chart(self, data: Dict, width: int = 800, height: int = 500) -> bytes:
        """Create bar chart"""
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        fig = go.Figure()
        
        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Bar(
                name=dataset.get('name', f'Series {i+1}'),
                x=labels,
                y=dataset.get('values', []),
                marker_color=self.colors[i % len(self.colors)]
            ))
        
        self._apply_layout(fig, data, width, height)
        fig.update_layout(barmode='group')
        
        return fig.to_image(format='png', engine='kaleido')
    
    def create_line_chart(self, data: Dict, width: int = 800, height: int = 500) -> bytes:
        """Create line chart"""
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        fig = go.Figure()
        
        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Scatter(
                name=dataset.get('name', f'Series {i+1}'),
                x=labels,
                y=dataset.get('values', []),
                mode='lines+markers',
                line=dict(color=self.colors[i % len(self.colors)], width=3),
                marker=dict(size=8)
            ))
        
        self._apply_layout(fig, data, width, height)
        
        return fig.to_image(format='png', engine='kaleido')
    
    def create_pie_chart(self, data: Dict, width: int = 700, height: int = 500) -> bytes:
        """Create pie chart"""
        labels = data.get('labels', [])
        values = data.get('datasets', [{}])[0].get('values', [])
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=self.colors[:len(labels)]),
            textinfo='label+percent',
            textfont=dict(color='white', size=14)
        )])
        
        self._apply_layout(fig, data, width, height)
        
        return fig.to_image(format='png', engine='kaleido')
    
    def create_area_chart(self, data: Dict, width: int = 800, height: int = 500) -> bytes:
        """Create area chart"""
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        fig = go.Figure()
        
        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Scatter(
                name=dataset.get('name', f'Series {i+1}'),
                x=labels,
                y=dataset.get('values', []),
                fill='tozeroy',
                mode='lines',
                line=dict(color=self.colors[i % len(self.colors)], width=2)
            ))
        
        self._apply_layout(fig, data, width, height)
        
        return fig.to_image(format='png', engine='kaleido')
    
    def create_scatter_chart(self, data: Dict, width: int = 800, height: int = 500) -> bytes:
        """Create scatter chart"""
        datasets = data.get('datasets', [])
        
        fig = go.Figure()
        
        for i, dataset in enumerate(datasets):
            x_vals = dataset.get('x_values', list(range(len(dataset.get('values', [])))))
            y_vals = dataset.get('values', [])
            
            fig.add_trace(go.Scatter(
                name=dataset.get('name', f'Series {i+1}'),
                x=x_vals,
                y=y_vals,
                mode='markers',
                marker=dict(
                    color=self.colors[i % len(self.colors)],
                    size=12,
                    opacity=0.7
                )
            ))
        
        self._apply_layout(fig, data, width, height)
        
        return fig.to_image(format='png', engine='kaleido')
    
    def _apply_layout(self, fig, data: Dict, width: int, height: int):
        """Apply common layout settings"""
        fig.update_layout(
            title=dict(
                text=data.get('title', ''),
                font=dict(color=self.text_color, size=18)
            ),
            xaxis_title=dict(
                text=data.get('x_axis_label', ''),
                font=dict(color=self.text_color)
            ),
            yaxis_title=dict(
                text=data.get('y_axis_label', ''),
                font=dict(color=self.text_color)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.text_color),
            width=width,
            height=height,
            margin=dict(l=60, r=40, t=60, b=60),
            legend=dict(
                font=dict(color=self.text_color),
                bgcolor='rgba(0,0,0,0)'
            ),
            xaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.2)',
                tickfont=dict(color=self.text_color)
            ),
            yaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.2)',
                tickfont=dict(color=self.text_color)
            )
        )
    
    def create_chart(self, chart_type: str, data: Dict, width: int = 800, height: int = 500) -> bytes:
        """Create chart by type"""
        creators = {
            'bar': self.create_bar_chart,
            'line': self.create_line_chart,
            'pie': self.create_pie_chart,
            'area': self.create_area_chart,
            'scatter': self.create_scatter_chart,
        }
        
        creator = creators.get(chart_type.lower(), self.create_bar_chart)
        return creator(data, width, height)
