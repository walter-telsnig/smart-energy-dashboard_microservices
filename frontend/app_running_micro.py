import dash
from dash import html
import dash_bootstrap_components as dbc
import os

# Wir behalten nur das Notwendigste
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# Minimales Layout mit großem, weißem Text
app.layout = html.Div([
    html.H1("DASH LÄUFT ERFOLGREICH!", style={
        'color': 'white', 
        'textAlign': 'center', 
        'marginTop': '100px'
    }),
    html.P("Wenn Sie diesen Text sehen, ist Dash in Docker korrekt konfiguriert.", style={
        'color': 'white', 
        'textAlign': 'center'
    })
], style={
    'backgroundColor': '#212529', # Dunkler Hintergrund
    'height': '100vh'
})


if __name__ == "__main__":
    # HOST und PORT müssen auf 0.0.0.0 und 8050 gesetzt sein, damit es in Docker funktioniert
    app.run(debug=True, host="0.0.0.0", port=8050)