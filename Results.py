import json
import os
import dash
from dash import dcc, html
import plotly.graph_objs as go


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = [json.loads(line) for line in file]
    return data


def process_data(data):
    game_numbers = list(range(1, len(data) + 1))
    enemies_killed = [entry["enemies_killed"] for entry in data]
    return game_numbers, enemies_killed


# List of all the algorithms and their file paths
Algorithms = ["All_Money_Algorithm", "Random_Algorithm", "Expensive_Algorithm", "SpreadPlacement_Algorithm"]
file_paths = [f"D:/Alpha-project/game_results_{algorithm}.json" for algorithm in Algorithms]

# Here we read and process data for each algorithm
data_traces = []
for algorithm, file_path in zip(Algorithms, file_paths):
    if os.path.exists(file_path):
        data = read_json_file(file_path)
        game_numbers, enemies_killed = process_data(data)

        #This creates a scatter plot for each algorithm
        trace = go.Scatter(
            x=game_numbers,
            y=enemies_killed,
            mode='markers',
            name=algorithm
        )
        data_traces.append(trace)
    else:
        print(f"File {file_path} does not exist.")

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(
        id='scatter-plot',
        figure={
            'data': data_traces,
            'layout': go.Layout(
                xaxis={'title': 'Game number'},
                yaxis={'title': 'Enemies Killed'},
                height=1000
            )
        },
        style={'width': '90%', 'height': '80vh'}
    )
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
