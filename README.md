# Feed prodotti Trovaprezzi.it

Genera automaticamente ogni giorno il catalogo prodotti nel formato richiesto da
Trovaprezzi.it (vedi `Requisiti_tecnici_Trovaprezzi.it_Network.pdf`, campi separati da `|`,
`<endrecord>` a fine riga).

**Scope attuale:** tutti i prodotti attivi e pubblicati sull'Online Store (tutti i vendor,
tutte le categorie). Per restringere lo scope, modifica la funzione `in_scope()` in
`generate_feed.py`.

## URL del feed da comunicare a Trovaprezzi

```
https://raw.githubusercontent.com/<TUO-ACCOUNT>/<NOME-REPO>/main/feed/trovaprezzi_feed.csv
```

(sostituisci `<TUO-ACCOUNT>` e `<NOME-REPO>` con i valori reali dopo aver creato il repo)

## Setup (una tantum)

1. Crea un repository GitHub **pubblico** (deve essere pubblico perché Trovaprezzi scarichi
   il file senza autenticazione).
2. Carica questa cartella nel repo (vedi comandi sotto).
3. Vai su **Settings → Secrets and variables → Actions** del repo e aggiungi due secret:
   - `SHOPIFY_STORE` → `993d99-cc.myshopify.com`
   - `SHOPIFY_ACCESS_TOKEN` → il token da `.env` (NON committare mai `.env` nel repo)
4. Il workflow gira automaticamente ogni giorno alle 05:00 UTC. Per un test immediato:
   scheda "Actions" del repo → "Aggiorna feed Trovaprezzi" → "Run workflow".
5. Comunica l'URL del feed (sopra) al referente Trovaprezzi per il "Tour del feed".

## Comandi per il primo push

```bash
cd trovaprezzi
git init
git add .
git commit -m "Setup iniziale feed Trovaprezzi"
git branch -M main
git remote add origin https://github.com/<TUO-ACCOUNT>/<NOME-REPO>.git
git push -u origin main
```

## Note

- Spese di spedizione: calcolate in `spese_spedizione()` in `generate_feed.py`, allineate
  alla logica live del sito — casseforti (`product_type == "cassaforte"`) a peso/zona
  Centro Italia (nessuna soglia gratuita), tutte le altre categorie 9,99€ fisso sotto 100€
  e gratuite da 100€ in su. Se cambia la logica di spedizione sul sito, aggiornare qui di
  conseguenza (Trovaprezzi richiede che il feed rispecchi esattamente quanto pubblicato).
- Il file feed viene sempre scritto con lo stesso percorso (`feed/trovaprezzi_feed.csv`):
  questo mantiene stabile l'URL richiesto dalle specifiche ("non cambiare il nome del
  catalogo e del link di scaricamento").
