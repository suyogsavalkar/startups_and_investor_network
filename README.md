# Startup Investor Network

This SI 507 final project maps startups as a network connected by shared investors. Each startup is a node, and an edge exists when two startups share at least one VC firm or investor. Edge weight is the number of shared investors, so stronger edges represent more overlap in the funding network.

The goal is to show what a flat startup table cannot show easily: which companies sit near each other in the funding ecosystem, which companies are central hubs, and how two startups can be connected through shared backers.

## Project Context

This project was built for the SI 507 final project requirements. The final project instructions asked for:

- A graph or tree as the primary structure
- Thoughtful object-oriented design
- Real-world data
- At least four interaction modes
- A usable interface, with Streamlit encouraged
- A test suite that demonstrates understanding of the project behavior

The approved proposal targeted an A and described a startup investment graph built from two CSV datasets. The realistic scope promised a Streamlit app with startup search, shortest-path discovery, rankings, and filters. This final version implements that scope.

The proposal also mentioned an optional AI narration layer as a stretch feature. That feature was removed from the final app so the deployed project requires no API key and all path explanations are deterministic, reproducible, and fully based on the graph data.

## Data

The project uses two real CSV datasets stored in `data/`:

- `data/Startups in 2021 end.csv`: global startup/unicorn data with company, industry, country, city, valuation, and selected investors.
- `data/Startups.csv`: YC startup data with company, categories, headquarters fields, investors, and related metadata.

The loader standardizes both files into one table with these canonical fields:

- `startup_id`
- `company`
- `industry`
- `country`
- `city`
- `valuation`
- `investors_raw`
- `dataset`

Current combined dataset size:

- 1,624 startup rows
- 936 rows from `Startups in 2021 end.csv`
- 688 rows from `Startups.csv`

With the default graph settings, the app builds:

- 1,624 startup nodes
- 25,086 investor-overlap edges
- 1,786 unique normalized investors
- 568 investors eligible under the default filtering thresholds

## Graph Structure

The graph is the core data structure.

Nodes represent startups. Each node stores company metadata such as name, industry, country, city, valuation, source dataset, and parsed investor lists.

Edges represent shared investors. Two startups are connected when at least one normalized investor name appears in both startup records.

Edge weights represent the number of shared investors. For example, if two startups share Sequoia Capital and Accel, their edge weight is `2`.

Weighted path-finding uses inverse edge weight as distance, which means the app can prefer stronger investor relationships rather than only the fewest hops.

## Object-Oriented Design

The code uses domain classes and a service layer rather than keeping all logic inside the Streamlit app.

Important classes:

- `Company` in `startup_network/models.py`: represents one startup and exposes a `connected_companies()` method.
- `Investor` in `startup_network/models.py`: represents one normalized investor and exposes related company and co-investor behavior.
- `InvestorNetwork` in `startup_network/service.py`: loads the data, builds lookup indices, creates graph objects, and exposes query methods.
- `NetworkBundle` in `startup_network/types.py`: groups the filtered startup table, graph, diagnostics, and eligible-investor counts.

The project is split into modules by responsibility:

- `startup_network/data_loader.py`: loads and unifies the CSV files.
- `startup_network/parsing.py`: parses and normalizes investor names.
- `startup_network/indices.py`: builds startup-investor lookup maps and domain objects.
- `startup_network/graph_builder.py`: builds weighted NetworkX graphs.
- `startup_network/queries.py`: handles connected-company search, path-finding, path edge details, rankings, and diagnostics.
- `startup_network/explainers.py`: generates deterministic explanations of graph paths.
- `app.py`: provides UI-free helper functions used by Streamlit.
- `streamlit_app.py`: contains the Streamlit interface.

## Interaction Modes

The Streamlit app provides four main interaction modes, plus global filters.

1. **Home**
   Shows high-level graph statistics: startup count, investor connections, largest cluster, active investors, network density, and current filters.

2. **Search**
   Lets the user pick a startup, inspect its metadata and investors, and see connected startups sorted by shared-investor strength.

3. **Connections**
   Lets the user choose two startups and find a path between them through shared investors. The user can choose normal shortest path or weighted path-finding that favors stronger relationships.

4. **Rankings**
   Ranks startups by network position. The available ranking modes are total investor reach, number of connections, and bridge score.

Global sidebar filters:

- Industry filter
- Country filter
- Minimum investor frequency
- Maximum investor prevalence
- Minimum shared investors required to draw an edge

## Running the App

Clone the repository:

```bash
git clone https://github.com/suyogsavalkar/startups_and_investor_network.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

The main deployment entry point is:

```text
streamlit_app.py
```

## Testing

Run the full test suite:

```bash
python -m unittest discover -v
```

Current test result:

```text
Ran 16 tests
OK
```

The test suite is split into focused files:

- `tests/test_data_loading.py`: verifies CSV loading, required columns, investor parsing, and investor-name normalization.
- `tests/test_graph_building.py`: verifies graph diagnostics, shared-investor edge creation, edge weights, and minimum edge weight filtering.
- `tests/test_queries.py`: verifies no-path behavior, connected-company sorting, ranking output, path edge details, same-startup paths, weighted path behavior, and deterministic path explanations.
- `tests/test_domain_and_facade.py`: verifies domain objects, object methods, and app-level filtering.
- `tests/helpers.py`: contains small synthetic datasets that make graph behavior easy to check by hand.

The tests are meant to read like living documentation: they show what the graph is supposed to do, how edge cases behave, and how the app-facing helper functions should respond.