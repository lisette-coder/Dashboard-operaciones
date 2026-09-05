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
    "Monitoreo estratégico de los **20 principales clientes/proveedores** "
    "clasificados por **ticket promedio** y **frecuencia de dispersión**."
)

# Cargar datos desde utils
with st.spinner("Cargando datos desde Google Drive..."):
    df = load_data_consolidado()

if df is None or df.empty:
    st.error("No se pudieron cargar los datos de la hoja de cálculo.")
    st.stop()

# Detectar columnas necesarias
col_proveedor = "Proveedor"
col_monto = "Monto Dispersado"
col_rfc = next((c for c in df.columns if "RFC" in c.upper()), None)

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

if col_rfc:
    df_clean[col_rfc] = df_clean[col_rfc].fillna("N/A").astype(str)

# Agrupación y cálculo de métricas generales
group_cols = [col_proveedor] if not col_rfc else [col_rfc, col_proveedor]

df_resumen = df_clean.groupby(group_cols).agg(
    Ticket_Promedio=(col_monto, "mean"),
    Dispersiones=(col_monto, "count"),
    Monto_Total=(col_monto, "sum")
).reset_index()

if not col_rfc:
    df_resumen["RFC Proveedor"] = "N/A"
else:
    df_resumen.rename(columns={col_rfc: "RFC Proveedor"}, inplace=True)

df_resumen.rename(columns={col_proveedor: "Proveedor"}, inplace=True)


# =============================================================================
# SECCIÓN 1: TOP 20 — TICKET PROMEDIO MÁS ALTO
# =============================================================================
st.markdown("---")
st.header("💎 TOP 20 — CLIENTES CON TICKET PROMEDIO MÁS ALTO")

df_ticket = df_resumen.sort_values(by="Ticket_Promedio", ascending=False).head(20).copy()
df_ticket.insert(0, "Rank", range(1, len(df_ticket) + 1))

# Métricas rápidas (KPIs destacados)
kpi1, kpi2 = st.columns(2)
with kpi1:
    st.metric("Líder en Ticket Promedio", df_ticket.iloc[0]["Proveedor"])
with kpi2:
    st.metric("Ticket Máximo", f"${df_ticket.iloc[0]['Ticket_Promedio']:,.2f}")

st.write("") # Espaciador

# Tabla interactiva formateada tipo Dashboard
st.dataframe(
    df_ticket,
    column_order=["Rank", "RFC Proveedor", "Proveedor", "Ticket_Promedio", "Dispersiones", "Monto_Total"],
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", width="small"),
        "RFC Proveedor": st.column_config.TextColumn("RFC Proveedor", width="medium"),
        "Proveedor": st.column_config.TextColumn("Proveedor", width="large"),
        "Ticket_Promedio": st.column_config.ProgressColumn(
            "Ticket promedio",
            format="$%,.2f",
            min_value=0,
            max_value=float(df_ticket["Ticket_Promedio"].max()),
        ),
        "Dispersiones": st.column_config.NumberColumn("Dispersiones", format="%d"),
        "Monto_Total": st.column_config.NumberColumn("Monto total dispersado", format="$%,.2f"),
    },
    hide_index=True,
    use_container_width=True,
    height=550
)


# =============================================================================
# SECCIÓN 2: TOP 20 — MAYOR FRECUENCIA DE DISPERSIÓN
# =============================================================================
st.markdown("---")
st.header("🔄 Top 20 —CLIENTES CON MAYOR FRECUENCIA DE DISPERSIÓN")

df_frec = df_resumen.sort_values(by="Dispersiones", ascending=False).head(20).copy()
df_frec.insert(0, "Rank", range(1, len(df_frec) + 1))

# Métricas rápidas (KPIs destacados)
frec1, frec2 = st.columns(2)
with frec1:
    st.metric("Líder en Dispersiones", df_frec.iloc[0]["Proveedor"])
with frec2:
    st.metric("Máximo de Dispersiones", f"{df_frec.iloc[0]['Dispersiones']:,} ops")

st.write("") # Espaciador

# Tabla interactiva formateada tipo Dashboard
st.dataframe(
    df_frec,
    column_order=["Rank", "RFC Proveedor", "Proveedor", "Dispersiones", "Ticket_Promedio", "Monto_Total"],
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", width="small"),
        "RFC Proveedor": st.column_config.TextColumn("RFC Proveedor", width="medium"),
        "Proveedor": st.column_config.TextColumn("Proveedor", width="large"),
        "Dispersiones": st.column_config.ProgressColumn(
            "Dispersiones",
            format="%d",
            min_value=0,
            max_value=int(df_frec["Dispersiones"].max()),
        ),
        "Ticket_Promedio": st.column_config.NumberColumn("Ticket promedio", format="$%,.2f"),
        "Monto_Total": st.column_config.NumberColumn("Monto total dispersado", format="$%,.2f"),
    },
    hide_index=True,
    use_container_width=True,
    height=550
)