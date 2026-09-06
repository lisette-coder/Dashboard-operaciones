import streamlit as st
import pandas as pd
from utils import load_data_consolidado

# Configuración de la página
st.set_page_config(
    page_title="Clientes Prioritarios", 
    layout="wide", 
    page_icon="⭐"
)

# Encabezado principal
st.title("⭐ Clientes Prioritarios")
st.markdown(
    "Monitoreo estratégico de los **20 principales clientes** "
    "clasificados por **ticket promedio** y **frecuencia de dispersión**."
)

# Cargar datos desde utils
with st.spinner("Cargando datos..."):
    df = load_data_consolidado()

if df is None or df.empty:
    st.error("No se pudieron cargar los datos de la hoja de cálculo.")
    st.stop()

# Detectar columnas necesarias
col_proveedor = "Proveedor"
col_monto = "Monto Dispersado"

# Búsqueda flexible de la columna RFC Proveedor
col_rfc = next((c for c in df.columns if "RFC" in c.upper() and "PROVEEDOR" in c.upper()), None)

if col_proveedor not in df.columns or col_monto not in df.columns:
    st.error(
        f"No se encontraron las columnas requeridas ('{col_proveedor}' y/o '{col_monto}'). "
        f"Columnas disponibles: {list(df.columns)}"
    )
    st.stop()

# Limpieza de datos
df_clean = df.copy()
df_clean[col_monto] = pd.to_numeric(df_clean[col_monto], errors="coerce")
df_clean = df_clean.dropna(subset=[col_proveedor, col_monto])

# Agrupación y cálculo de métricas
if col_rfc:
    df_clean[col_rfc] = df_clean[col_rfc].fillna("N/A").astype(str)
    group_cols = [col_rfc, col_proveedor]
else:
    group_cols = [col_proveedor]

df_resumen = df_clean.groupby(group_cols).agg(
    Ticket_Promedio=(col_monto, "mean"),
    Dispersiones=(col_monto, "count"),
    Monto_Total=(col_monto, "sum")
).reset_index()

# Normalización de nombres de columnas para la vista
if col_rfc:
    df_resumen.rename(columns={col_rfc: "RFC Proveedor"}, inplace=True)
else:
    df_resumen["RFC Proveedor"] = "N/A"

df_resumen.rename(columns={col_proveedor: "Proveedor"}, inplace=True)


# =============================================================================
# SECCIÓN 1: 💎 TOP 20 — TICKET PROMEDIO MÁS ALTO
# =============================================================================
st.markdown("---")
st.header("💎 TOP 20 — TICKET PROMEDIO MÁS ALTO")

df_ticket = df_resumen.sort_values(by="Ticket_Promedio", ascending=False).head(20).copy()
df_ticket.insert(0, "Rank", range(1, len(df_ticket) + 1))

# Métricas rápidas (KPIs destacados)
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Líder en Ticket Promedio", df_ticket.iloc[0]["Proveedor"])
with kpi2:
    st.metric("Ticket Máximo", f"${df_ticket.iloc[0]['Ticket_Promedio']:,.2f}")
with kpi3:
    st.metric("Monto Total Dispersado (Top 20)", f"${df_ticket['Monto_Total'].sum():,.2f}")

st.write("") # Espaciador

# Copia para renderizado de la tabla con formato directo de moneda
df_ticket_view = df_ticket.copy()
df_ticket_view["Ticket promedio"] = df_ticket_view["Ticket_Promedio"].apply(lambda x: f"${x:,.2f}")
df_ticket_view["Monto total dispersado"] = df_ticket_view["Monto_Total"].apply(lambda x: f"${x:,.2f}")

st.dataframe(
    df_ticket_view,
    column_order=["Rank", "RFC Proveedor", "Proveedor", "Ticket promedio", "Dispersiones", "Monto total dispersado"],
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", width="small"),
        "RFC Proveedor": st.column_config.TextColumn("RFC Proveedor", width="medium"),
        "Proveedor": st.column_config.TextColumn("Proveedor", width="large"),
        "Ticket promedio": st.column_config.TextColumn("Ticket promedio", width="medium"),
        "Dispersiones": st.column_config.NumberColumn("Dispersiones", format="%d"),
        "Monto total dispersado": st.column_config.TextColumn("Monto total dispersado", width="medium"),
    },
    hide_index=True,
    use_container_width=True,
    height=550
)


# =============================================================================
# SECCIÓN 2: 🔄 TOP 20 — MAYOR FRECUENCIA DE DISPERSIÓN
# =============================================================================
st.markdown("---")
st.header("🔄 TOP 20 — MAYOR FRECUENCIA DE DISPERSIÓN")

df_frec = df_resumen.sort_values(by="Dispersiones", ascending=False).head(20).copy()
df_frec.insert(0, "Rank", range(1, len(df_frec) + 1))

# Métricas rápidas (KPIs destacados)
frec1, frec2, frec3 = st.columns(3)
with frec1:
    st.metric("Líder en Dispersiones", df_frec.iloc[0]["Proveedor"])
with frec2:
    st.metric("Máximo de Dispersiones", f"{df_frec.iloc[0]['Dispersiones']:,} ops")
with frec3:
    st.metric("Monto Total Dispersado (Top 20)", f"${df_frec['Monto_Total'].sum():,.2f}")

st.write("") # Espaciador

# Copia para renderizado de la tabla con formato directo de moneda
df_frec_view = df_frec.copy()
df_frec_view["Ticket promedio"] = df_frec_view["Ticket_Promedio"].apply(lambda x: f"${x:,.2f}")
df_frec_view["Monto total dispersado"] = df_frec_view["Monto_Total"].apply(lambda x: f"${x:,.2f}")

st.dataframe(
    df_frec_view,
    column_order=["Rank", "RFC Proveedor", "Proveedor", "Dispersiones", "Ticket promedio", "Monto total dispersado"],
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", width="small"),
        "RFC Proveedor": st.column_config.TextColumn("RFC Proveedor", width="medium"),
        "Proveedor": st.column_config.TextColumn("Proveedor", width="large"),
        "Dispersiones": st.column_config.NumberColumn("Dispersiones", format="%d"),
        "Ticket promedio": st.column_config.TextColumn("Ticket promedio", width="medium"),
        "Monto total dispersado": st.column_config.TextColumn("Monto total dispersado", width="medium"),
    },
    hide_index=True,
    use_container_width=True,
    height=550
)