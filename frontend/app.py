import os
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, no_update
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Config
# Both services must point to the proper ports
API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://localhost:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8003")

# suppress_callback_exceptions MUSS gesetzt sein
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

# -------------------------------------------------------------
# Layouts
# -------------------------------------------------------------

# LOGIN LAYOUT: Enthält KEINE Klassen zur Höhen- oder Flexbox-Kontrolle (page-content macht das)
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Smart Energy Dashboard", className="text-center mb-4"),
            dbc.Input(id="username-box", placeholder="Username", type="text", className="mb-2", size="lg"),
            dbc.Input(id="password-box", placeholder="Password", type="password", className="mb-2", size="lg"),
            dbc.Button("Login", id="login-button", color="primary", className="w-100", size="lg"),
            html.Div(id="login-output", className="text-danger mt-2")
        # Responsive Layout:
        # xs/sm: Almost full width
        # md: slightly narrower
        # lg: original 4 column width centered
        ], width={"size": 10, "offset": 1, "md": 6, "md_offset": 3, "lg": 4, "lg_offset": 4}) 
    ])
]) 

dashboard_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Smart Energy Dashboard"), width=10),
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
    ])
], fluid=True)

# HAUPT-LAYOUT
app.layout = html.Div([
    dcc.Store(id="auth-token", storage_type="local"),
    dcc.Store(id="login-state", data=False),

    # Interval muss hier im Haupt-Layout sein
    dcc.Interval(id="interval-component", interval=15*1000, n_intervals=0),

    # page-content erhält KEINE Klassen, da sie dynamisch über Callback 
    # gesteuert werden muss (Output("page-content", "className"))
    # page-content initialisiert mit login_layout
    html.Div(login_layout, id="page-content", className="h-100 d-flex justify-content-center align-items-center"),
    
# Der ÄUSSERE Div setzt die absolute Viewport-Höhe (vh-100)
], className="vh-100") 

# -------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------

# NEUER, ZUSÄTZLICHER CALLBACK: Dynamische Klassenzuweisung für page-content
# Dieser Callback ist der entscheidende Fix, um Layout-Konflikte zu vermeiden
# 1. Page Routing (Login vs Dashboard)
@app.callback(
    Output("page-content", "children"),
    Input("login-state", "data")
)
def render_content(is_logged_in):
    if is_logged_in:
        # Dashboard: h-100 built-in
        return html.Div(dashboard_layout, className="h-100")
    
    # Login: Centered using d-flex
    return html.Div(login_layout, className="h-100 d-flex justify-content-center align-items-center")


# 2. Login Logic
@app.callback(
    [Output("auth-token", "data", allow_duplicate=True), 
     Output("login-state", "data", allow_duplicate=True), 
     Output("login-output", "children")],
    [Input("login-button", "n_clicks")],
    [State("username-box", "value"), State("password-box", "value")],
    prevent_initial_call=True
)
def login_user(n_clicks, username, password):
    if not n_clicks:
        return no_update, no_update, ""
        
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

# 3. Logout Logic
@app.callback(
    [Output("auth-token", "data", allow_duplicate=True), 
     Output("login-state", "data", allow_duplicate=True)],
    [Input("logout-button", "n_clicks")],
    prevent_initial_call=True
)
def logout_user(n_clicks):
    if n_clicks:
        return None, False
    return no_update, no_update

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
        r_flow = requests.get(f"{API_SERVICE_URL}/data/flow/timeseries", headers=headers)
        flow_data = r_flow.json() if r_flow.status_code == 200 else []
        
        r_soc = requests.get(f"{API_SERVICE_URL}/data/soc/timeseries", headers=headers)
        soc_data = r_soc.json() if r_soc.status_code == 200 else []
        
        r_status = requests.get(f"{API_SERVICE_URL}/data/current_status", headers=headers)
        status_data = r_status.json() if r_status.status_code == 200 else {}
        
    except Exception:
        return no_update, no_update, "Error fetching data"
    
    # Create Flow Graph
    # Create Flow Graph
    fig_flow = go.Figure()
    fig_flow.update_layout(title="Power Flow (kW)", template="plotly_dark")
    if flow_data:
        df_flow = pd.DataFrame(flow_data)
        if 'timestamp' in df_flow.columns:
            fig_flow.add_trace(go.Scatter(x=df_flow['timestamp'], y=df_flow.get('pv_power_kw', []), name='PV Generation'))
            fig_flow.add_trace(go.Scatter(x=df_flow['timestamp'], y=df_flow.get('consumption_power_kw', []), name='Consumption'))
    
    # Create SoC Graph
    fig_soc = go.Figure()
    fig_soc.update_layout(title="Battery SoC Forecast (%)", yaxis_range=[0, 100], template="plotly_dark")
    if soc_data:
        df_soc = pd.DataFrame(soc_data)
        if 'timestamp' in df_soc.columns:
            fig_soc.add_trace(go.Scatter(x=df_soc['timestamp'], y=df_soc.get('soc_percent', []), name='SoC Forecast', line=dict(color='green')))
            
    # Status Display
    status_html = html.Div([
        html.P(f"Current PV: {status_data.get('pv_power_kw', 0):.2f} kW"),
        html.P(f"Current Load: {status_data.get('consumption_power_kw', 0):.2f} kW"),
        html.P(f"Last Updated: {status_data.get('timestamp', 'N/A')}")
    ])
    
    return fig_flow, fig_soc, status_html

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)