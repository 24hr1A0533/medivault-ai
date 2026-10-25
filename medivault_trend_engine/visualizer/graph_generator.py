"""
SVG and JSON Trend Graph Generator for Medical Trend Analysis.
Renders responsive inline SVG visualizations with clinical reference bands,
data points, trend line, and citation footnotes.
"""
from typing import List, Dict, Any, Optional
from medivault_trend_engine.schemas.trend_schema import (
    BiomarkerMeasurement,
    TrendGraphData,
    ReportCitation,
    TrendDirection,
)

class TrendGraphGenerator:
    """
    Renders SVG charts and structured JSON points for clinical biomarkers.
    """

    def generate_graph(
        self,
        biomarker_name: str,
        unit: str,
        measurements: List[BiomarkerMeasurement],
        normal_min: Optional[float] = None,
        normal_max: Optional[float] = None,
        direction: TrendDirection = TrendDirection.STABLE,
    ) -> TrendGraphData:
        sorted_m = sorted(measurements, key=lambda x: x.report_date)
        dates = [m.report_date for m in sorted_m]
        values = [m.value for m in sorted_m]

        citations: List[ReportCitation] = [
            ReportCitation(
                report_name=m.report_name,
                page_number=m.page_number,
                report_date=m.report_date,
                document_id=m.document_id,
            )
            for m in sorted_m
        ]

        json_points: List[Dict[str, Any]] = [
            {
                "date": m.report_date,
                "value": m.value,
                "unit": m.unit,
                "report_name": m.report_name,
                "page_number": m.page_number,
                "is_normal": (normal_min is None or m.value >= normal_min) and (normal_max is None or m.value <= normal_max),
            }
            for m in sorted_m
        ]

        svg = self._render_svg(
            biomarker_name=biomarker_name,
            unit=unit,
            dates=dates,
            values=values,
            normal_min=normal_min,
            normal_max=normal_max,
            direction=direction,
            citations=citations,
        )

        return TrendGraphData(
            biomarker_name=biomarker_name,
            unit=unit,
            dates=dates,
            values=values,
            normal_min=normal_min,
            normal_max=normal_max,
            svg_render=svg,
            json_points=json_points,
            citations=citations,
        )

    def _render_svg(
        self,
        biomarker_name: str,
        unit: str,
        dates: List[str],
        values: List[float],
        normal_min: Optional[float],
        normal_max: Optional[float],
        direction: TrendDirection,
        citations: List[ReportCitation],
    ) -> str:
        width = 640
        height = 320
        pad_left = 60
        pad_right = 40
        pad_top = 50
        pad_bottom = 60

        plot_w = width - pad_left - pad_right
        plot_h = height - pad_top - pad_bottom

        if not values:
            return f'<svg width="{width}" height="{height}"><text x="50%" y="50%" text-anchor="middle">No data</text></svg>'

        # Determine min and max for scaling
        all_vals = list(values)
        if normal_min is not None:
            all_vals.append(normal_min)
        if normal_max is not None:
            all_vals.append(normal_max)

        val_min = min(all_vals) * 0.9
        val_max = max(all_vals) * 1.1
        if val_min == val_max:
            val_min -= 1.0
            val_max += 1.0

        def get_x(idx: int) -> float:
            if len(values) == 1:
                return pad_left + plot_w / 2
            return pad_left + (idx / (len(values) - 1)) * plot_w

        def get_y(val: float) -> float:
            ratio = (val - val_min) / (val_max - val_min)
            return pad_top + (1.0 - ratio) * plot_h

        # Color based on trend direction
        line_color = "#3B82F6"  # Blue default
        if direction == TrendDirection.IMPROVING:
            line_color = "#10B981"  # Emerald green
        elif direction == TrendDirection.DETERIORATING:
            line_color = "#EF4444"  # Red

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: #0F172A; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; border-radius: 8px;">',
            f'<rect width="{width}" height="{height}" fill="#0F172A" rx="8"/>',
            # Title & Badge
            f'<text x="{pad_left}" y="30" fill="#F8FAFC" font-size="16" font-weight="600">{biomarker_name} Trend ({unit})</text>',
            f'<text x="{width - pad_right}" y="30" fill="{line_color}" font-size="12" font-weight="600" text-anchor="end">Status: {direction.value}</text>',
        ]

        # Normal reference range band (green translucent background)
        if normal_min is not None and normal_max is not None:
            y_top = get_y(normal_max)
            y_bot = get_y(normal_min)
            band_h = max(2.0, y_bot - y_top)
            svg_parts.append(
                f'<rect x="{pad_left}" y="{y_top}" width="{plot_w}" height="{band_h}" fill="#10B981" fill-opacity="0.12" />'
            )
            svg_parts.append(
                f'<line x1="{pad_left}" y1="{y_top}" x2="{width - pad_right}" y2="{y_top}" stroke="#10B981" stroke-dasharray="4" stroke-opacity="0.4"/>'
            )
            svg_parts.append(
                f'<line x1="{pad_left}" y1="{y_bot}" x2="{width - pad_right}" y2="{y_bot}" stroke="#10B981" stroke-dasharray="4" stroke-opacity="0.4"/>'
            )
            svg_parts.append(
                f'<text x="{width - pad_right - 4}" y="{y_top - 4}" fill="#10B981" font-size="10" text-anchor="end">Normal max: {normal_max}</text>'
            )

        # Plot axes
        svg_parts.append(
            f'<line x1="{pad_left}" y1="{pad_top + plot_h}" x2="{width - pad_right}" y2="{pad_top + plot_h}" stroke="#334155" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{pad_top + plot_h}" stroke="#334155" stroke-width="1"/>'
        )

        # Draw polyline connecting data points
        pts_str = " ".join([f"{get_x(i)},{get_y(v)}" for i, v in enumerate(values)])
        svg_parts.append(
            f'<polyline fill="none" stroke="{line_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{pts_str}" />'
        )

        # Draw points and value labels
        for i, (date, val) in enumerate(zip(dates, values)):
            cx = get_x(i)
            cy = get_y(val)
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="5" fill="{line_color}" stroke="#FFFFFF" stroke-width="2"/>'
            )
            svg_parts.append(
                f'<text x="{cx}" y="{cy - 10}" fill="#F8FAFC" font-size="11" font-weight="bold" text-anchor="middle">{val}</text>'
            )
            # Date label on x-axis
            date_short = date[-5:] if len(date) >= 10 else date
            svg_parts.append(
                f'<text x="{cx}" y="{pad_top + plot_h + 18}" fill="#94A3B8" font-size="10" text-anchor="middle">{date_short}</text>'
            )

        # Citation Footnote
        cite_str = "Sources: " + ", ".join([f"{c.report_name} ({c.report_date})" for c in citations[:2]])
        if len(citations) > 2:
            cite_str += f" + {len(citations) - 2} more"
        svg_parts.append(
            f'<text x="{pad_left}" y="{height - 12}" fill="#64748B" font-size="9">{cite_str}</text>'
        )

        svg_parts.append("</svg>")
        return "".join(svg_parts)
