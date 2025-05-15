import streamlit as st
from rdflib import Graph, URIRef
import pandas as pd
from io import BytesIO
from collections import defaultdict
from urllib.parse import urlparse
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components

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

    # Genereer interactieve GraphView
    st.markdown("### 🧭 RDF Model Visualisatie")
    net = Network(height='600px', directed=True)

    for s, p, o in g:
        if not str(p).startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
            net.add_node(str(s), label=str(s).split("/")[-1][:30], shape='ellipse')
            net.add_node(str(o), label=str(o).split("/")[-1][:30], shape='box')
            net.add_edge(str(s), str(o), label=str(p).split("/")[-1][:30])

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(tmp_file.name)
    with open(tmp_file.name, 'r', encoding='utf-8') as f:
        html = f.read()
    components.html(html, height=600, scrolling=True)

    st.markdown("### 🗂️ Mapping van Excel kolommen naar RDF eigenschappen")
    predicate_map = {str(p): p for p in predicate_samples.keys()}
    kolom_mapping = {}

    for kolom in kolommen:
        opties = [f"{str(p)} ➜ [{', '.join(predicate_samples[p])}]" for p in predicate_samples]
        selectie = st.selectbox(f"Kies RDF eigenschap voor kolom '{kolom}'", opties, key=kolom)
        uri = selectie.split(" ➜ ")[0].strip()
        kolom_mapping[kolom] = URIRef(uri)

    if len(kolom_mapping) < len(kolommen):
        st.warning("Niet alle kolommen zijn gemapped.")
    else:
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
