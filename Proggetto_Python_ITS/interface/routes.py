# interface/routes.py
from flask import render_template, request, redirect, url_for, session, flash
from business.game_service import GameService
from business.user_service import UserService
from business.wishlist_service import WishlistService

game_service = GameService()
user_service = UserService()
wishlist_service = WishlistService()

def register_routes(app):
    @app.route('/')
    def index():
        query = request.args.get('q', '').strip()
        
        # Ottieni i giochi in base alla query o di tendenza
        if query:
            games = game_service.search_games(query)
        else:
            games = game_service.get_trending_games()
        
        # Ottieni i dati della wishlist
        wishlist_games = wishlist_service.load_wishlist()
        user_wishlist_slugs = [game["slug"] for game in wishlist_games]
        
        # Genera il grafico di confronto dei prezzi
        graph_html = game_service.generate_price_graph(games)
        
        return render_template('index.html', 
                              games=games, 
                              query=query, 
                              graph_html=graph_html,
                              wishlist_games=wishlist_games, 
                              user_wishlist_slugs=user_wishlist_slugs)

    @app.route('/search')
    def search():
        query = request.args.get('q', '').strip()
        
        if not query:
            return redirect(url_for('index'))
        
        # Ottieni i risultati della ricerca
        games = game_service.search_games(query)
        
        # Genera il grafico per i risultati della ricerca
        graph_html = game_service.generate_price_graph(games)
        
        # Ottieni i dati della wishlist per l'utente attuale
        wishlist_games = wishlist_service.load_wishlist()
        user_wishlist_slugs = [game["slug"] for game in wishlist_games]
        
        no_results = False
        if games and games[0]["titolo"] == "No games available":
            no_results = True
            
        return render_template('index.html', 
                              games=games, 
                              query=query, 
                              graph_html=graph_html, 
                              wishlist_games=wishlist_games,
                              user_wishlist_slugs=user_wishlist_slugs,
                              no_results=no_results)

    @app.route('/game/<slug>')
    def game_details(slug):
        game, price_info = game_service.get_game_by_slug(slug)
        
        # Controlla se il gioco è nella wishlist dell'utente
        wishlist_games = wishlist_service.load_wishlist()
        user_wishlist_slugs = [game["slug"] for game in wishlist_games]
        in_wishlist = slug in user_wishlist_slugs
        
        if game:
            return render_template('game.html', 
                                  game=game, 
                                  prezzo_steam=price_info['steam'], 
                                  prezzo_ig=price_info['ig'],
                                  in_wishlist=in_wishlist)
        
        return "Gioco non trovato", 404

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if user_service.validate_user(username, password):
                session['user_id'] = username
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
            
            if user_service.user_exists(username):
                flash('Username già esistente!', 'warning')
            else:
                user_service.register_user(username, password)
                flash('Registrazione avvenuta con successo! Ora puoi accedere.', 'success')
                return redirect(url_for('login'))
               
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
        
        game = game_service.find_game_by_slug(slug)
        if game:
            wishlist_service.add_to_wishlist(game)
            flash('Gioco aggiunto ai preferiti!', 'success')
        
        return redirect(request.referrer or url_for('index'))

    @app.route('/remove_from_wishlist/<slug>')
    def remove_from_wishlist(slug):
        if 'user_id' not in session:
            flash('Devi accedere per rimuovere giochi dai preferiti', 'warning')
            return redirect(url_for('login'))
        
        wishlist_service.remove_from_wishlist(slug)
        flash('Gioco rimosso dai preferiti!', 'success')
        
        return redirect(request.referrer or url_for('index'))
