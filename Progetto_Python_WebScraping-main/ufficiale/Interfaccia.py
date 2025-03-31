import LogicaBusiness as cpr

# Funzione per accedere alla wishlist
def accedi_alla_wishlist():
    try:
        # Chiedi l'ID account per accedere alla wishlist
        id_account = int(input("Inserisci l'ID account per accedere: "))
        account = cpr.wishList(id_account)  # Usa il prefisso 'cpr' per importare la classe
        print("\nDettagli dell'account e la tua wishlist:")
        print(f"Titolo: {account._title}")
        print(f"Prezzo: {account._price}")
        print(f"Data di rilascio: {account._release_date}")
        print(f"Descrizione: {account._description}")
        print(f"Generi: {account._genres_str}")
        print(f"Editore: {account._publisher}")
        print(f"Link: {account._game_url}")
        print(f"Immagine: {account._image_url}")
    except Exception as e:
        print(f"Errore: {str(e)}")

# Funzione per creare un nuovo account
def crea_account():
    print("\n--- Creazione Nuovo Account ---")
    utenza = input("Inserisci il nome utente: ")
    password = input("Inserisci la tua password: ")
    # Crea un nuovo account e registra nella wishlist
    account = cpr.wishList()  # Senza ID, verrà creato un nuovo account
    account.creazioneAccount(utenza, password)
    print(f"Account creato con successo! ID account: {account._id}")

# Funzione per disattivare un account
def disattiva_account():
    try:
        id_account = int(input("Inserisci l'ID account da disattivare: "))
        account = cpr.wishList(id_account)  # Ottieni l'account esistente
        account.disattiva_account(id_account)  # Disattiva l'account
        print(f"Account con ID {id_account} disattivato con successo!")
    except Exception as e:
        print(f"Errore: {str(e)}")

# Menu principale
def menu():
    while True:
        print("\n--- MENU ---")
        print("1. Crea un nuovo account")
        print("2. Accedi alla tua wishlist")
        print("3. Disattiva un account")
        print("4. Esci")
        
        # Ottieni la scelta dell'utente
        scelta = input("Scegli un'opzione (1/2/3/4): ")

        # Usa uno switch (simulato con if-else in Python)
        if scelta == "1":
            crea_account()
        elif scelta == "2":
            accedi_alla_wishlist()
        elif scelta == "3":
            disattiva_account()
        elif scelta == "4":
            print("Uscita dal programma...")
            break
        else:
            print("Opzione non valida. Riprova.")

# Avvia il menu
menu()
