from datetime import datetime
import gdown
import pandas as pd
import plotly.express as px
import streamlit as st


# Conecta al archivo Excel y carga base de datos
@st.cache_data(ttl=60)
def load_data():
  drive_url = "https://docs.google.com/spreadsheets/d/1NaIOHho98ZpRMfOoyxQFW6HeKvarkUvj/edit?gid=2069564386#gid=2069564386"
  output_file = "temp_solistica.xlsx"

  try:
    if "/d/" in drive_url:
      file_id = drive_url.split("/d/")[1].split("/")[0]
      download_url = f"https://drive.google.com/uc?id={file_id}"

      gdown.download(download_url, output_file, quiet=True)

      # Lee la pestaña principal
      df = pd.read_excel(output_file, sheet_name="Reporte Consolidado")
      return df
  except Exception as e:
    st.error(f"Error al conectar con Google Drive: {e}")
    return None

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

# Funcion para crear tarjetas tarjetas de KPI's (Titulo, Monto total, monto relevante)
def mostrar_metrica(columna_streamlit, label, df_total, df_mes, col_nombre):
  if col_nombre in df_total.columns:
    total_ytd = df_total[col_nombre].sum()
    total_mes = df_mes[col_nombre].sum()

    columna_streamlit.metric(
        label=label,
        value=f"${total_ytd:,.2f}",
        delta=f"Mes actual: ${total_mes:,.2f}",
    )
  else:
    columna_streamlit.metric(label=label, value="Columna no encontrada")


def render_filtros_tiempo(df, sufijo_key, date_column="Fecha de Dispersión"):

    if date_column not in df.columns:
        st.warning(f"No se encontró la columna de fecha '{date_column}' en los datos.")
        return df, "Sin Filtro"

    # Columnas de trabajo
    df_copia = df.copy()
    df_copia[date_column] = pd.to_datetime(df_copia[date_column], errors="coerce")
    df_copia["_Anio_Filtro"] = df_copia[date_column].dt.year
    df_copia["_Mes_Filtro"] = df_copia[date_column].dt.month
    
    anos_disponibles = sorted(df_copia["_Anio_Filtro"].dropna().unique())
    if not anos_disponibles:
        return df, "Sin Filtro"

    col_f1, col_f2 = st.columns([1, 2])

    with col_f1:
        tipo_filtro = st.radio(
            "Filtrar por:",
            ["Rango de Meses", "Mes Específico", "Año Completo"],
            key=f"radio_tiempo_{sufijo_key}",
        )

    with col_f2:
        if tipo_filtro == "Mes Específico":
            anio_sel = st.selectbox(
                "Selecciona el Año",
                anos_disponibles,
                key=f"anio_mes_{sufijo_key}",
            )
            meses_disponibles = sorted(df_copia[df_copia["_Anio_Filtro"] == anio_sel]["_Mes_Filtro"].dropna().unique())
            mes_sel = st.selectbox(
                "Selecciona el Mes",
                meses_disponibles,
                format_func=lambda x: nombres_meses.get(x, x),
                key=f"mes_esp_{sufijo_key}",
            )
            df_filtrado = df_copia[(df_copia["_Anio_Filtro"] == anio_sel) & (df_copia["_Mes_Filtro"] == mes_sel)]
        
        elif tipo_filtro == "Rango de Meses":
            anio_sel = st.selectbox(
                "Selecciona el Año para el Rango",
                anos_disponibles,
                key=f"anio_rango_{sufijo_key}",
            )
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                mes_inicio = st.selectbox(
                    "Mes Inicial",
                    list(nombres_meses.keys()),
                    format_func=lambda x: nombres_meses[x],
                    index=0,
                    key=f"mes_ini_{sufijo_key}",
                )
            with col_m2:
                mes_fin = st.selectbox(
                    "Mes Final",
                    list(nombres_meses.keys()),
                    format_func=lambda x: nombres_meses[x],
                    index=len(nombres_meses) - 1,
                    key=f"mes_fin_{sufijo_key}",
                )
            df_filtrado = df_copia[
                (df_copia["_Anio_Filtro"] == anio_sel)
                & (df_copia["_Mes_Filtro"] >= mes_inicio)
                & (df_copia["_Mes_Filtro"] <= mes_fin)
            ]

        else:
            anio_sel = st.selectbox(
                "Selecciona el Año Completo",
                anos_disponibles,
                key=f"anio_comp_{sufijo_key}",
            )
            df_filtrado = df_copia[df_copia["_Anio_Filtro"] == anio_sel]

    # Limpiamos las columnas auxiliares internas antes de regresarlo
    df_filtrado = df_filtrado.drop(columns=["_Anio_Filtro", "_Mes_Filtro"])

    return df_filtrado, tipo_filtro

