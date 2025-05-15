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

    # Verzamel predicates met voorbeelddata
    predicate_samples = defaultdict(list)
    for s, p, o in g:
        if not str(p).startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
            if len(predicate_samples[p]) < 3:
                predicate_samples[p].append(str(o))

    # Sorteer en toon alleen predicates met data
    predicates = sorted(predicate_samples.keys(), key=lambda p: str(p))

    def format_predicate(p):
        voorbeeld = ", ".join(predicate_samples[p])
        return f"{str(p)}  ➜  [{voorbeeld}]"

    formatted_options = [format_predicate(p) for p in predicates]
    predicate_map = {format_predicate(p): p for p in predicates}

    st.markdown("### 🗂️ Mapping van Excel kolommen naar RDF eigenschappen")
    kolom_mapping = {}

    for kolom in kolommen:
        selectie = st.selectbox(f"Koppel RDF eigenschap aan kolom '{kolom}'", formatted_options, key=kolom)
        kolom_mapping[kolom] = predicate_map[selectie]

    root_kolom = st.selectbox("Welke kolom bevat de 'root node'?", kolommen)

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
