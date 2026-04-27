"""3D attack-graph renderer for the Streamlit UI.

Plots reconstructed events along three axes:

  X — chronological order
  Y — kill-chain phase (canonical MITRE ordering)
  Z — severity score

Each point is annotated with the techniques and description so an analyst
can hover and read the story without leaving the graph.
"""
from __future__ import annotations

from typing import List

import pandas as pd
import plotly.graph_objects as go

from neural_architect.core.models import AttackEvent, Severity

_SEVERITY_SCORE = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

_PHASE_ORDER = [
    "reconnaissance",
    "resource_development",
    "initial_access",
    "execution",
    "persistence",
    "privilege_escalation",
    "defense_evasion",
    "credential_access",
    "discovery",
    "lateral_movement",
    "collection",
    "command_and_control",
    "exfiltration",
    "impact",
]
_PHASE_LABEL = {p: p.replace("_", " ").title() for p in _PHASE_ORDER}
_PHASE_INDEX = {p: i for i, p in enumerate(_PHASE_ORDER)}


def render_3d_attack_graph(events: List[AttackEvent]):
    """Build a Plotly 3D scatter from a reconstructed AttackChain's events.

    Returns ``None`` if there are no events; otherwise returns a ``go.Figure``
    ready to hand to ``st.plotly_chart``.
    """
    if not events:
        return None

    rows = []
    for idx, e in enumerate(events):
        phase = e.phase.value
        techniques = ", ".join(t.name for t in e.techniques) or "—"
        ts_label = e.timestamp.isoformat() if e.timestamp else f"step {idx + 1}"
        rows.append(
            {
                "order": idx,
                "phase": phase,
                "phase_label": _PHASE_LABEL.get(phase, phase),
                "phase_idx": _PHASE_INDEX.get(phase, 0),
                "severity_score": _SEVERITY_SCORE.get(e.severity, 2),
                "ts_label": ts_label,
                "techniques": techniques,
                "description": e.description,
            }
        )

    df = pd.DataFrame(rows)

    hover = [
        f"<b>{r.phase_label}</b><br>"
        f"{r.ts_label}<br>"
        f"<i>{r.techniques}</i><br>"
        f"{r.description}"
        for r in df.itertuples()
    ]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=df["order"],
                y=df["phase_idx"],
                z=df["severity_score"],
                mode="markers+lines",
                marker=dict(
                    size=8,
                    color=df["severity_score"],
                    colorscale="Viridis",
                    opacity=0.85,
                    cmin=1,
                    cmax=4,
                    showscale=False,
                ),
                line=dict(color="rgba(140, 140, 140, 0.5)", width=3),
                text=hover,
                hoverinfo="text",
            )
        ]
    )

    fig.update_layout(
        scene=dict(
            xaxis_title="Event order",
            yaxis_title="Kill chain phase",
            zaxis_title="Severity",
            yaxis=dict(
                tickmode="array",
                tickvals=list(_PHASE_INDEX.values()),
                ticktext=[_PHASE_LABEL[p] for p in _PHASE_ORDER],
            ),
            zaxis=dict(
                tickmode="array",
                tickvals=[1, 2, 3, 4],
                ticktext=["Low", "Medium", "High", "Critical"],
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        template="plotly_dark",
    )

    return fig