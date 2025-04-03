# app.py
from flask import Flask
from interface.routes import register_routes

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Registra tutte le route
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True)