from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import load_data

st.set_page_config(
    page_title="Resumen Ejecutivo", page_icon="📊", layout="wide"
)

st.title("📊 Resumen Ejecutivo")
st.markdown(
    "Radiografía en tiempo real de la salud financiera, volúmenes de operación"
    " y estatus de cartera."
)

with st.spinner("Procesando datos financieros y ejecutivos..."):
  df = load_data()

if df is not None and not df.empty:
  # --- 0. PREPROCESAMIENTO DE FECHAS (Para Mes Actual y YTD) ---
  # Buscamos columnas de fecha comunes en reportes de factoraje
  date_column = None
  for col in ["Fecha de Dispersión", "Fecha de Factura", "Fecha", "Created At"]:
    if col in df.columns:
      date_column = col
      break

  if date_column:
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df["Mes_Año"] = df[date_column].dt.to_period("M").astype(str)
    df["Año"] = df[date_column].dt.year

    current_year = datetime.now().year
    current_month_str = datetime.now().strftime("%Y-%m")

    # Filtros temporales auxiliares
    df_ytd = df[df["Año"] == current_year]
    df_mes_actual = df[df["Mes_Año"] == current_month_str]
  else:
    df_ytd = df
    df_mes_actual = df

  # --- 1. KPIS PRINCIPALES (TARJETAS DE ALTO NIVEL) ---
  st.markdown("### 📈 Indicadores Clave de Rendimiento")
  col1, col2, col3, col4 = st.columns(4)

  # Identificar la columna de monto de facturas
  monto_factura_col = (
      "Monto Factura"
      if "Monto Factura" in df.columns
      else df.columns[
          df.columns.str.contains("Monto Factura", case=False, na=False)
      ][0]
  )

  if monto_factura_col:
    total_ytd_facturas = df_ytd[monto_factura_col].sum()
    total_mes_facturas = df_mes_actual[monto_factura_col].sum()

    col1.metric(
        label="Monto Total de Dispersiones",
        value=f"${total_ytd_facturas:,.2f}",
        delta=f"Mes actual: ${total_mes_facturas:,.2f}",
    )
  else:
    col1.metric(
        label="Monto Total de Facturas", value="Columna no encontrada"
    )

  # Identificar la columna de monto de descuentos
  descuento_col = (
      "Descuento"
      if "Descuento" in df.columns
      else df.columns[
          df.columns.str.contains("Descuento", case=False, na=False)
      ][0]
  )

  if descuento_col:
    total_ytd_descuentos = df_ytd[descuento_col].sum()
    total_mes_descuentos = df_mes_actual[descuento_col].sum()

    col2.metric(
        label="Descuentos/Ganancias ",
        value=f"${total_ytd_descuentos:,.2f}",
        delta=f"Mes actual: ${total_mes_descuentos:,.2f}",
    )
  else:
    col2.metric(label="Descuentos/Ganancias", value="Columna no encontrada")

  # Identificar la columna de To be paid
  pago_kamina_col = (
      "Monto a Pagar a Kamina"
      if "Monto a Pagar a Kamina" in df.columns
      else None
  )
  estatus_pago_col = (
      "Estatus Pago a Kamina" if "Estatus Pago a Kamina" in df.columns else None
  )

  if pago_kamina_col and estatus_pago_col:
    # Filtramos las facturas que están pendientes de pago ("To be paid")
    df_cartera_activa = df[df[estatus_pago_col] == "To be paid"]

    total_cartera_activa = df_cartera_activa[pago_kamina_col].sum()

    col3.metric(
        label="Cartera Activa (Por Cobrar)",
        value=f"${total_cartera_activa:,.2f}",
      
    )
  else:
    col3.metric(label="Cartera Activa", value="Columnas no encontradas")










  # --- 2. GRÁFICO DE BARRAS: MONTO DE FACTURAS POR MES ---
  st.markdown("---")
  st.subheader("📊 Evolución Mensual del Monto de Dispersiones")

  # Asegurarnos de tener las columnas de Mes y Año preparadas para la agrupación
  if "Mes" in df.columns and "Año" in df.columns:
    # Agrupar por año y mes para sumar el monto de facturas
    df_mensual = (
        df.groupby(["Año", "Mes"])[monto_factura_col].sum().reset_index()
    )

    # Diccionario para convertir el número de mes a nombre legible
    nombres_meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    df_mensual["Nombre_Mes"] = df_mensual["Mes"].map(nombres_meses)

    # Ordenar cronológicamente por si acaso
    df_mensual = df_mensual.sort_values(by=["Año", "Mes"])

    # Crear gráfico de barras con Plotly
    fig = px.bar(
        df_mensual,
        x="Nombre_Mes",
        y=monto_factura_col,
        text_auto=".2s",
        title="Monto Total de Facturas Procesadas por Mes",
        labels={
            "Nombre_Mes": "Mes",
            monto_factura_col: "Monto Total Facturas ($)",
        },
        color=monto_factura_col,
        color_continuous_scale="blues",
    )

    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Monto Acumulado ($)",
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
  else:
    st.warning(
        "No se encontraron las columnas 'Mes' y 'Año' para generar la gráfica"
        " mensual."
    )









  