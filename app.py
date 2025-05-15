import streamlit as st
from rdflib import Graph
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="TTL Data Extractor", layout="wide")
st.title("🧠 RDF Mapping Tool voor Eisen")

uploaded_file = st.file_uploader("Upload een .ttl bestand", type=["ttl"])

if uploaded_file:
    # Parse RDF
    g = Graph()
    g.parse(uploaded_file, format="turtle")

    # Extract predicates
    predicates = sorted(set(str(p) for _, p, _ in g if not p.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#")))

    st.markdown("### 🗂️ Mapping instellen")
    col1, col2, col3 = st.columns(3)

    with col1:
        predicate_eis = st.selectbox("Kies eigenschap voor 'Eis'", predicates)
    with col2:
        predicate_tekst = st.selectbox("Kies eigenschap voor 'Eistekst'", predicates)
    with col3:
        predicate_object = st.selectbox("Kies eigenschap voor 'Object'", predicates)

    # Verzamel triples
    eis_data = []
    for s in set(g.subjects()):
        eis = g.value(subject=s, predicate=predicate_eis)
        tekst = g.value(subject=s, predicate=predicate_tekst)
        obj = g.value(subject=s, predicate=predicate_object)
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
        st.download_button("📥 Download als Excel", buffer.getvalue(), file_name="eisen_export.xlsx")
    else:
        st.info("Geen data gevonden op basis van de gekozen mappings.")
