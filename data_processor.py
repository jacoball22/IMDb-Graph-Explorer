import gzip
import sqlite3
import shutil
import os
from pathlib import Path
from requests import Session

# Settings
base_url = "https://datasets.imdbws.com/"
data_dir = Path.cwd() / "data_imdb"
db_path = data_dir / "imdb.db"

def update_data():
    print("--- STARTING UPDATE (SQLite Version) ---")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    files = ['title.principals.tsv.gz', 'name.basics.tsv.gz', 'title.basics.tsv.gz']
    
    # 1. Download
    for file in files:
        target_path = data_dir / file
        url = base_url + file
        if not target_path.exists(): # Optional: Skip if already exists to save bandwidth during testing
            print(f"Downloading {file}...")
            try:
                with Session() as s:
                    response = s.get(url, stream=True)
                    response.raise_for_status()
                    with open(target_path, 'wb') as f:
                        shutil.copyfileobj(response.raw, f)
            except Exception as e:
                print(f"Download failed: {e}")
                return False

    # 2. Prepare Database
    if db_path.exists():
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create Tables
    c.execute('CREATE TABLE movies (id INTEGER PRIMARY KEY, tconst TEXT, title TEXT, year INTEGER)')
    c.execute('CREATE TABLE actors (id INTEGER PRIMARY KEY, nconst TEXT, name TEXT)')
    c.execute('CREATE TABLE roles (actor_id INTEGER, movie_id INTEGER)')
    
    # Speed optimizations
    c.execute('PRAGMA synchronous = OFF')
    c.execute('PRAGMA journal_mode = MEMORY')

    # 3. Process Movies (Filter: Year > 1970 to save space)
    print("Processing Movies...")
    true_movies = {} # tconst -> int_id
    movie_id_counter = 0
    
    with gzip.open(data_dir / 'title.basics.tsv.gz', 'rt', encoding='utf-8') as f:
        f.readline()
        batch = []
        for line in f:
            parts = line.strip().split('\t')
            # tconst=0, type=1, title=2, year=5
            if len(parts) > 5 and parts[1] == 'movie' and parts[5].isdigit():
                year = int(parts[5])
                if year > 1970: # <--- FILTER: Keeps DB small
                    tconst = parts[0]
                    title = parts[2]
                    true_movies[tconst] = movie_id_counter
                    batch.append((movie_id_counter, tconst, title, year))
                    movie_id_counter += 1
                    
            if len(batch) > 10000:
                c.executemany('INSERT INTO movies VALUES (?,?,?,?)', batch)
                batch = []
        if batch: c.executemany('INSERT INTO movies VALUES (?,?,?,?)', batch)

    # 4. Process Actors & Roles
    print("Processing Actors & Roles...")
    actor_map = {} # nconst -> int_id
    actor_id_counter = 0
    roles_batch = []
    actors_batch = []
    
    # We read principals to find out which actors act in our "true_movies"
    with gzip.open(data_dir / 'title.principals.tsv.gz', 'rt', encoding='utf-8') as f:
        f.readline()
        for line in f:
            parts = line.strip().split('\t')
            tconst = parts[0]
            nconst = parts[2]
            category = parts[3]
            
            if tconst in true_movies and category in ('actor', 'actress'):
                m_id = true_movies[tconst]
                
                # If new actor, assign ID
                if nconst not in actor_map:
                    actor_map[nconst] = actor_id_counter
                    # We will fill the name later
                    actors_batch.append((actor_id_counter, nconst, "")) 
                    actor_id_counter += 1
                
                a_id = actor_map[nconst]
                roles_batch.append((a_id, m_id))
                
            if len(roles_batch) > 10000:
                c.executemany('INSERT INTO roles VALUES (?,?)', roles_batch)
                roles_batch = []
            if len(actors_batch) > 10000:
                c.executemany('INSERT INTO actors VALUES (?,?,?)', actors_batch)
                actors_batch = []
                
        if roles_batch: c.executemany('INSERT INTO roles VALUES (?,?)', roles_batch)
        if actors_batch: c.executemany('INSERT INTO actors VALUES (?,?,?)', actors_batch)

    # 5. Update Actor Names
    print("Updating Actor Names...")
    # We need to update the blank names in the DB
    conn.commit()
    
    # Create index for fast name update
    c.execute('CREATE INDEX idx_actor_nconst ON actors(nconst)')
    
    with gzip.open(data_dir / 'name.basics.tsv.gz', 'rt', encoding='utf-8') as f:
        f.readline()
        batch = []
        for line in f:
            parts = line.strip().split('\t')
            nconst = parts[0]
            name = parts[1]
            if nconst in actor_map:
                batch.append((name, nconst))
                
            if len(batch) > 10000:
                c.executemany('UPDATE actors SET name=? WHERE nconst=?', batch)
                batch = []
        if batch: c.executemany('UPDATE actors SET name=? WHERE nconst=?', batch)

    # ... (Previous code remains the same) ...

    # 6. Final Indices
    print("Building Indexes...")
    c.execute('CREATE INDEX idx_roles_actor ON roles(actor_id)')
    c.execute('CREATE INDEX idx_roles_movie ON roles(movie_id)')
    c.execute('CREATE INDEX idx_actor_name ON actors(name)')
    
    conn.commit()
    conn.close()
    
    # --- NEW: COMPRESSION STEP ---
    print("Compressing database for GitHub...")
    with open(db_path, 'rb') as f_in:
        with gzip.open(str(db_path) + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    # Remove the raw big file so we don't accidentally push it
    os.remove(db_path)
    
    # Cleanup downloads
    for file in files:
        try: os.remove(data_dir / file)
        except: pass
        
    print(f"--- UPDATE COMPLETE. Compressed size: {os.path.getsize(str(db_path) + '.gz') / (1024*1024):.2f} MB ---")

if __name__ == "__main__":
    update_data()