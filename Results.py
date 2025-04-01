import json
import os
import dash
from dash import dcc, html
import plotly.graph_objs as go


def read_json_file(file_path):
    """
    Read a file where each line is either a plain JSON object (such as in GA_Results1.json) or a line starting with a prefix (e.g. "GA_results: ")
    and return a list of parsed JSON entries. If a line is prefixed, the prefix is stored as "algorithm_name" in the entry.

    Parameters:
        file_path (str): the path to the file we will read and extract data from

    Returns:
        The data from the file
    """
    data = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line[0] != '{':
                    parts = line.split(": ", 1)
                    prefix = parts[0]
                    json_str = parts[1] if len(parts) == 2 else line
                    try:
                        entry = json.loads(json_str)
                        if "algorithm_name" not in entry:
                            entry["algorithm_name"] = prefix
                        data.append(entry)
                    except json.decoder.JSONDecodeError:
                        pass
                else:
                    try:
                        entry = json.loads(line)
                        data.append(entry)
                    except json.decoder.JSONDecodeError:
                        pass
    except Exception:
        data = []
    return data


def process_data(data, file_name):
    """
    Process raw JSON data to extract rounds survived and average rounds survived from the last 11 entries
    (representing health levels 1 to 11). For RL_results, extract the "rounds_survived" value from the dictionary
    stored under a key ending with "best_performance: " and use the value from "average_performance: " for the average.

    Parameters:
        data (list): The list of JSON entries.
        file_name (str): The algorithm name.

    Returns:
        tuple: Two lists containing rounds survived and average rounds survived.
    """
    rounds_survived = []
    average_rounds_survived = []
    selected_data = data[-11:] if len(data) >= 11 else data
    for entry in selected_data:
        if file_name == "RL_results":
            bp_value = 0
            for k, v in entry.items():
                if k.endswith("best_performance: "):
                    bp_value = v.get("rounds_survived", 0)
                    break
            Best_Performance = bp_value
            average_performance = entry.get("average_performance: ", 0)
        else:
            Best_Performance = entry.get("best_performance: ", 0)
            average_performance = entry.get("average_performance", [0])[0]
        rounds_survived.append(Best_Performance)
        average_rounds_survived.append(average_performance)
    return rounds_survived, average_rounds_survived


def combine_results(load_file_path="D:/Alpha-project/", save_file_path="D:/Alpha-project/All_Algorithms_Results.json"):
    """
    Combine the last 11 entries from each individual algorithm result file into one big file.

    If the file at save_file_path exists, load and return its data. Otherwise, for each algorithm and spawner number,
    read each file from load_file_path, keep only the last 11 lines, add 'algorithm_name' and 'spawner_number' fields
    to each entry, and write each line with a prefix (the algorithm name followed by ": ") to save_file_path.

    Parameters:
        load_file_path (str): The directory where individual result files are stored.
        save_file_path (str): The file path where the combined results will be saved.

    Returns:
        list: The combined data as a list of JSON objects.
    """
    if os.path.exists(save_file_path):
        combined_data = read_json_file(save_file_path)
        print("Combined file exists, loading data.")
    else:
        combined_data = []
        if os.path.exists(save_file_path):
            os.remove(save_file_path)
        algorithms = ["SA_results", "GA_results", "LS_results", "RL_results"]
        with open(save_file_path, 'w') as out_file:
            out_file.write("")
        for alg in algorithms:
            for num in range(1, 6):
                curr_file = f"{load_file_path}{alg}{num}.json"
                if os.path.exists(curr_file):
                    with open(curr_file, 'r') as f:
                        lines = f.readlines()
                        selected_lines = lines[-11:] if len(lines) >= 11 else lines
                        for line in selected_lines:
                            try:
                                entry = json.loads(line)
                                entry["algorithm_name"] = alg
                                entry["spawner_number"] = num
                                line_str = f"{alg}: " + json.dumps(entry) + "\n"
                                combined_data.append(entry)
                                with open(save_file_path, 'a') as out_file:
                                    out_file.write(line_str)
                            except json.decoder.JSONDecodeError:
                                pass
        print("All data copied into combined file.")
    return combined_data


