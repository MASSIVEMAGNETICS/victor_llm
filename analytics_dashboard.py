"""
analytics_dashboard.py - Visual Analytics & Monitoring
Part of the DataBlob Godmode Toolkit for Victor LLM

Features:
- Real-time data blob inspection dashboard
- Data quality heatmaps (ASCII + HTML)
- Training progress monitoring
- Dataset statistics and distribution visualization
- Performance bottleneck identification
- Standalone HTTP server for web-based dashboard
"""

from __future__ import annotations

import html
import json
import logging
import math
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

Record = Dict[str, Any]


# ---------------------------------------------------------------------------
# ASCII chart helpers
# ---------------------------------------------------------------------------

class ASCIIChart:
    """Generate simple ASCII bar charts."""

    WIDTH = 40

    @classmethod
    def bar(cls, value: float, max_value: float, label: str = "", width: int = 0) -> str:
        w = width or cls.WIDTH
        if max_value == 0:
            filled = 0
        else:
            filled = int((value / max_value) * w)
        bar = "█" * filled + "░" * (w - filled)
        pct = (value / max_value * 100) if max_value else 0
        label_part = f"{label:<20}" if label else ""
        return f"{label_part}[{bar}] {value:.2f} ({pct:.1f}%)"

    @classmethod
    def histogram(
        cls,
        values: List[float],
        bins: int = 10,
        title: str = "",
    ) -> str:
        if not values:
            return "(no data)"
        mn, mx = min(values), max(values)
        if mn == mx:
            return f"All values = {mn}"
        bin_width = (mx - mn) / bins
        counts = [0] * bins
        for v in values:
            idx = min(int((v - mn) / bin_width), bins - 1)
            counts[idx] += 1
        max_count = max(counts) or 1

        lines = []
        if title:
            lines.append(title)
            lines.append("-" * (cls.WIDTH + 30))
        for i, count in enumerate(counts):
            lo = mn + i * bin_width
            hi = lo + bin_width
            lines.append(cls.bar(count, max_count, f"[{lo:.2f}-{hi:.2f})"))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quality heatmap
# ---------------------------------------------------------------------------

class QualityHeatmap:
    """Generate quality heatmap visualisations."""

    PALETTE = ["🟩", "🟨", "🟧", "🟥"]  # good -> bad

    def ascii_heatmap(
        self, null_pcts: Dict[str, float], title: str = "NULL % Heatmap"
    ) -> str:
        """ASCII heatmap of null percentages per field."""
        if not null_pcts:
            return "(no data)"
        lines = [title, "=" * 60]
        for field, pct in sorted(null_pcts.items(), key=lambda x: -x[1]):
            idx = min(int(pct / 25), 3)
            symbol = self.PALETTE[idx]
            lines.append(f"  {symbol}  {field:<30} {pct:5.1f}% null")
        lines.append("  Legend: 🟩 <25%  🟨 25-49%  🟧 50-74%  🟥 ≥75%")
        return "\n".join(lines)

    def html_heatmap(
        self, null_pcts: Dict[str, float], title: str = "NULL % Heatmap"
    ) -> str:
        """HTML heatmap of null percentages per field."""
        rows = ""
        for field_name, pct in sorted(null_pcts.items(), key=lambda x: -x[1]):
            color = self._pct_to_color(pct)
            escaped = html.escape(field_name)
            rows += (
                f"<tr><td style='padding:4px 8px'>{escaped}</td>"
                f"<td style='padding:4px 8px;background:{color};text-align:center'>"
                f"{pct:.1f}%</td></tr>\n"
            )

        return f"""<div class='heatmap'>
<h3>{html.escape(title)}</h3>
<table border='1' cellspacing='0' style='border-collapse:collapse;font-family:monospace'>
<thead><tr><th>Field</th><th>Null %</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>"""

    @staticmethod
    def _pct_to_color(pct: float) -> str:
        if pct < 25:
            return "#90EE90"  # light green
        if pct < 50:
            return "#FFD700"  # gold
        if pct < 75:
            return "#FFA500"  # orange
        return "#FF6B6B"      # red


# ---------------------------------------------------------------------------
# Training progress display
# ---------------------------------------------------------------------------

