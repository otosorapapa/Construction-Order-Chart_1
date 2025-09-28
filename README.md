# Construction Order Chart

This repository contains a Streamlit application for visualising construction project schedules as a Gantt chart. The actual application code lives in the [`streamlit-gantt/`](streamlit-gantt) directory.

## Quick start

1. Create and activate a virtual environment (optional but recommended).
2. Install the Python dependencies:
   ```bash
   # From the repository root
   pip install -r requirements.txt

   # Or, if you prefer working inside the app directory
   pip install -r streamlit-gantt/requirements.txt
   ```
   If you need PNG export support, install [Kaleido](https://github.com/plotly/Kaleido) as an optional dependency:
   ```bash
   pip install kaleido
   ```
3. Launch the Streamlit app:
   ```bash
   streamlit run streamlit-gantt/app.py
   ```

If you encounter an error such as `No module named 'plotly'`, it means the dependencies have not been installed yet. Running either of the installation commands above will install Plotly and the other required libraries.

Refer to [`streamlit-gantt/README.md`](streamlit-gantt/README.md) for more detailed documentation, including feature descriptions and testing instructions.
