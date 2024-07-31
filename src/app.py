import dash
from dash import dash_table
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from llama_index.core import PromptTemplate
from llama_index.experimental.query_engine import PandasQueryEngine
import pathlib

# Da die App via RENDER deployed wird, erfolgt der Zugriff auf den Token via .yaml-File
# mapbox_token = open(".env").read()
# print(token)
import os
mapbox_token = os.environ.get('mapbox_token')


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Path
BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("assets").resolve()

# Read data
df = pd.read_csv(DATA_PATH.joinpath("unfallorte.csv"))


# Instruction Prompt
instruction_str = """\
1. Convert the query to executable Python code using Pandas.
2. The final line of code should be a Python expression that can be called with the `eval()` function.
3. The code should represent a solution to the query.
4. PRINT ONLY THE EXPRESSION.
5. Do not quote the expression.
"""

# Initialize the PandasQueryEngine
query_engine = PandasQueryEngine(df=df, verbose=True, instruction_str=instruction_str)

# Prompt
new_prompt = PromptTemplate(
    """\
You are working with a pandas dataframe in Python.
The name of the dataframe is `df`.
This is the result of `print(df.head())`:
{df_str}

Follow these instructions:
{instruction_str}
Query: {query_str}

Expression: """
)
# Update Prompt
query_engine.update_prompts({"pandas_prompt": new_prompt})


# Hilfsvariablen
monate = ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
wtage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

# # Mapping der Strings in den Spalten, um kürzere Strings für die Paramenterwahl zu haben
mapping_dict_typ = {
    'Abbiegeunfall': 'Abbiege',
    'Auffahrunfall': 'Auffahr',
    'Andere': 'Andere',
    'Einbiegeunfall': 'Einbiege',
    'Frontalkollision': 'Frontal',
    'Fussgängerunfall': 'Fussgänger',
    'Parkierunfall': 'Parkier',
    'Schleuder- oder Selbstunfall': 'Schleuder',
    'Tierunfall': 'Tier',
    'Überholunfall oder Fahrstreifenwechsel': 'Überholunfall',
    'Überqueren der Fahrbahn': 'Fahrbahnüberquerung',
}
df['Unfalltyp'] = df['Unfalltyp'].map(mapping_dict_typ)

mapping_dict_schwere = {
    'Unfall mit Leichtverletzten': 'Leicht',
    'Unfall mit Schwerverletzten': 'Schwer',
    'Unfall mit Getöteten': 'Tod',
}
df['Unfallschwere'] = df['Unfallschwere'].map(mapping_dict_schwere)


# Components

card = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Information und Anleitung", className="card-title"),
            html.P(
                """Diese interaktive Auswertung ist eine Weiterentwicklung der 
                bestehenden App. Unterhalb der Einstellungen wurde die Möglichkeit
                integriert, direkt Fragen zum Datensatz zu stellen. 
                Die Umsetzung nutzt den PandasQueryEngine von Llamaindex und ist
                unabhängig von den eingestellten Parametern.""",
                className="card-text"),
            #  html.H4("Einstellung Unfallparameter", className="card-title"),
        ]
    ),
)


cl_all = dbc.Card(
            [
               dbc.CardBody(
                    [
                    html.H6("Zeitraum", className="card-title"),
                    dcc.RangeSlider(
                        id="zeitraum",
                        marks={i: f"{i}" for i in range(2011, 2023, 1)},
                        min=2011,
                        max=2022,
                        step=1,
                        value=[2012, 2019],  # Default range from 2012 to 2022
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ],
                    style={"height": "4.4rem", "padding-top": "0.2rem"},
                ),
               dbc.CardBody(
                    [
                    html.H6("Schwere der Verletzung", className="card-title"),
                    dbc.Checklist(
                            id="checklist_schwere",
                            options=[{'label': item, 'value': item} for item in df["Unfallschwere"].unique()],
                            value=["Leicht", "Schwer", "Getötete"],
                            inline = True
                        )
                    ],
                    style={"height": "4rem"},
                ),
               dbc.CardBody(
                    [
                    html.H6("Beteiligte am Unfall", className="card-title"),
                    dbc.Checklist(id="checklist_beteiligte",
                        options=[
                                {'label': 'Fussgänger', 'value': 'Fussgänger'},
                                {'label': 'Fahrrad', 'value': 'Fahrrad'},
                                {'label': 'Motorrad', 'value': 'Motorrad'},
                        ],
                        value=['Fussgänger', 'Fahrrad'],
                        inline=True
                        )
                    ],
                    style={"height": "4rem"},
                ),
            ],
    body=True,
)

chatbot_card = dbc.Card(
    dbc.CardBody([
        # dbc.Row([
        #     dbc.Col(html.H6("Klicke, um Fragen zu stellen", className="card-title mb-0"), width="auto"),
        #     dbc.Col(dbc.Button("Submit", id="submit-question", color="primary"), width="auto", className="ms-auto"),
        # ], className="d-flex justify-content-between align-items-center mb-2"),
        dbc.Button(
            "Frage senden",
            id="submit-question",
            color="primary",
            className="mb-3 w-80 text-left",
            style={"textAlign": "left", "fontWeight": "bold"}
        ),
        dbc.Textarea(
            id="question",
            placeholder=' FRAGE hier! zB "Welche Attribute enthält der Datensatz" ',
            style={"margin-bottom": "1rem", "height": "30px"}
        ),
        dbc.Textarea(
            id="answer",
            placeholder="ANTWORT",
            style={"margin-bottom": "1rem", "height": "120px"},
            readOnly=True
        ),
    ]),
    body=True,
    className="mt-4",
)


# Layout
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H2(
                    "Verkehrsunfallorte in St. Gallen",
                    className="text-center bg-primary text-white p-2 mb-6",
                ),
            ),
            className=" mb-3"
        ),
        dbc.Row(
                [
                dbc.Col(card, width=12, lg=4, className="mt-4 "),
                dbc.Col([html.H6("Häufigkeit nach Wochentag und Stunde"),
                    html.Div(id="table_sg")
                         ]),
                ],
                className="ms-1",
                ),
        dbc.Row(
                [
                    dbc.Col([cl_all, chatbot_card],
                                width=12, lg=4, className="mt-4"),
                    dbc.Col(dcc.Graph(id="map_sg"), width=12, lg=8, className="mt-4 border"),
                ],
                className="ms-1",
                ),
        # dbc.Row(dbc.Col(footer)),
    ],
    fluid=True,
)

