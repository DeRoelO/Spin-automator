# 🚧 SPIN Automator

**SPIN Automator** is een robuuste webapplicatie ontworpen om in bulk inspectie-aanvragen (MJPV) geautomatiseerd in te dienen via het Rijkswaterstaat SPIN-portaal. 

De tool rekent af met handmatig, repetitief invulwerk: het splitst lange routes automatisch op in hanteerbare vakken, berekent werkbare tijden en waarschuwt voor de 12-werkdagen regel, waarna het via een onzichtbare browser razendsnel alle meldingen indient.

## ✨ Functionaliteiten

* **Bulk Verwerking**: Verwerk onbeperkt routes verspreid over willekeurige datums in één run.
* **Slimme Route Opsplitsing**: Routes langer dan 20 kilometer worden wiskundig en naadloos opgesplitst (inclusief correcte afhandeling van kleine restvakken < 5km).
* **12-Werkdagen Assistentie**: De applicatie rekent zelf uit wat de minimale aanvraagdatum mag zijn (exclusief weekenden) en waarschuwt bij overschrijding.
* **Headless Automatisering**: Via Playwright navigeert de applicatie onzichtbaar door de ExtJS (GXT) omgeving van SPIN, accepteert het vereiste pop-ups (bijv. maximale lengte-waarschuwingen) en vult het alle wegzijdes, km-waardes en instellingen perfect in.
* **Lokale Geheugenopslag**: Gebruikersinstellingen en wachtwoorden blijven lokaal bewaard in een `user_settings.json` bestand voor supersnel hergebruik.

## 🚀 Installatie & Gebruik (Docker)

Veruit de eenvoudigste en meest schone manier om SPIN Automator te draaien is via Docker. Alle browser-afhankelijkheden (Playwright) zitten al perfect geconfigureerd in de container.

### Vereisten
* [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Starten

1. Kloon of download deze repository.
2. Open een terminal/command prompt in de map.
3. Voer het volgende commando uit:

```bash
docker-compose up --build
```

4. Ga in je webbrowser naar: `http://localhost:8501`

*(Tip: Stop de applicatie in de terminal met `CTRL+C` en gooi de container naderhand weg met `docker-compose down`)*

## 🛠️ Installatie & Gebruik (Lokaal / Handmatig)

Heb je geen Docker? Dan kun je hem ook lokaal installeren met Python.

### Vereisten
* Python 3.10 of nieuwer
* Google Chrome geïnstalleerd op je computer

### Installatie

```bash
# 1. Maak een virtuele omgeving aan (optioneel maar aanbevolen)
python -m venv venv
venv\Scripts\activate  # (Of "source venv/bin/activate" op Mac/Linux)

# 2. Installeer de Python pakketten
pip install -r requirements.txt

# 3. Installeer de Chromium browser voor Playwright
playwright install chromium
```

### Starten

```bash
streamlit run app.py
```
Er opent zich nu automatisch een browserscherm naar `http://localhost:8501`.

## ⚠️ Veiligheid en Privacy
Dit script draait **volledig lokaal** (of binnen je eigen lokale Docker container). Je SPIN-inloggegevens en persoonsgegevens worden nergens naar een externe server gestuurd. Ze worden louter in een lokaal tekstbestandje (`user_settings.json`) in de map zelf opgeslagen zodat je ze niet telkens opnieuw hoeft in te typen. Zorg ervoor dat je deze applicatie op een veilige, afgeschermde pc draait.

---
*Disclaimer: Deze tool is onafhankelijk ontwikkeld ter ondersteuning van RWS/MJPV processen.*
