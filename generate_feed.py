# -*- coding: utf-8 -*-
"""
Genera il catalogo prodotti per Trovaprezzi.it (formato testuale con delimitatore '|').
Specifiche: Requisiti_tecnici_Trovaprezzi.it_Network.pdf (v. 23/12/2025)

Scope attuale (primo test): solo Bordogna, tipo 'cassaforte', tag contenente 'Casseforti a muro'.
Per allargare lo scope, modifica la funzione `in_scope`.
"""
import os
import re
import html
import csv
import sys
import requests

STORE = os.environ["SHOPIFY_STORE"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
API_BASE = f"https://{STORE}/admin/api/2024-01"
SHOP_DOMAIN = "cassefortieserrature.com"

SOGLIA_SPEDIZIONE_FISSA = 100.0  # sotto questa soglia, spedizione a tariffa fissa
SPEDIZIONE_FISSA = 9.99          # tariffa fissa sotto soglia (tutte le categorie)
SPEDIZIONE_CASSAFORTE_OLTRE_SOGLIA = 20.0  # casseforti >= soglia: costo a peso/zona sul sito, valore di riferimento per il feed
SPEDIZIONE_ALTRO_OLTRE_SOGLIA = 0.0        # altre categorie >= soglia: spedizione gratuita


def spese_spedizione(product, prezzo):
    prezzo = float(prezzo or 0)
    if prezzo < SOGLIA_SPEDIZIONE_FISSA:
        return SPEDIZIONE_FISSA
    if product.get("product_type", "").strip().lower() == "cassaforte":
        return SPEDIZIONE_CASSAFORTE_OLTRE_SOGLIA
    return SPEDIZIONE_ALTRO_OLTRE_SOGLIA

FIELDS = [
    "Nome", "Marca", "Descrizione", "Prezzo di Riferimento", "Prezzo Vendita",
    "Codice Interno", "Link all'offerta", "Disponibilita", "Albero Categorie",
    "Link Immagine", "Spese di Spedizione", "Codice Produttore", "Codice EAN",
    "Peso", "Ulteriore Link Immagine 1", "Ulteriore Link Immagine 2",
    "Condizione", "Parent ID",
]


def in_scope(product):
    if product.get("vendor", "").strip().lower() != "bordogna":
        return False
    if product.get("product_type", "").strip().lower() != "cassaforte":
        return False
    tags = [t.strip().lower() for t in product.get("tags", "").split(",")]
    return any("casseforti a muro" in t for t in tags)


def fetch_products():
    products = []
    url = f"{API_BASE}/products.json"
    params = {"vendor": "Bordogna", "limit": 250, "status": "active"}
    while url:
        r = requests.get(url, headers={"X-Shopify-Access-Token": TOKEN}, params=params)
        r.raise_for_status()
        data = r.json()
        products.extend(data.get("products", []))
        link = r.headers.get("Link", "")
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
        url = next_url
        params = None  # i parametri sono già inclusi nell'URL 'next'
    return products


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def disponibilita(qty):
    if qty is None:
        return ""
    if qty >= 2:
        return "disponibile"
    if qty == 1:
        return "limitata"
    return "non disponibile"


def fmt_price(value):
    if value in (None, ""):
        return ""
    return f"{float(value):.2f}"


def build_records(products):
    records = []
    for p in products:
        if not in_scope(p):
            continue
        nome_base = strip_html(p["title"]).replace(" – ", " - ").replace("�", "-")
        marca = p.get("vendor", "")
        descrizione = strip_html(p.get("body_html", ""))[:255]
        if descrizione == nome_base:
            descrizione = ""
        tags = [t.strip() for t in p.get("tags", "").split(",") if t.strip()]
        albero = ";".join(tags) if tags else "Casseforti"
        images = p.get("images", [])
        img_main = images[0]["src"] if images else ""
        img2 = images[1]["src"] if len(images) > 1 else ""
        img3 = images[2]["src"] if len(images) > 2 else ""
        handle = p["handle"]

        for v in p.get("variants", []):
            nome = nome_base
            if v.get("title") and v["title"] != "Default Title":
                nome = f"{nome_base} {v['title']}"
            nome = nome[:255]

            link = f"https://{SHOP_DOMAIN}/products/{handle}"
            if len(p.get("variants", [])) > 1:
                link += f"?variant={v['id']}"

            prezzo = fmt_price(v.get("price"))
            prezzo_rif = ""
            compare = v.get("compare_at_price")
            if compare and float(compare) > float(v.get("price") or 0):
                prezzo_rif = fmt_price(compare)

            peso = ""
            if v.get("weight"):
                w = float(v["weight"])
                unit = v.get("weight_unit", "kg")
                if unit == "g":
                    w = w / 1000
                elif unit == "lb":
                    w = w * 0.453592
                elif unit == "oz":
                    w = w * 0.0283495
                peso = f"{w:.3f}"

            record = {
                "Nome": nome,
                "Marca": marca,
                "Descrizione": descrizione,
                "Prezzo di Riferimento": prezzo_rif,
                "Prezzo Vendita": prezzo,
                "Codice Interno": str(v["id"]),
                "Link all'offerta": link,
                "Disponibilita": disponibilita(v.get("inventory_quantity")),
                "Albero Categorie": albero,
                "Link Immagine": img_main,
                "Spese di Spedizione": fmt_price(spese_spedizione(p, v.get("price"))),
                "Codice Produttore": v.get("sku") or "",
                "Codice EAN": v.get("barcode") or "",
                "Peso": peso,
                "Ulteriore Link Immagine 1": img2,
                "Ulteriore Link Immagine 2": img3,
                "Condizione": "",
                "Parent ID": "",
            }
            records.append(record)
    return records


def write_feed(records, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("|".join(FIELDS) + " <endrecord>\n")
        for r in records:
            line = "|".join(str(r[k]) for k in FIELDS)
            f.write(line + " <endrecord>\n")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "trovaprezzi_feed.csv"
    products = fetch_products()
    print(f"Prodotti Bordogna totali (attivi): {len(products)}")
    records = build_records(products)
    print(f"Record generati (in scope: casseforti a muro): {len(records)}")
    write_feed(records, out_path)
    print(f"Scritto {out_path}")
