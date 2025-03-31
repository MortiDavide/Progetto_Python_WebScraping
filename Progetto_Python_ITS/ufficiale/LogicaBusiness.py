import Persistenza as pers

class wishList:
    def __init__(self, id=0):
        if id == 0:
            # Se non viene passato un id, generiamo un nuovo id
            self._id = pers.cerca_ultimo_id() + 1  # Usando la funzione di persistenza per ottenere l'ID
            self._title = None
            self._price = None
            self._release_date = None
            self._description = None
            self._genres_str = None
            self._publisher = None
            self._game_url = None
            self._image_url = None
            self._stato = False  # Stato disattivato inizialmente
            self._credenziali = dict()  # Dizionario per utenza e password
        else:
            # Se viene passato un id, inizializziamo l'oggetto con i dati dell'account
            self._id = id
            diz = pers.leggiDettagli(self._id)  # Recupera i dettagli dall'archivio
            self._title = diz['title']
            self._price = diz['price']
            self._release_date = diz['release_date']
            self._description = diz['description']
            self._genres_str = diz['genres_str']
            self._publisher = diz['publisher']
            self._game_url = diz['game_url']
            self._image_url = diz['image_url']
            self._stato = diz['Stato']  # Carica lo stato (attivo o disattivato)
            self._credenziali = {}  # Vuoto inizialmente fino alla creazione dell'account

    def creazioneAccount(self, utenza, password):
        """Funzione per creare un nuovo account utente."""
        self._utenza = utenza
        self._password = password
        self._stato = True  # Stato attivo
        self._credenziali[utenza] = password
        
        # Salva i dettagli dell'account nella persistenza
        diz = {
            'id': self._id,
            'title': self._title,
            'price': self._price,
            'release_date': self._release_date,
            'description': self._description,
            'genres_str': self._genres_str,
            'publisher': self._publisher,
            'game_url': self._game_url,
            'image_url': self._image_url,
            'utenza': utenza,
            'password': password,
            'Stato': self._stato  # Aggiungi lo stato (attivo)
        }
        pers.scriviDettagli(diz)  # Salva nella persistenza
        print(f"Account creato con successo per {utenza}!")

    def disattiva_account(self, id_account):
        """Funzione per disattivare un account."""
        self._stato = False
        pers.disattiva_account(id_account)  # Impostiamo lo stato su False nella persistenza
        print(f"Account con ID {id_account} disattivato!")

    # Getter e Setter per il titolo (facoltativo)
    def get_title(self):
        return self._title

    def set_title(self, title):
        self._title = title

    # Metodo per aggiungere un gioco alla wishlist
    def aggiungi_gioco_wishlist(self):
        pers.aggiungi_gioco(self)
