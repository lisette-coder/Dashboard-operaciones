# utils.py
import os
import gdown
import pandas as pd
import streamlit as st


@st.cache_data(ttl=60)
def load_data():
  # Tu enlace de Google Drive
  drive_url = "https://docs.google.com/spreadsheets/d/1NaIOHho98ZpRMfOoyxQFW6HeKvarkUvj/edit?gid=2069564386#gid=2069564386"
  output_file = "temp_solistica.xlsx"

  try:
    if "/d/" in drive_url:
      file_id = drive_url.split("/d/")[1].split("/")[0]
      download_url = f"https://drive.google.com/uc?id={file_id}"

      # Descarga silenciosa desde Google Drive
      gdown.download(download_url, output_file, quiet=True, fuzzy=True)

      # Lee la pestaña principal
      df = pd.read_excel(output_file, sheet_name="Reporte Consolidado")
      return df
  except Exception as e:
    st.error(f"Error al conectar con Google Drive: {e}")
    return None