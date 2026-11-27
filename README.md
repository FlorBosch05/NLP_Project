# Flavor Chef: eerste projectbasis

## Notebooks

De notebooks 01 tot en met 04 bevatten de keuzes en bijbehorende code. Open JupyterLab vanuit de projectmap met `uv run jupyter lab`. Voer de schrijfcellen uit om de uitvoerbare Python-bestanden te vernieuwen. Streamlit en MCP gebruiken deze bestanden als aparte processen.

Een lokale Streamlit-app met een LangGraph-router, LlamaIndex/Chroma voor recepten en een MCP-server voor porties schalen. De recepten zijn synthetische voorbeelden en moeten voor gebruik en evaluatie inhoudelijk worden gecontroleerd.

## Starten

1. Installeer Python 3.11 of 3.12 en maak een virtuele omgeving: `uv venv --python 3.12`.
2. Installeer pakketten: `uv pip install -r requirements.txt`.
3. Kopieer `.env.example` naar `.env` en vul je Groq API-sleutel in.
4. Start: `uv run streamlit run app.py`.

De eerste start downloadt een lokaal embeddingmodel. De Chroma-index wordt bij het starten van de app opnieuw opgebouwd. Stel bijvoorbeeld een vraag over een recept of vraag om een recept van twee naar vier porties te schalen.

## Stand van zaken

Dit is een eerste basis, geen voltooid MVP. De 30 voorbeeldrecepten en labels zijn nog niet onafhankelijk geverifieerd. Evaluatieset en Ragas-benchmark ontbreken nog; routing en MCP-integratie moeten met een echte API-sleutel end-to-end worden getest. De tokenweergave meet alleen de laatste generatieaanroep; TTFT en totale tokens voor router/extractie ontbreken. Conversatiegeschiedenis wordt aan de antwoordgenerator gegeven, maar niet aan de router of retrieval. Allergeeninformatie mag niet als veiligheidsadvies worden beschouwd.
