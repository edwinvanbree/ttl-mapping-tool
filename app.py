import streamlit as st
from rdflib import Graph, URIRef
import pandas as pd
from io import BytesIO
from collections import defaultdict
import re

st.set_page_config(page_title="RDF naar Excel Mapper", layout="wide")
st.title("🧠 Slimme RDF Mapping Tool")

uploaded_ttl = st.file_uploader("Upload een .ttl bestand", type=["ttl"])
uploaded_excel = st.file_uploader("Upload een Excel-template met kolomnamen op rij 1", type=["xlsx"])

if uploaded_ttl and uploaded_excel:
    st.success("Bestanden succesvol ingeladen.")

    # Parse RDF
    g = Graph()
    g.parse(uploaded_ttl, format="turtle")

    # Lees Excel
    df_excel = pd.read_excel(uploaded_excel)
    kolommen = df_excel.columns.tolist()

    st.markdown("---")
    st.header("🔍 Slimme RDF Analyse")

    # Zoek kandidaten voor 'interessante' resources
    beschrijvende_predicaten = [
        "http://www.w3.org/2004/02/skos/core#prefLabel",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#value",
        "http://www.w3.org/2000/01/rdf-schema#label",
        "http://www.w3.org/2004/02/skos/core#definition"
    ]

    kandidaat_resources = defaultdict(dict)

    for s, p, o in g:
        if isinstance(o, str) or isinstance(o, URIRef):
            if str(p) in beschrijvende_predicaten:
                kandidaat_resources[s][str(p)] = str(o)

    st.write(f"Gevonden {len(kandidaat_resources)} mogelijke kernresources met beschrijvende data.")

    # Laat gebruiker kiezen welk predicaat als hoofdwaarde gebruikt moet worden
    alle_predicaten = set()
    for props in kandidaat_resources.values():
        alle_predicaten.update(props.keys())

    hoofdwaarde_pred = st.selectbox("Kies eigenschap voor hoofdwaarde (bijv. naam of omschrijving)", sorted(alle_predicaten))

    # Genereer voorstel voor mapping
    voorbeeld_data = []
    for subj, props in list(kandidaat_resources.items())[:100]:
        rij = {kol: "" for kol in kolommen}
        if hoofdwaarde_pred in props:
            rij[kolommen[0]] = props[hoofdwaarde_pred]  # eerste kolom als hoofdwaarde
        # vul andere kolommen indien beschikbaar
        for i, kol in enumerate(kolommen[1:], 1):
            for val in props.values():
                if kol.lower() in val.lower():
                    rij[kol] = val
                    break
        voorbeeld_data.append(rij)

    df_resultaat = pd.DataFrame(voorbeeld_data)
    st.markdown("### 📋 Voorbeeld gegenereerde mapping")
    st.dataframe(df_resultaat, use_container_width=True)

    buffer = BytesIO()
    df_resultaat.to_excel(buffer, index=False)
    st.download_button("📥 Download als Excel", buffer.getvalue(), file_name="rdf_mapping_result.xlsx")

else:
    st.info("Upload zowel een .ttl bestand als een Excel-template om te starten.")