def build_tables(combined_data):
    """
    Build best and average results tables from the combined data.

    Groups the combined data by algorithm and spawner number (1 to 5), computes the sum for each group,
    and creates two Plotly Table figures (one for best results and one for average results) with an extra total row.

    Parameters:
        combined_data (list): The combined JSON data from all result files.

    Returns:
        tuple: Two Plotly Table figures.
    """
    Algorithms = ["RL_results", "SA_results", "LS_results", "GA_results"]
    best_results = {alg: [0] * 5 for alg in Algorithms}
    average_results = {alg: [0] * 5 for alg in Algorithms}
    for entry in combined_data:
        alg = entry.get("algorithm_name", None)
        spawner = entry.get("spawner_number", None)
        if alg in Algorithms and spawner is not None and 1 <= spawner <= 5:
            if alg == "RL_results":
                bp = 0
                for k, v in entry.items():
                    if k.endswith("best_performance: "):
                        bp = v.get("rounds_survived", 0)
                        break
                ap = entry.get("average_performance: ", 0)
            else:
                bp = entry.get("best_performance: ", 0)
                ap = entry.get("average_performance", [0])[0]
            best_results[alg][spawner - 1] += bp
            average_results[alg][spawner - 1] += ap
    total_best = {alg: round(sum(best_results[alg]), 2) for alg in Algorithms}
    total_avg = {alg: round(sum(average_results[alg]), 2) for alg in Algorithms}
    spawner_labels = [f"{i} Spawners" for i in range(1, 6)] + ["<b>Total Rounds</b>"]
    table_best = {"Spawners": spawner_labels}
    table_avg = {"Spawners": spawner_labels}
    for alg in Algorithms:
        table_best[alg] = [f"{round(val, 2):.2f}" for val in best_results[alg]] + [f"<b>{total_best[alg]:.2f}</b>"]
        table_avg[alg] = [f"{round(val, 2):.2f}" for val in average_results[alg]] + [f"<b>{total_avg[alg]:.2f}</b>"]
    fig_best = go.Figure(data=[go.Table(
        header=dict(values=["Spawners"] + Algorithms,
                    fill_color="paleturquoise",
                    align="center",
                    font=dict(size=14, color="black")),
        cells=dict(values=[table_best["Spawners"]] + [table_best[alg] for alg in Algorithms],
                   fill_color="lavender",
                   align="center",
                   font=dict(size=12, color="black"))
    )])
    fig_best.update_layout(title="Best Results per Game", height=600, width=800)
    fig_avg = go.Figure(data=[go.Table(
        header=dict(values=["Spawners"] + Algorithms,
                    fill_color="paleturquoise",
                    align="center",
                    font=dict(size=14, color="black")),
        cells=dict(values=[table_avg["Spawners"]] + [table_avg[alg] for alg in Algorithms],
                   fill_color="lavender",
                   align="center",
                   font=dict(size=12, color="black"))
    )])
    fig_avg.update_layout(title="Average Results per Game", height=600, width=800)
    return fig_best, fig_avg