class TrainingProgressDisplay:
    """Display training metrics in the terminal."""

    def print_epoch(
        self,
        epoch: int,
        max_epochs: int,
        train_loss: float,
        val_loss: Optional[float] = None,
        lr: float = 0.0,
        elapsed: float = 0.0,
    ) -> None:
        val_str = f"{val_loss:.4f}" if val_loss is not None else "N/A  "
        bar_filled = int((epoch / max_epochs) * 30)
        bar = "=" * bar_filled + ">" + " " * (30 - bar_filled)
        print(
            f"\r  [{bar}] Epoch {epoch:3d}/{max_epochs}"
            f"  train_loss={train_loss:.4f}  val_loss={val_str}"
            f"  lr={lr:.2e}  {elapsed:.1f}s",
            end="",
            flush=True,
        )
        if epoch == max_epochs:
            print()

    def print_metrics_table(
        self, history: List[Dict[str, Any]]
    ) -> None:
        if not history:
            return
        header = f"{'Epoch':>6} {'Train Loss':>12} {'Val Loss':>12} {'LR':>10} {'Time(s)':>8}"
        print(header)
        print("-" * len(header))
        for m in history:
            val = f"{m['val_loss']:.4f}" if m.get("val_loss") is not None else "N/A"
            print(
                f"{m['epoch']:>6} {m['train_loss']:>12.4f} {val:>12}"
                f" {m.get('learning_rate', 0):>10.2e} {m.get('elapsed_seconds', 0):>8.1f}"
            )


# ---------------------------------------------------------------------------
# Dataset statistics visualizer
# ---------------------------------------------------------------------------

class DatasetStatsVisualizer:
    """Visualize dataset field statistics."""

    def summary(self, field_stats: List[Dict[str, Any]]) -> str:
        """Return a formatted text summary of field statistics."""
        if not field_stats:
            return "(no field stats)"
        lines = [
            f"{'Field':<30} {'Type':<20} {'Nulls':>6} {'Unique':>8}  {'Stats'}",
            "-" * 90,
        ]
        for s in field_stats:
            name = str(s.get("field", ""))[:30]
            ftype = str(s.get("type", ""))[:20]
            nulls = f"{s.get('null_pct', 0):.1f}%"
            unique = str(s.get("unique_count", ""))
            extra = ""
            if "mean" in s:
                extra = f"mean={s['mean']:.3f} min={s['min']:.3f} max={s['max']:.3f}"
            elif "avg_length" in s:
                extra = f"avg_len={s['avg_length']:.1f}"
            elif "top_values" in s:
                top = s["top_values"][:3]
                extra = "top: " + ", ".join(f"{k}({v})" for k, v in top)
            lines.append(f"{name:<30} {ftype:<20} {nulls:>6} {unique:>8}  {extra}")
        return "\n".join(lines)

    def distribution_chart(
        self, field_stats: List[Dict[str, Any]], field_name: str
    ) -> str:
        """ASCII bar chart for a categorical or numeric field."""
        stat = next((s for s in field_stats if s.get("field") == field_name), None)
        if stat is None:
            return f"Field '{field_name}' not found."
        if "top_values" in stat:
            max_count = stat["top_values"][0][1] if stat["top_values"] else 1
            lines = [f"Distribution: {field_name}"]
            for val, count in stat["top_values"]:
                lines.append(ASCIIChart.bar(count, max_count, str(val)[:20]))
            return "\n".join(lines)
        if "mean" in stat:
            return (
                f"Numeric field: {field_name}\n"
                f"  min={stat.get('min'):.4f}  max={stat.get('max'):.4f}\n"
                f"  mean={stat.get('mean'):.4f}  std={stat.get('std_dev', 0):.4f}"
            )
        return f"No distribution data for '{field_name}'."


# ---------------------------------------------------------------------------
# HTML Dashboard generator
# ---------------------------------------------------------------------------

