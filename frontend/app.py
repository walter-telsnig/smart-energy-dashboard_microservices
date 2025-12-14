import os
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, no_update
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Config
API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://localhost:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8003")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# Layout
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("HEMS Login", className="text-center mb-4"),
            dbc.Input(id="username-box", placeholder="Username", type="text", className="mb-2"),
            dbc.Input(id="password-box", placeholder="Password", type="password", className="mb-2"),
            dbc.Button("Login", id="login-button", color="primary", className="w-100"),
            html.Div(id="login-output", className="text-danger mt-2")
        ], width={"size": 4, "offset": 4})
    ], className="vh-100 align-items-center")
])

dashboard_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Smart Energy Dashboard V3"), width=10),
        dbc.Col(dbc.Button("Logout", id="logout-button", color="danger"), width=2)
    ], className="mt-3 mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Energy Flow (Real-time)"),
                dbc.CardBody(dcc.Graph(id="flow-graph"))
            ])
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Current Status"),
                dbc.CardBody(html.Div(id="status-display"))
            ])
        ], md=4)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("SoC Forecast (24h)"),
                dbc.CardBody(dcc.Graph(id="soc-graph"))
            ])
        ])
    ]),
    
    dcc.Interval(id="interval-component", interval=15*1000, n_intervals=0)
], fluid=True)

app.layout = html.Div([
    dcc.Store(id="auth-token", storage_type="local"),
    dcc.Store(id="login-state", data=False),
    html.Div(id="page-content")
])

# Callbacks

# 1. Page Routing (Login vs Dashboard)
@app.callback(
    Output("page-content", "children"),
    Input("login-state", "data")
)
def render_content(is_logged_in):
    if is_logged_in:
        return dashboard_layout
    return login_layout

# 2. Login Logic
@app.callback(
    [Output("auth-token", "data"), Output("login-state", "data"), Output("login-output", "children")],
    [Input("login-button", "n_clicks"), Input("logout-button", "n_clicks")],
    [State("username-box", "value"), State("password-box", "value"), State("auth-token", "data")]
)
def handle_auth(n_login, n_logout, username, password, current_token):
    ctx = callback_context
    if not ctx.triggered:
        # Check if token exists in store on load (optional implementation for persistence)
        return no_update, no_update, ""
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "logout-button":
        return None, False, ""
    
    if trigger_id == "login-button":
        if not username or not password:
            return no_update, no_update, "Please enter credentials."
        
        try:
            response = requests.post(f"{AUTH_SERVICE_URL}/token", data={"username": username, "password": password})
            if response.status_code == 200:
                token = response.json().get("access_token")
                return token, True, ""
            else:
                return None, False, "Invalid credentials."
        except Exception as e:
            return None, False, f"Connection error: {str(e)}"
            
    return no_update, no_update, ""

# 3. Data Update Logic
@app.callback(
    [Output("flow-graph", "figure"), Output("soc-graph", "figure"), Output("status-display", "children")],
    [Input("interval-component", "n_intervals")],
    [State("auth-token", "data")]
)
def update_metrics(n, token):
    if not token:
        return go.Figure(), go.Figure(), "Not authenticated"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Fetch Data
    try:
        # Flow Timeseries
        r_flow = requests.get(f"{API_SERVICE_URL}/data/flow/timeseries", headers=headers)
        flow_data = r_flow.json() if r_flow.status_code == 200 else []
        
        # SoC Timeseries
        r_soc = requests.get(f"{API_SERVICE_URL}/data/soc/timeseries", headers=headers)
        soc_data = r_soc.json() if r_soc.status_code == 200 else []
        
        # Current Status
        r_status = requests.get(f"{API_SERVICE_URL}/data/current_status", headers=headers)
        status_data = r_status.json() if r_status.status_code == 200 else {}
        
    except Exception:
        return no_update, no_update, "Error fetching data"
    
    # Create Flow Graph
    fig_flow = go.Figure()
    if flow_data:
        df_flow = pd.DataFrame(flow_data)
        if 'timestamp' in df_flow.columns:
            fig_flow.add_trace(go.Scatter(x=df_flow['timestamp'], y=df_flow.get('pv_power_kw', []), name='PV Generation'))
            fig_flow.add_trace(go.Scatter(x=df_flow['timestamp'], y=df_flow.get('consumption_power_kw', []), name='Consumption'))
            fig_flow.update_layout(title="Power Flow (kW)", template="plotly_dark")
    
    # Create SoC Graph
    fig_soc = go.Figure()
    if soc_data:
        df_soc = pd.DataFrame(soc_data)
        if 'timestamp' in df_soc.columns:
            fig_soc.add_trace(go.Scatter(x=df_soc['timestamp'], y=df_soc.get('soc_percent', []), name='SoC Forecast', line=dict(color='green')))
            fig_soc.update_layout(title="Battery SoC Forecast (%)", yaxis_range=[0, 100], template="plotly_dark")
            
    # Status Display
    status_html = html.Div([
        html.P(f"Current PV: {status_data.get('pv_power_kw', 0):.2f} kW"),
        html.P(f"Current Load: {status_data.get('consumption_power_kw', 0):.2f} kW"),
        html.P(f"Last Updated: {status_data.get('timestamp', 'N/A')}")
    ])
    
    return fig_flow, fig_soc, status_html

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