#Funcion para generar la grafica de puntos
def render_curva_financiera_generica(
    df, 
    columna_metrica, 
    titulo_base, 
    color_linea="royalblue", 
    date_column="Fecha de Dispersión",
    filtro_estatus_col=None,
    filtro_estatus_val=None
):
    """
    Plantilla única reutilizable para cualquier curva temporal (Colocación, Cobro, Liquidación, etc.).
    """
    st.markdown("---")
    st.subheader(f"📈 {titulo_base}")

    # 1. Aplicar filtro de estatus previo (opcional, ej. para separar 'To be paid' o 'Paid')
    df_trabajo = df.copy()
    if filtro_estatus_col and filtro_estatus_val:
        df_trabajo = df_trabajo[df_trabajo[filtro_estatus_col] == filtro_estatus_val]

    # 2. Reutilizamos tus filtros de tiempo pasando la columna de fecha que corresponda
    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df_trabajo, 
        sufijo_key=f"curva_{columna_metrica.lower().replace(' ', '_')}", 
        date_column=date_column
    )

    if date_column not in df_filtrado.columns:
        st.warning(f"No se encontró la columna de fecha '{date_column}' en los datos.")
        return

    # 3. Procesamiento y agrupación por día
    df_filtrado["Fecha_Dia"] = pd.to_datetime(df_filtrado[date_column], errors="coerce").dt.date

    df_agrupado = (
        df_filtrado.groupby("Fecha_Dia")[columna_metrica]
        .sum()
        .reset_index()
    )
    df_agrupado = df_agrupado.sort_values(by="Fecha_Dia")

    if not df_agrupado.empty:
        df_agrupado["Fecha_Str"] = pd.to_datetime(df_agrupado["Fecha_Dia"]).dt.strftime("%Y-%m-%d")

        # 4. Renderizado con Plotly (La misma estructura visual de tu plantilla)
        fig = px.line(
            df_agrupado,
            x="Fecha_Str",
            y=columna_metrica,
            markers=True,
            title=f"{titulo_base} ({tipo_filtro})",
            labels={"Fecha_Str": "Día", columna_metrica: f"{titulo_base} ($)"},
        )

        fig.update_traces(
            line=dict(width=2, color=color_linea),
            marker=dict(size=6),
            hovertemplate="Día: %{x}<br>Monto: $%{y:,.2f}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="Día",
            yaxis_title=f"{titulo_base} ($)",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos diarios disponibles para el filtro seleccionado.")



#Funcion para curva dual

def render_curva_cartera_dual(df, columna_metrica, titulo_base, date_column="Fecha Vencimiento"):
    """
    Renderiza una gráfica con dos líneas separadas por estatus y agrupadas estrictamente por día:
    1. Lo pendiente (ej. 'To be paid' / Lo que se debía o debe pagar).
    2. Lo pagado o liquidado (o el comparativo que requieras).
    """
    st.markdown("---")
    st.subheader(f"📈 {titulo_base}")

    # 1. Reutilizamos los filtros de tiempo generales
    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, 
        sufijo_key="curva_cartera_dual", 
        date_column=date_column
    )

    if date_column not in df_filtrado.columns or "Estatus Pago a Kamina" not in df_filtrado.columns:
        st.warning(f"Faltan columnas necesarias ('{date_column}' o 'Estatus Pago a Kamina') en los datos.")
        return

    # 2. Convertimos la columna a fecha diaria estricta
    df_filtrado["Fecha_Dia"] = pd.to_datetime(df_filtrado[date_column], errors="coerce").dt.date

    # 3. Separamos los dos grupos para la gráfica de doble línea
    # Grupo A: Lo que está pendiente ("To be paid")
    df_pendiente = df_filtrado[df_filtrado["Estatus Pago a Kamina"] == "To be paid"]
    df_pend_grouped = df_pendiente.groupby("Fecha_Dia")[columna_metrica].sum().reset_index()
    df_pend_grouped["Tipo_Flujo"] = "Pendiente / Por Pagar"

    # Grupo B: Lo que ya se pagó o tiene otro estatus (puedes cambiar "Paid" por el valor real de tu Excel)
    df_pagado = df_filtrado[df_filtrado["Estatus Pago a Kamina"] == "PAID"] 
    df_pag_grouped = df_pagado.groupby("Fecha_Dia")[columna_metrica].sum().reset_index()
    df_pag_grouped["Tipo_Flujo"] = "Pagado / Liquidado"

    # 4. Unimos ambos grupos en una sola tabla para Plotly
    df_final = pd.concat([df_pend_grouped, df_pag_grouped])
    df_final = df_final.dropna(subset=["Fecha_Dia"])
    df_final = df_final.sort_values(by="Fecha_Dia")

    if not df_final.empty:
        df_final["Fecha_Str"] = pd.to_datetime(df_final["Fecha_Dia"]).dt.strftime("%Y-%m-%d")

        # 5. Gráfica de líneas múltiples por día usando el parámetro 'color'
        fig = px.line(
            df_final,
            x="Fecha_Str",
            y=columna_metrica,
            color="Tipo_Flujo",
            markers=True,
            title=f"{titulo_base} - Vista Diaria ({tipo_filtro})",
            labels={"Fecha_Str": "Día", columna_metrica: f"{titulo_base} ($)", "Tipo_Flujo": "Estatus"},
            color_discrete_map={
                "Pendiente / Por Pagar": "darkorange",
                "Pagado / Liquidado": "forestgreen"
            }
        )

        fig.update_traces(
            line=dict(width=2),
            marker=dict(size=6),
            hovertemplate="Día: %{x}<br>Monto: $%{y:,.2f}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="Día",
            yaxis_title=f"{titulo_base} ($)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            legend_title="Flujo"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos diarios disponibles para graficar las dos líneas en este rango.")


