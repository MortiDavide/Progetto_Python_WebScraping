# Interfaccia.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from Business_logic import (
    load_trending_games, cerca_giochi, create_price_comparison_graph, 
    get_game_by_slug, add_game_to_wishlist, saved_games, searched_games,
    authenticate_user, load_wishlist_games, register_user, remove_game_from_wishlist
)

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route('/')
def index():
    global saved_games
    if not saved_games:
        saved_games = load_trending_games()
    
    query = request.args.get('q', '').strip()  # Se non c'è una query, usa una stringa vuota
    games = saved_games  # Predefinito ai giochi di tendenza se non viene fornita alcuna query
    
    # Se esiste una query, filtriamo i giochi in base al termine di ricerca
    if query:
        games = cerca_giochi(query)  # Questo dovrebbe restituire un elenco di giochi corrispondenti alla query

    # Carica i giochi dalla wishlist tramite business logic
    wishlist_games = load_wishlist_games()
    user_wishlist_slugs = [game["slug"] for game in wishlist_games]
    
    # Crea l'HTML del grafico se sono presenti giochi
    graph_html = create_price_comparison_graph(games)
        
    # Passa i giochi e il grafico al template
    return render_template('index.html', games=games, query=query, graph_html=graph_html, 
                           wishlist_games=wishlist_games, user_wishlist_slugs=user_wishlist_slugs)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return index()  # Se non c'è una query, restituisci i giochi di tendenza
    
    # Ottieni i risultati della ricerca
    searched_games = cerca_giochi(query)
    
    # Genera l'HTML del grafico per i risultati della ricerca
    graph_html = create_price_comparison_graph(searched_games, query)

    return render_template('index.html', games=searched_games, query=query, graph_html=graph_html)

@app.route('/game/<slug>')
def game_details(slug):
    gioco_selezionato, prezzo_steam, prezzo_ig = get_game_by_slug(slug)
    
    if gioco_selezionato:
        return render_template('game.html', game=gioco_selezionato, prezzo_steam=prezzo_steam, prezzo_ig=prezzo_ig)
    
    return "Gioco non trovato", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user["id"]
            session['username'] = username
            flash('Login avvenuto con successo!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenziali non valide.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Registra un nuovo utente tramite business logic
        success, message = register_user(username, password)
        
        if success:
            flash('Registrazione avvenuta con successo! Ora puoi accedere.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'warning')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Sei uscito dall'account.", 'info')
    return redirect(url_for('index'))

@app.route('/add_to_wishlist/<slug>')
def add_to_wishlist(slug):
    if 'user_id' not in session:
        flash('Devi accedere per aggiungere giochi ai preferiti', 'warning')
        return redirect(url_for('login'))
    
    success = add_game_to_wishlist(slug)
    if not success:
        flash('Il gioco è già nella tua wishlist o non è stato trovato', 'info')
    else:
        flash('Gioco aggiunto alla wishlist con successo!', 'success')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/remove_from_wishlist/<slug>')
def remove_from_wishlist(slug):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    remove_game_from_wishlist(slug)
    flash('Gioco rimosso dalla wishlist', 'success')
    
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)