def build_graphs(combined_data):
    """
    Build best and average results graphs from the combined data.

    For each spawner number (1 to 5) and for each algorithm, filter the combined data and use process_data
    to extract rounds survived and average rounds survived. Create Scatter traces for each algorithm to make the graphs.

    Parameters:
        combined_data (list): The combined JSON data from all result files.

    Returns:
        tuple: Two dictionaries of Plotly figures keyed by spawner number.
    """
    Algorithms = ["SA_results", "GA_results", "LS_results", "RL_results"]
    Main_categories = ['1 HP']
    for i in range(1, 11):
        Main_categories.append(f"{10 * i} HP")
    x_axis_labels = Main_categories
    x_axis_values = list(range(len(x_axis_labels)))
    graphs_best = {}
    graphs_avg = {}
    for num in range(1, 6):
        traces_best = []
        traces_avg = []
        for alg in Algorithms:
            subset = [entry for entry in combined_data if
                      entry.get("algorithm_name") == alg and entry.get("spawner_number") == num]
            if subset:
                rounds_survived, avg_rounds = process_data(subset, alg)
            else:
                rounds_survived = [0] * 11
                avg_rounds = [0] * 11
            traces_best.append(go.Scatter(x=x_axis_values, y=rounds_survived, mode='markers+lines', name=alg))
            traces_avg.append(go.Scatter(x=x_axis_values, y=avg_rounds, mode='markers+lines', name=alg))
        fig_best = go.Figure(data=traces_best)
        fig_best.update_layout(
            xaxis=dict(tickvals=x_axis_values, ticktext=x_axis_labels, tickangle=-45),
            title=f"Best Results for {num} Spawners",
            xaxis_title="Starting Player HP",
            yaxis_title="Rounds Survived",
            height=1000,
            margin=dict(l=100, r=50, b=150, t=50)
        )
        fig_avg = go.Figure(data=traces_avg)
        fig_avg.update_layout(
            xaxis=dict(tickvals=x_axis_values, ticktext=x_axis_labels, tickangle=-45),
            title=f"Average Results for {num} Spawners",
            xaxis_title="Starting Player HP",
            yaxis_title="Rounds Survived",
            height=1000,
            margin=dict(l=100, r=50, b=150, t=50)
        )
        graphs_best[num] = fig_best
        graphs_avg[num] = fig_avg
    return graphs_best, graphs_avg


def run_dashboard(load_file_path="D:/Alpha-project/", save_file_path="D:/Alpha-project/All_Algorithms_Results.json"):
    """
    Build a unified Dash app layout with tabs for tables and graphs, then run the server.

    The layout contains two main tabs: one for side-by-side tables (best and average results) and one for graphs.
    The graphs tab contains two sub-tabs: one for best results graphs (1–5) and one for average results graphs (1–5),
    each arranged in a scrollable layout.

    This function uses the combined data from the All_Algorithms_Results file (if it exists).
    This is the main function that shows the results

    """
    combined_data = combine_results(load_file_path, save_file_path)
    fig_best_table, fig_avg_table = build_tables(combined_data)
    graphs_best, graphs_avg = build_graphs(combined_data)
    table_layout = html.Div([
        html.H1("Combined Results Tables"),
        html.Div([
            html.Div([dcc.Graph(figure=fig_best_table)], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(figure=fig_avg_table)], style={'width': '50%', 'display': 'inline-block'})
        ])
    ])
    best_graphs_layout = html.Div([
        html.H1("Best Results Graphs"),
        html.Div([dcc.Graph(figure=graphs_best[num]) for num in range(1, 6)],
                 style={'height': '150vh', 'overflowY': 'scroll'})
    ])
    avg_graphs_layout = html.Div([
        html.H1("Average Results Graphs"),
        html.Div([dcc.Graph(figure=graphs_avg[num]) for num in range(1, 6)],
                 style={'height': '150vh', 'overflowY': 'scroll'})
    ])
    graphs_layout = dcc.Tabs([
        dcc.Tab(label="Best Results Graphs", children=[best_graphs_layout]),
        dcc.Tab(label="Average Results Graphs", children=[avg_graphs_layout])
    ])
    main_layout = dcc.Tabs([
        dcc.Tab(label="Tables", children=[table_layout]),
        dcc.Tab(label="Graphs", children=[graphs_layout])
    ])
    app = dash.Dash(__name__)
    app.layout = html.Div([main_layout])
    app.run_server(port=8050, debug=True)


if __name__ == '__main__':
    """
    Calls the function that shows the tables and graphs.
    """
    run_dashboard()
