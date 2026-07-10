# MarcheMobility

Sistema di biglietteria digitale per il trasporto pubblico extraurbano
nella regione Marche. Progetto d'esame - Ingegneria del Software.

## Avvio rapido (2 comandi, dal terminale)

```bash
pip install -r requirements.txt
python run.py
```

Poi, aprire il browser su **http://127.0.0.1:8000/**

Il primo avvio crea automaticamente il database (SQLite, un singolo file
`db.sqlite3`) e alcuni dati di esempio: due corse da Ancona e un
account demo per ciascuno dei tre ruoli (Viaggiatore, Controllore,
Admin).

Una cosa importante da notare è che il mockup non corrisponderà all’interfaccia grafica finale del sito. Riprodurre fedelmente il design richiederebbe competenze avanzate di Front-End Development, che né io (Dennis) né Damiano possediamo al momento.

## Perche' SQLite, e non PostgreSQL/Docker come descritto nella tesina?

Nel Capitolo 6 della tesina il sistema e' progettato per PostgreSQL,
orchestrato tramite Docker, pensato per un utilizzo reale del servizio
(molti utenti connessi contemporaneamente, ambiente di produzione).

Questo codice e' invece la dimostrazione pratica che il progetto
funziona davvero, pensata per essere eseguita ed esaminata in modo
semplice, senza dover installare o configurare un database esterno o
Docker solo per una prova.

SQLite e' semplicemente un file sul disco (`db.sqlite3`), creato in
automatico al primo avvio: nessuna installazione, nessun server da
avviare. Dal punto di vista del codice, la differenza rispetto a
PostgreSQL e' minima: e' Django stesso a occuparsi di "tradurre" le
operazioni sul database, quindi i modelli (`core/models.py`) e tutta
la logica applicativa restano identici in entrambi i casi; cambierebbe
soltanto qualche riga di configurazione in `settings.py`.

## Cosa si puo provare

**Viaggiatore** account demo: (`mario.rossi@email.com` / `password123`)
1. Registrarsi, e poi accedere con un account
2. Cercare una corsa (provare "Ancona" -> "Pesaro")
3. Acquistare un biglietto: viene generato un vero codice QR
4. Consultare "I miei biglietti" e lo "Storico biglietti"

**Controllore** account demo: (`luca.bianchi@marchemobility.it` / `controller123`)
1. Verificare il biglietto: incollare il codice QR ottenuto durante l'acquisto
2. Se l'esito non e' valido, emettere una multa

**Admin** account demo: (`admin@marchemobility.it` / `admin123`)
1. Creare un account controllore
2. Gestire utenti e controllori (sospendere, riattivare o eliminare utenti/controllori)
3. Aggiungere/eliminare corse
4. Rispondere alle segnalazioni
5. Inviare una notifica globale
