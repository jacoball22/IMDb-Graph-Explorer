from flask import Flask, render_template, request
import graph_logic
import os
import gzip
import shutil

app = Flask(__name__)

# UNZIPPER
DB_FILE = 'data_imdb/imdb.db'
ZIPPED_FILE = 'data_imdb/imdb.db.gz'
if not os.path.exists(DB_FILE) and os.path.exists(ZIPPED_FILE):
    print("Unzipping database...")
    with gzip.open(ZIPPED_FILE, 'rb') as f_in:
        with open(DB_FILE, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

graph_logic.load_data()

@app.route('/')
@app.route('/web')
def home():
    return render_template('index.html', mode='home')

@app.route('/web/actor')
def actor():
    search = request.args.get('search')
    aid = request.args.get('id')
    
    if aid:
        data = graph_logic.get_actor(int(aid))
        return render_template('index.html', mode='actor_profile', actor=data, movies=data['movies'], actor_id=aid)
    elif search:
        # The new graph_logic returns {name, index, count, last_year}
        results = graph_logic.search_actor(search)
        return render_template('index.html', mode='actor_search_results', candidates=results, search_term=search)
    return render_template('index.html', mode='home')

# --- ADD THIS ROUTE TO app.py ---

@app.route('/web/movie')
def movie_route():
    search = request.args.get('search')
    mid = request.args.get('id')
    
    if mid:
        # Show specific movie profile
        movie_data = graph_logic.get_movie(int(mid))
        return render_template('index.html', mode='movie_profile', movie=movie_data)
        
    elif search:
        # Show search results
        results = graph_logic.search_movie(search)
        return render_template('index.html', mode='movie_search_results', candidates=results, search_term=search)
    
    return render_template('index.html', mode='home')

@app.route('/web/distance')
def distance():
    a1_input = request.args.get('actor1')
    a2_input = request.args.get('actor2')
    
    # Intelligent Selection:
    # search_actor now sorts by POPULARITY.
    # So results[0] is the most famous "Tom Hardy".
    p1_candidates = graph_logic.search_actor(a1_input)
    p2_candidates = graph_logic.search_actor(a2_input)
    
    if not p1_candidates or not p2_candidates:
        return render_template('index.html', mode='distance_result', error="One or both actors not found.")
        
    p1 = p1_candidates[0]
    p2 = p2_candidates[0]
    
    dist, raw_path = graph_logic.bfs_path(p1['index'], p2['index'])
    
    if dist == -1:
         return render_template('index.html', mode='distance_result', error=f"No connection found between {p1['name']} and {p2['name']}.")
         
    formatted = []
    for i in range(0, len(raw_path)-1, 2):
        formatted.append({
            'movie': raw_path[i], 
            'actor_b': raw_path[i+1]
        })
        
    return render_template('index.html', mode='distance_result', 
                           distance=dist, 
                           formatted_path=formatted, 
                           start_name=p1['name'],
                           a1_input=a1_input, a2_input=a2_input)

if __name__ == '__main__':
    app.run(debug=True)