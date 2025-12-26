import sqlite3
import os
from pathlib import Path
from collections import deque

data_dir = Path.cwd() / "data_imdb"
db_path = data_dir / "imdb.db"

def get_db():
    if not db_path.exists() or os.path.getsize(db_path) == 0:
        return None
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def load_data():
    pass 

# --- ADD THESE FUNCTIONS TO graph_logic.py ---

def search_movie(title):
    conn = get_db()
    if conn is None: return []
    try:
        # Simple search by title
        # We limit to 20 to keep it fast
        query = "SELECT * FROM movies WHERE title LIKE ? ORDER BY year DESC LIMIT 20"
        rows = conn.execute(query, (f"%{title}%",)).fetchall()
        
        results = []
        for r in rows:
            results.append({
                'title': r['title'],
                'year': r['year'],
                'index': r['id']
            })
        return results
    except:
        return []
    finally:
        conn.close()

def get_movie(id):
    conn = get_db()
    if conn is None: return None
    try:
        # 1. Get Movie Basic Info
        movie = conn.execute("SELECT * FROM movies WHERE id = ?", (id,)).fetchone()
        if not movie: return None
        
        # 2. Get Cast (Actors in this movie)
        query = """
            SELECT a.name, a.id
            FROM actors a
            JOIN roles r ON a.id = r.actor_id
            WHERE r.movie_id = ?
            ORDER BY a.name ASC
        """
        rows = conn.execute(query, (id,)).fetchall()
        cast_list = [{'name': r['name'], 'index': r['id']} for r in rows]
        
        return {
            'title': movie['title'],
            'year': movie['year'],
            'cast': cast_list
        }
    except:
        return None
    finally:
        conn.close()

def search_actor(name):
    conn = get_db()
    if conn is None: return []
    try:
        # Search + Count Movies + Sort by Popularity
        query = """
            SELECT a.id, a.name, COUNT(r.movie_id) as movie_count, MAX(m.year) as last_year
            FROM actors a
            LEFT JOIN roles r ON a.id = r.actor_id
            LEFT JOIN movies m ON r.movie_id = m.id
            WHERE a.name LIKE ?
            GROUP BY a.id
            ORDER BY movie_count DESC
            LIMIT 20
        """
        rows = conn.execute(query, (f"%{name}%",)).fetchall()
        
        results = []
        for r in rows:
            results.append({
                'name': r['name'],
                'index': r['id'],
                'count': r['movie_count'],
                'last_year': r['last_year'] if r['last_year'] else 'N/A'
            })
        return results
    except:
        return []
    finally:
        conn.close()

def get_actor(id):
    conn = get_db()
    if conn is None: return None
    try:
        # 1. Get Actor Basic Info
        actor = conn.execute("SELECT * FROM actors WHERE id = ?", (id,)).fetchone()
        if not actor: return None
        
        # 2. Get Movies
        query_movies = """
            SELECT m.title, m.year, m.id 
            FROM movies m 
            JOIN roles r ON m.id = r.movie_id 
            WHERE r.actor_id = ?
            ORDER BY m.year DESC
        """
        movies = conn.execute(query_movies, (id,)).fetchall()
        filmography = [{'name': m['title'], 'year': m['year'], 'index': m['id']} for m in movies]
        
        # 3. Get Network (Costars) - NEW FEATURE
        # Finds people who played in the same movies (Limit 100 to be safe)
        query_costars = """
            SELECT DISTINCT a.name
            FROM roles r1
            JOIN roles r2 ON r1.movie_id = r2.movie_id
            JOIN actors a ON r2.actor_id = a.id
            WHERE r1.actor_id = ? AND a.id != ?
            LIMIT 100
        """
        costars_rows = conn.execute(query_costars, (id, id)).fetchall()
        costars_list = [row['name'] for row in costars_rows]
        costars_list.sort() # Alphabetical order

        return {
            'name': actor['name'], 
            'movies': filmography, 
            'costars': costars_list # Sending this to the website now
        }
    except Exception as e:
        print(e)
        return None
    finally:
        conn.close()

def bfs_path(origin, destination):
    conn = get_db()
    if conn is None: return -1, []
    try:
        cursor = conn.cursor()
        queue = deque([ (origin, []) ])
        visited = {origin}
        
        while queue:
            curr_actor, path = queue.popleft()
            if len(path) > 6: continue 
            
            cursor.execute("SELECT movie_id FROM roles WHERE actor_id=?", (curr_actor,))
            my_movies = [r[0] for r in cursor.fetchall()]
            
            for mid in my_movies:
                cursor.execute("SELECT actor_id FROM roles WHERE movie_id=?", (mid,))
                costars = [r[0] for r in cursor.fetchall()]
                
                for costar in costars:
                    if costar == destination:
                        full_path_ids = path + [mid, costar]
                        return format_result(origin, full_path_ids, conn)
                    if costar not in visited:
                        visited.add(costar)
                        queue.append((costar, path + [mid, costar]))
        return -1, []
    except:
        return -1, []
    finally:
        conn.close()

def format_result(start_id, path_ids, conn):
    try:
        result_path = []
        for i in range(0, len(path_ids), 2):
            mid = path_ids[i]
            aid = path_ids[i+1]
            m_title = conn.execute("SELECT title FROM movies WHERE id=?", (mid,)).fetchone()['title']
            a_name = conn.execute("SELECT name FROM actors WHERE id=?", (aid,)).fetchone()['name']
            result_path.append(m_title)
            result_path.append(a_name)
        return len(result_path)//2, result_path
    except:
        return -1, []