# Funcion para generar la gráfica de barras apiladas de Revenue vs Rebate por Mes
def render_grafica_revenue_rebate_dual(df, date_column="Fecha de Dispersión"):
    """
    Renderiza una gráfica de barras apiladas mensual mostrando Revenue (80%) y Rebate Broker (20%).
    """
    st.markdown("---")
    st.subheader("📊 Distribución Mensual de Ingresos: Revenue Kamina vs. Rebate Broker")

    if "Revenue Kamina" not in df.columns or "Rebate Broker" not in df.columns:
        st.warning("No se encontraron las columnas calculadas de Revenue y Rebate.")
        return

    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, 
        sufijo_key="revenue_rebate_dual", 
        date_column=date_column
    )

    if date_column not in df_filtrado.columns:
        st.warning(f"No se encontró la columna de fecha '{date_column}'.")
        return

    # Convertimos a fecha y extraemos el Periodo Mensual (YYYY-MM)
    df_filtrado["_Fecha_Parsed"] = pd.to_datetime(df_filtrado[date_column], errors="coerce")
    df_filtrado["Mes_Periodo"] = df_filtrado["_Fecha_Parsed"].dt.to_period("M").astype(str)
    
    df_agrupado = (
        df_filtrado.groupby("Mes_Periodo")[["Revenue Kamina", "Rebate Broker"]]
        .sum()
        .reset_index()
    )
    df_agrupado = df_agrupado.sort_values(by="Mes_Periodo")

    if not df_agrupado.empty:
        df_melted = df_agrupado.melt(
            id_vars=["Mes_Periodo"], 
            value_vars=["Revenue Kamina", "Rebate Broker"],
            var_name="Concepto", 
            value_name="Monto"
        )

        fig = px.bar(
            df_melted,
            x="Mes_Periodo",
            y="Monto",
            color="Concepto",
            title=f"Evolución Mensual: Revenue vs Rebate ({tipo_filtro})",
            labels={"Mes_Periodo": "Mes", "Monto": "Monto ($)", "Concepto": "Distribución"},
            color_discrete_map={
                "Revenue Kamina": "#1f77b4",  # Azul profesional
                "Rebate Broker": "#ff7f0e"     # Naranja / ámbar
            },
            barmode="stack"
        )

        fig.update_traces(
            hovertemplate="Mes: %{x}<br>%{customdata}: $%{y:,.2f}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="Mes",
            yaxis_title="Monto Total ($)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            legend_title="Concepto"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para mostrar la distribución mensual en este rango.")