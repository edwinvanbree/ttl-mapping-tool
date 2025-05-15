import streamlit as st
from rdflib import Graph, URIRef
import pandas as pd
from io import BytesIO
from collections import defaultdict

st.set_page_config(page_title="TTL Data Extractor", layout="wide")
st.title("🧠 RDF Mapping Tool voor Eisen")

uploaded_ttl = st.file_uploader("Upload een .ttl bestand", type=["ttl"])
uploaded_excel = st.file_uploader("Upload een Excel bestand met kolomkoppen op rij 1", type=["xlsx"])

if uploaded_ttl and uploaded_excel:
    # Parse RDF
    g = Graph()
    g.parse(uploaded_ttl, format="turtle")

    # Lees Excel
    df_excel = pd.read_excel(uploaded_excel)
    kolommen = df_excel.columns.tolist()

    # Verzamel unieke eigenschappen met representatieve voorbeelddata
    predicate_samples = {}
    for s, p, o in g:
        if not str(p).startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
            if p not in predicate_samples:
                predicate_samples[p] = str(o)

    predicates = list(predicate_samples.keys())
    predicate_map = {str(p): p for p in predicate_samples.keys()}

    st.markdown("### 🗂️ Mapping van Excel kolommen naar RDF eigenschappen")

    # Root-kolom eerst kiezen
    root_kolom = st.selectbox("Welke kolom bevat de 'root node'?", kolommen)

    # Initialiseer session state mapping als het er nog niet is
    if 'kolom_mapping' not in st.session_state:
        st.session_state.kolom_mapping = {}
        st.session_state.gebruikte_predicaten = set()

    for i, kolom in enumerate(kolommen):
        if kolom in st.session_state.kolom_mapping:
            gekozen = st.session_state.kolom_mapping[kolom]
            st.markdown(f"**{kolom}** is gekoppeld aan: `{gekozen}`")
            continue

        beschikbare_predicaten = [p for p in predicate_samples if p not in st.session_state.gebruikte_predicaten]
        opties = [f"{str(p)} ➜ [{predicate_samples[p]}]" for p in beschikbare_predicaten]

        if not opties:
            st.warning("Er zijn geen beschikbare RDF-eigenschappen meer om te koppelen.")
            break

        selectie = st.selectbox(f"Kies RDF eigenschap voor kolom '{kolom}'", opties, key=f"select_{kolom}")
        uri = selectie.split(" ➜ ")[0].strip()
        gekozen_pred = URIRef(uri)
        st.session_state.kolom_mapping[kolom] = gekozen_pred
        st.session_state.gebruikte_predicaten.add(gekozen_pred)

    if len(st.session_state.kolom_mapping) < len(kolommen):
        st.warning("Niet alle kolommen zijn gemapped.")
    else:
        kolom_mapping = st.session_state.kolom_mapping
        # Bouw resultaat
        resultaat_data = []
        for s in set(g.subjects()):
            root_waarde = g.value(subject=s, predicate=kolom_mapping[root_kolom])
            if root_waarde:
                rij = {root_kolom: str(root_waarde)}
                for kolom, pred in kolom_mapping.items():
                    if kolom == root_kolom:
                        continue
                    val = g.value(subject=s, predicate=pred)
                    rij[kolom] = str(val) if val else ""
                resultaat_data.append(rij)

        if resultaat_data:
            df_resultaat = pd.DataFrame(resultaat_data)
            st.markdown("### 📋 Gematchte Data")
            st.dataframe(df_resultaat)

            buffer = BytesIO()
            df_resultaat.to_excel(buffer, index=False)
            st.download_button("📥 Download resultaat als Excel", buffer.getvalue(), file_name="rdf_mapping_export.xlsx")
        else:
            st.warning("Er is geen matchende data gevonden voor de gekozen mappings.")
