import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
from llama_index.experimental.query_engine import PandasQueryEngine
import os
from dotenv import load_dotenv

# Load CSV file into a DataFrame
df = pd.read_csv('./src/assets/unfallorte.csv')

# Initialize the PandasQueryEngine
query_engine = PandasQueryEngine(df)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("Frag mich!"),
    dcc.Input(id='query-input', type='text', placeholder='Was ist die Frage', style={'width': '50%'}),
    html.Button(id='submit-button', n_clicks=0, children='Submit'),
    html.Div(id='query-output')
])

# Define the callback
@app.callback(
    Output('query-output', 'children'),
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('query-input', 'value')]
)
def update_output(n_clicks, query):
    if n_clicks > 0 and query:
        try:
            result = query_engine.query(query)
            # The response is typically in the 'response' attribute
            response_text = result.response
            return html.Div([
                html.H4('Query Result:'),
                html.Pre(response_text)
            ])
        except Exception as e:
            return html.Div([
                html.H4('Error:'),
                html.Pre(str(e))
            ])
    return html.Div()


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8055)
