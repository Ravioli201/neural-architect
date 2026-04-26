import plotly.graph_objects as go
import pandas as pd
from typing import List
from neural_architect.core.models import AttackEvent

def render_3d_attack_graph(events: List[AttackEvent]):
    if not events:
        return None

    # Convert events to a dataframe for Plotly
    df = pd.DataFrame([
        {
            "time": e.timestamp,
            "phase": e.kill_chain_phase.value,
            "severity": e.severity.value,
            "technique": e.technique.name if e.technique else "Unknown",
            "description": e.description
        } for e in events
    ])

    # Map phases to numeric values for the Y axis
    phase_order = ["Reconnaissance", "Initial Access", "Execution", "Persistence", 
                   "Privilege Escalation", "Defense Evasion", "Credential Access", 
                   "Discovery", "Lateral Movement", "Collection", "Command and Control", "Exfiltration", "Impact"]
    phase_map = {p: i for i, p in enumerate(phase_order)}
    df["phase_idx"] = df["phase"].map(phase_map)

    fig = go.Figure(data=[go.Scatter3d(
        x=df["time"],
        y=df["phase_idx"],
        z=df["severity"],
        mode='markers+lines',
        marker=dict(
            size=8,
            color=df["severity"],
            colorscale='Viridis',
            opacity=0.8
        ),
        text=df["technique"],
        hoverinfo='text'
    )])

    fig.update_layout(
        scene=dict(
            xaxis_title='Timeline',
            yaxis_title='Kill Chain Phase',
            zaxis_title='Severity Score',
            yaxis=dict(tickvals=list(phase_map.values()), ticktext=list(phase_map.keys()))
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        template="plotly_dark"
    )
    
    return fig