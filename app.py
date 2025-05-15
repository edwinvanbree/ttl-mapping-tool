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

    # Verzamel unieke eigenschappen met meerdere voorbeeldwaarden
    predicate_samples = defaultdict(list)
    for s, p, o in g:
        if not str(p).startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
            if len(predicate_samples[p]) < 5:
                predicate_samples[p].append(str(o))

    predicates = list(predicate_samples.keys())
    predicate_labels = {
        str(p): f"{str(p)} ➔ [{'; '.join(predicate_samples[p])}]"
        for p in predicates
    }
    label_to_uri = {v: k for k, v in predicate_labels.items()}

    st.markdown("### 🗂️ Mapping van Excel kolommen naar RDF eigenschappen")

    root_kolom = st.selectbox("Welke kolom bevat de 'root node'?", kolommen)

    # Initialiseer de mapping als die nog niet bestaat
    if 'kolom_mapping' not in st.session_state:
        st.session_state.kolom_mapping = {kolom: "" for kolom in kolommen}

    for kolom in kolommen:
        opties = ["-- Maak een keuze --"] + list(predicate_labels.values())

        huidige_uri = st.session_state.kolom_mapping.get(kolom, "")
        huidige_label = predicate_labels.get(huidige_uri, "-- Maak een keuze --")

        selectie = st.selectbox(
            f"Kies RDF eigenschap voor kolom '{kolom}'",
            options=opties,
            index=0 if huidige_label not in opties else None,
            key=f"select_{kolom}",
            label_visibility="visible",
            placeholder="-- Maak een keuze --"
        )

        if selectie and selectie != "-- Maak een keuze --":
            uri = label_to_uri.get(selectie)
            if uri:
                st.session_state.kolom_mapping[kolom] = uri

    kolom_mapping = {kol: URIRef(uri) for kol, uri in st.session_state.kolom_mapping.items() if uri}

    # Bouw resultaat
    resultaat_data = []
    for s in set(g.subjects()):
        root_waarde = g.value(subject=s, predicate=kolom_mapping.get(root_kolom))
        if root_waarde:
            rij = {k: "" for k in kolommen}  # alle kolommen initieel leeg
            rij[root_kolom] = str(root_waarde)
            for kolom in kolommen:
                if kolom == root_kolom:
                    continue
                pred = kolom_mapping.get(kolom)
                if pred:
                    val = g.value(subject=s, predicate=pred)
                    rij[kolom] = str(val) if val else ""
            resultaat_data.append(rij)

    if resultaat_data:
        df_resultaat = pd.DataFrame(resultaat_data)
        st.markdown("### 📋 Gematchte Data")
        st.dataframe(df_resultaat)

        buffer = BytesIO()
        df_resultaat.to_excel(buffer, index=False)
        st.download_button("📅 Download resultaat als Excel", buffer.getvalue(), file_name="rdf_mapping_export.xlsx")
    else:
        st.warning("Er is geen matchende data gevonden voor de gekozen mappings.")