# functions
def filter_df(checklist_schwere, checklist_beteiligte, jahre_bereich):
    start_jahr, ende_jahr = jahre_bereich
    start = pd.to_datetime(f"{start_jahr}-01-01")
    ende = pd.to_datetime(f"{ende_jahr}-12-31")

    # Convert 'Datum' column to datetime if it's not already
    df['Datum'] = pd.to_datetime(df['Datum'])

    df_filtered = df.query('@start <= Datum <= @ende')

    # Filter based on Unfallbeteiligung
    beteiligte = ' or '.join([f'{col} == True' for col in checklist_beteiligte])
    df_filtered = df_filtered.query(beteiligte)

    # Filter based on Unfallschwere
    df_filtered = df_filtered.query('Unfallschwere in @checklist_schwere')
    return df_filtered

# Callbacks
@app.callback(
    Output("map_sg", "figure"),
    Input("checklist_schwere", "value"),
    Input("checklist_beteiligte", "value"),
    Input("zeitraum", "value")
)
def fig_update(checklist_schwere, checklist_beteiligte, jahr_range):
    df_filtered = filter_df(checklist_schwere, checklist_beteiligte, jahr_range)
    fig = px.scatter_mapbox(df_filtered, lat="Breitengrad", lon="Längengrad",
                            color=df_filtered['Unfallschwere'], color_discrete_map={"Leicht": "green", "Schwer": "orange", "Getötete": "red"},
                                    opacity=0.99, zoom=12, width=1200, height=600,
                                    hover_data={'Längengrad':False, 'Breitengrad':False, 'Unfallschwere':False,
                                                'Unfalltyp': True, 'Jahr': True, 'Monat': True, 'Wochentag': True, 'Stunde': True
                                    })
    # fig.update_layout(mapbox_style="streets", mapbox_accesstoken = mapbox_token,
    #                         legend = dict(bgcolor = '#F5F5F5', title_text='Schwere der Verletzung', x=0.02, y=1.02, orientation="h", yanchor='bottom'),
    #                         )
    fig.update_layout(mapbox_style="carto-positron",
                        legend = dict(bgcolor = '#F5F5F5', title_text='Schwere der Verletzung', x=0.02, y=1.02, orientation="h", yanchor='bottom'),
                        )
    return fig


@app.callback(
    Output("table_sg", "children"),
    Input("checklist_schwere", "value"),
    Input("checklist_beteiligte", "value"),
    Input("zeitraum", "value")
)

def table_update(checklist_schwere, checklist_beteiligte, jahre_bereich):
    df_filtered = filter_df(checklist_schwere, checklist_beteiligte, jahre_bereich)
    # In den nächsten beiden Zeilen sorge ich noch dafür, dass von MO nach SO sortiert wird
    df_filtered['Wochentag'] = pd.Categorical(df_filtered['Wochentag'],categories=wtage)
    df_filtered = df_filtered.sort_values('Wochentag')
    df_weekday_hour = pd.pivot_table(df_filtered, values="Unfalltyp", index='Wochentag', columns='Stunde', aggfunc='size', fill_value=0)
    # print(df_weekday_hour)
    # # Ensure all hours from 0 to 23 are present
    # for hour in range(24):
    #     if hour not in df_weekday_hour.columns:
    #         df_weekday_hour[hour] = 0
    # df_weekday_hour = df_weekday_hour.sort_index(axis=1)
    # If needed, reset the index to make 'Wochentag' a column again
    df_weekday_hour = df_weekday_hour.reset_index()
    # Die DataTable benötigt Spaltenköpfe vom Typ STRING
    df_weekday_hour.columns = df_weekday_hour.columns.astype(str)
    df_weekday_hour_new = df_weekday_hour.iloc[:, 0:25]
    # print(df_weekday_hour_new)
    # print(df_weekday_hour_new.columns)
    data = df_weekday_hour_new.to_dict('records')
    # print(data)
    columns =  [{"name": i, "id": i} for i in df_weekday_hour_new.columns]
    # print("Spalten")
    # print(columns)

    table_sg = dash_table.DataTable(
        data=data,
        columns=columns,
        style_cell={
            'font-family': 'inherit',
            'width': '7px',
            'maxWidth': '7px',
            'minWidth': '7px',
            'textAlign': 'center',
        },
        style_header={'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#F5F5F5',
            },
        ] ,
        style_cell_conditional=[
            {
                'if': {'column_id': 'Wochentag'},
                'width': '15%'
            },
        ]
        )
    return table_sg

@app.callback(
    Output("answer", "value"),
    [Input("submit-question", "n_clicks")],
    [dash.dependencies.State("question", "value")]
)
def update_answer(n_clicks, question):
    if n_clicks and question:
        try:
            response = query_engine.query(question)
            return response.response  # Assuming response.response contains the answer text
        except Exception as e:
            return f"Error: {str(e)}"
    return ""



if __name__ == '__main__':
    app.run_server(debug=True, port = 8056)