class HTMLDashboard:
    """Generate a self-contained HTML analytics dashboard."""

    def generate(
        self,
        title: str = "DataBlob Godmode Dashboard",
        dataset_stats: Optional[List[Dict[str, Any]]] = None,
        null_pcts: Optional[Dict[str, float]] = None,
        training_history: Optional[List[Dict[str, Any]]] = None,
        quality_score: float = 0.0,
        anomaly_count: int = 0,
        record_count: int = 0,
        manifest: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return full HTML string for the dashboard."""
        hm = QualityHeatmap()
        heatmap_html = hm.html_heatmap(null_pcts or {}, "Field Null Percentages")

        stats_rows = self._stats_table(dataset_stats or [])
        training_chart = self._training_chart(training_history or [])
        manifest_section = self._manifest_section(manifest or {})

        ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        quality_color = "#90EE90" if quality_score >= 80 else "#FFD700" if quality_score >= 50 else "#FF6B6B"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; margin: 0; background: #0d1117; color: #c9d1d9; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
    h1 {{ color: #58a6ff; border-bottom: 2px solid #21262d; padding-bottom: 10px; }}
    h2 {{ color: #79c0ff; }}
    h3 {{ color: #d2a8ff; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin: 12px 0; }}
    .metric {{ display: inline-block; background: #21262d; border-radius: 6px; padding: 10px 18px; margin: 6px; text-align: center; }}
    .metric .value {{ font-size: 2em; font-weight: bold; color: #58a6ff; }}
    .metric .label {{ font-size: 0.85em; color: #8b949e; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #21262d; }}
    th {{ background: #21262d; color: #79c0ff; }}
    tr:hover {{ background: #1c2128; }}
    .quality-badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-weight: bold; background: {quality_color}; color: #000; }}
    .chart-bar {{ height: 20px; background: #58a6ff; margin: 2px 0; transition: width 0.5s; }}
    pre {{ background: #0d1117; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 0.85em; }}
    .timestamp {{ color: #8b949e; font-size: 0.85em; }}
    .heatmap td {{ color: #000; font-weight: bold; }}
    .heatmap th {{ color: #79c0ff; }}
  </style>
</head>
<body>
<div class="container">
  <h1>🧠 {html.escape(title)}</h1>
  <p class="timestamp">Generated: {ts}</p>

  <div class="card">
    <h2>📊 Overview</h2>
    <div class="metric"><div class="value">{record_count:,}</div><div class="label">Records</div></div>
    <div class="metric"><div class="value">{len(dataset_stats or [])}</div><div class="label">Fields</div></div>
    <div class="metric"><div class="value">{anomaly_count}</div><div class="label">Anomalies</div></div>
    <div class="metric"><div class="value"><span class="quality-badge">{quality_score:.1f}</span></div><div class="label">Quality Score</div></div>
  </div>

  <div class="card">
    {heatmap_html}
  </div>

  <div class="card">
    <h2>📋 Field Statistics</h2>
    <table>
      <thead><tr><th>Field</th><th>Type</th><th>Null %</th><th>Unique</th><th>Min</th><th>Max</th><th>Mean</th></tr></thead>
      <tbody>
        {stats_rows}
      </tbody>
    </table>
  </div>

  {training_chart}

  <div class="card">
    <h2>📄 Dataset Manifest</h2>
    {manifest_section}
  </div>
</div>
</body>
</html>"""

    @staticmethod
    def _stats_table(field_stats: List[Dict[str, Any]]) -> str:
        rows = ""
        for s in field_stats:
            name = html.escape(str(s.get("field", "")))
            ftype = html.escape(str(s.get("type", "")))
            null_pct = f"{s.get('null_pct', 0):.1f}%"
            unique = str(s.get("unique_count", ""))
            mn = f"{s.get('min', '')}" if "min" in s else ""
            mx = f"{s.get('max', '')}" if "max" in s else ""
            mean = f"{s.get('mean', ''):.3f}" if "mean" in s else ""
            rows += f"<tr><td>{name}</td><td>{ftype}</td><td>{null_pct}</td><td>{unique}</td><td>{mn}</td><td>{mx}</td><td>{mean}</td></tr>\n"
        return rows

    @staticmethod
    def _training_chart(history: List[Dict[str, Any]]) -> str:
        if not history:
            return ""
        losses = [m.get("train_loss", 0) for m in history]
        val_losses = [m.get("val_loss") for m in history]
        max_loss = max((l for l in losses + [v for v in val_losses if v is not None]), default=1.0) or 1.0

        rows = ""
        for m in history:
            e = m.get("epoch", 0)
            tl = m.get("train_loss", 0)
            vl = m.get("val_loss")
            bar_w = int((tl / max_loss) * 300)
            val_str = f"{vl:.4f}" if vl is not None else "N/A"
            rows += (
                f"<tr><td>{e}</td>"
                f"<td><div class='chart-bar' style='width:{bar_w}px'></div>{tl:.4f}</td>"
                f"<td>{val_str}</td></tr>\n"
            )

        return f"""<div class="card">
  <h2>📈 Training Progress</h2>
  <table>
    <thead><tr><th>Epoch</th><th>Train Loss</th><th>Val Loss</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    @staticmethod
    def _manifest_section(manifest: Dict[str, Any]) -> str:
        if not manifest:
            return "<p>No manifest available.</p>"
        escaped = html.escape(json.dumps(manifest, indent=2, default=str))
        return f"<pre>{escaped}</pre>"


# ---------------------------------------------------------------------------
# Dashboard HTTP server
# ---------------------------------------------------------------------------

class DashboardServer:
    """
    Minimal HTTP server that serves the HTML dashboard.
    Non-blocking: runs in a background thread.
    """

    def __init__(
        self,
        dashboard: HTMLDashboard,
        dashboard_kwargs: Optional[Dict[str, Any]] = None,
        host: str = "127.0.0.1",
        port: int = 8787,
    ) -> None:
        self._dashboard = dashboard
        self._kwargs: Dict[str, Any] = dashboard_kwargs or {}
        self._host = host
        self._port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._html_cache: str = ""

    def update(self, **kwargs: Any) -> None:
        """Update dashboard data and regenerate HTML."""
        self._kwargs.update(kwargs)
        self._html_cache = self._dashboard.generate(**self._kwargs)

    def start(self) -> None:
        """Start the server in a background thread."""
        self._html_cache = self._dashboard.generate(**self._kwargs)
        html_ref = [self._html_cache]
        server_ref = [self]

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                content = server_ref[0]._html_cache.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def log_message(self, *args: Any) -> None:  # suppress default logging
                pass

        self._server = HTTPServer((self._host, self._port), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("Dashboard server started at http://%s:%d", self._host, self._port)
        print(f"📊 Dashboard: http://{self._host}:{self._port}")

    def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.shutdown()
            logger.info("Dashboard server stopped.")

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"


# ---------------------------------------------------------------------------
# Main AnalyticsDashboard facade
# ---------------------------------------------------------------------------

class AnalyticsDashboard:
    """
    High-level analytics and monitoring facade.

    Usage::

        dash = AnalyticsDashboard()
        dash.update_dataset(field_stats, null_pcts, quality_score, record_count)
        dash.update_training(metrics_history)
        dash.print_summary()           # terminal output
        html = dash.render_html()      # full HTML string
        dash.serve(port=8787)          # start web server
    """

    def __init__(self) -> None:
        self._heatmap = QualityHeatmap()
        self._stats_viz = DatasetStatsVisualizer()
        self._progress = TrainingProgressDisplay()
        self._html_dash = HTMLDashboard()
        self._server: Optional[DashboardServer] = None

        # State
        self._field_stats: List[Dict[str, Any]] = []
        self._null_pcts: Dict[str, float] = {}
        self._training_history: List[Dict[str, Any]] = []
        self._quality_score: float = 0.0
        self._anomaly_count: int = 0
        self._record_count: int = 0
        self._manifest: Dict[str, Any] = {}
        self._title: str = "DataBlob Godmode Dashboard"

    def update_dataset(
        self,
        field_stats: List[Dict[str, Any]],
        null_pcts: Dict[str, float],
        quality_score: float,
        record_count: int,
        anomaly_count: int = 0,
        manifest: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._field_stats = field_stats
        self._null_pcts = null_pcts
        self._quality_score = quality_score
        self._record_count = record_count
        self._anomaly_count = anomaly_count
        if manifest:
            self._manifest = manifest
        if self._server:
            self._server.update(**self._dash_kwargs())

    def update_training(
        self, history: List[Dict[str, Any]]
    ) -> None:
        self._training_history = history
        if self._server:
            self._server.update(**self._dash_kwargs())

    def print_summary(self) -> None:
        """Print a summary to stdout."""
        print(f"\n{'=' * 60}")
        print(f"  {self._title}")
        print(f"  Records: {self._record_count:,}  |  Quality: {self._quality_score:.1f}/100  |  Anomalies: {self._anomaly_count}")
        print(f"{'=' * 60}")
        if self._null_pcts:
            print(self._heatmap.ascii_heatmap(self._null_pcts))
        if self._field_stats:
            print("\n" + self._stats_viz.summary(self._field_stats))
        if self._training_history:
            print("\nTraining History:")
            self._progress.print_metrics_table(self._training_history)

    def render_html(self, title: Optional[str] = None) -> str:
        """Return a complete HTML dashboard string."""
        kwargs = self._dash_kwargs()
        if title:
            kwargs["title"] = title
        return self._html_dash.generate(**kwargs)

    def save_html(self, path: Union[str, Path]) -> Path:
        """Save HTML dashboard to disk."""
        path = Path(path)
        path.write_text(self.render_html(), encoding="utf-8")
        logger.info("Dashboard saved to %s", path)
        return path

    def serve(
        self,
        host: str = "127.0.0.1",
        port: int = 8787,
    ) -> DashboardServer:
        """Start a background HTTP server for the dashboard."""
        if self._server:
            self._server.stop()
        self._server = DashboardServer(
            self._html_dash,
            self._dash_kwargs(),
            host=host,
            port=port,
        )
        self._server.start()
        return self._server

    def stop_server(self) -> None:
        if self._server:
            self._server.stop()
            self._server = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _dash_kwargs(self) -> Dict[str, Any]:
        return {
            "title": self._title,
            "dataset_stats": self._field_stats,
            "null_pcts": self._null_pcts,
            "training_history": self._training_history,
            "quality_score": self._quality_score,
            "anomaly_count": self._anomaly_count,
            "record_count": self._record_count,
            "manifest": self._manifest,
        }
