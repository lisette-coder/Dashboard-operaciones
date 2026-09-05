import streamlit as st
from utils import load_data

st.set_page_config(page_title="Dispersiones", page_icon="💸", layout="wide")

st.title("💸 Análisis de Dispersiones y Disposiciones")

df = load_data()

if df is not None:
  # Aquí filtras y analizas exclusivamente lo relacionado con dispersiones
  st.subheader("Monto Total Dispersado por Proveedor")
  if "Monto Dispersado" in df.columns and "Proveedor" in df.columns:
    disp_prov = df.groupby("Proveedor")["Monto Dispersado"].sum().reset_index()
    st.dataframe(disp_prov, use_container_width=True)
else:
  st.warning("No se pudieron cargar los datos.")