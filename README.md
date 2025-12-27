# 🎬 IMDb Graph Explorer

### [Live Demo: https://movies-sw08.onrender.com/](https://movies-sw08.onrender.com/)

A full-stack web application that visualizes connections between actors and explores filmographies using real-time data from IMDb. It features an intelligent search engine and a "Six Degrees of Separation" algorithm to find the shortest collaboration path between any two actors.

---

## Features

*   **Collaboration Distance Calculator:** Uses a Breadth-First Search (BFS) algorithm to find the shortest path between two actors (e.g., *How is Tom Cruise connected to Kevin Bacon?*).
*   **IMDb Dark Theme:** A responsive, professional user interface designed to match the classic IMDb dark aesthetic.
*   **Automated Data Pipeline:** The dataset updates automatically every 24 hours using GitHub Actions.
*   **Optimized Performance:** Handles millions of records using a compressed SQLite database, allowing it to run on low-memory environments.

---

## Architecture & Tech Stack

### Backend
*   **Python & Flask:** Serves the web application and API endpoints.
*   **SQLite:** Data is stored in a relational database for efficient querying (replacing in-memory JSON to solve RAM constraints).
*   **Gzip Compression:** The database is compressed (`imdb.db.gz`) to bypass GitHub's 100MB file limit and unzipped dynamically on server startup.

### Frontend
*   **HTML5 & CSS3:** Custom-built styling with CSS variables for the dark theme scheme.
*   **Jinja2:** Server-side template rendering.

### Automation (CI/CD)
*   **GitHub Actions:** A workflow (`update_data.yml`) runs daily at 00:00 UTC.
    1.  Downloads raw TSV files from `datasets.imdbws.com`.
    2.  Filters data (Movies > 1970) to ensure relevance and save space.
    3.  Processes relationships (Actor <-> Movie) into a relational schema.
    4.  Compresses the database and commits it back to the repository.
    5.  **Render** automatically redeploys the website upon the new commit.

---

## How to Run Locally

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/movies.git
    cd movies
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate the Database**
    *Note: The app needs the database to run. You can either wait for the GitHub Action to run, or generate it locally:*
    ```bash
    python data_processor.py
    ```
    *This will download the data, process it, and create `data_imdb/imdb.db.gz`.*

4.  **Run the App**
    ```bash
    python app.py
    ```

5.  **Visit the site**
    Open `http://127.0.0.1:5000/web` in your browser.

---

## Project Structure

```text
├── .github/workflows/   # GitHub Actions (Daily Update Script)
├── data_imdb/           # Stores the compressed database
├── static/              # CSS Stylesheets
├── templates/           # HTML Templates
├── app.py               # Flask Web Server
├── data_processor.py    # ETL Script (Download -> Clean -> SQL -> Compress)
├── graph_logic.py       # BFS Algorithm & Database Queries
└── requirements.txt     # Python Dependencies
```
---

## Data Source

Data is sourced from IMDb Datasets.
    
    title.basics.tsv.gz
    title.principals.tsv.gz
    name.basics.tsv.gz

---

Note: AI tools (Google AI Studio) were used as general guidance during the development of this project.


