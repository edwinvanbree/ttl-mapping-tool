import streamlit as st
from rdflib import Graph, URIRef
import pandas as pd
from io import BytesIO
from collections import defaultdict

st.set_page_config(page_title="TTL Data Extractor", layout="wide")
st.title("🧠 RDF Mapping Tool voor Eisen")

uploaded_file = st.file_uploader("Upload een .ttl bestand", type=["ttl"])

if uploaded_file:
    # Parse RDF
    g = Graph()
    g.parse(uploaded_file, format="turtle")

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

    st.markdown("### 🗂️ Mapping instellen")
    col1, col2, col3 = st.columns(3)

    with col1:
        predicate_eis_f = st.selectbox("Kies eigenschap voor 'Eis'", formatted_options)
    with col2:
        predicate_tekst_f = st.selectbox("Kies eigenschap voor 'Eistekst'", formatted_options)
    with col3:
        predicate_object_f = st.selectbox("Kies eigenschap voor 'Object'", formatted_options)

    # Zet om naar URIRef
    pred_eis = predicate_map[predicate_eis_f]
    pred_tekst = predicate_map[predicate_tekst_f]
    pred_object = predicate_map[predicate_object_f]

    # Verzamel triples
    eis_data = []
    for s in set(g.subjects()):
        eis = g.value(subject=s, predicate=pred_eis)
        tekst = g.value(subject=s, predicate=pred_tekst)
        obj = g.value(subject=s, predicate=pred_object)
        if eis or tekst or obj:
            eis_data.append({
                "Eis": str(eis) if eis else "",
                "Eistekst": str(tekst) if tekst else "",
                "Object": str(obj) if obj else ""
            })

    if eis_data:
        df = pd.DataFrame(eis_data)
        st.markdown("### 📋 Resultaat")
        st.dataframe(df)

        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("📅 Download als Excel", buffer.getvalue(), file_name="eisen_export.xlsx")
    else:
        st.info("Geen data gevonden op basis van de gekozen mappings.")
