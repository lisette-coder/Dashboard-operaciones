from datetime import datetime
import gdown
import pandas as pd
import plotly.express as px
import streamlit as st


# Conecta a los archivos Excel y carga base de datos
# Base del consolidado 
@st.cache_data(ttl=60)
def load_data_consolidado():
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

@st.cache_data(ttl=60)
def load_data_deuda():
  drive_url = "https://docs.google.com/spreadsheets/d/1NaIOHho98ZpRMfOoyxQFW6HeKvarkUvj/edit?gid=2069564386#gid=2069564386"
  output_file = "temp_solistica_deuda.xlsx"

  try:
    if "/d/" in drive_url:
      file_id = drive_url.split("/d/")[1].split("/")[0]
      download_url = f"https://drive.google.com/uc?id={file_id}"

      gdown.download(download_url, output_file, quiet=True)

      # Lee la pestaña principal
      df_deuda = pd.read_excel(output_file, sheet_name="Resumen interes")
      return df_deuda
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
    
    if not df_filtrado.empty and columna_metrica in df_filtrado.columns:
        total_filtrado = df_filtrado[columna_metrica].sum()
        st.metric(
            label=f"Total Acumulado ({tipo_filtro})",
            value=f"${total_filtrado:,.2f}",
        )

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
    df_pendiente = df_filtrado[df_filtrado["Estatus Pago a Kamina"] == "To be paid"]
    df_pagado = df_filtrado[df_filtrado["Estatus Pago a Kamina"] == "PAID"]


    if not df_filtrado.empty and columna_metrica in df_filtrado.columns:
        total_pagado = df_pagado[columna_metrica].sum()
        total_pendiente = df_pendiente[columna_metrica].sum()

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                label=f"Dinero Cobrado ({tipo_filtro})",
                value=f"${total_pagado:,.2f}",
            )
        with col_m2:
            st.metric(
                label=f"Dinero por Cobrar ({tipo_filtro})",
                value=f"${total_pendiente:,.2f}",
            )


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


def render_curva_revenue_rebate_dual(df, date_column="Fecha de Dispersión"):
    """
    Renderiza la evolución diaria y tarjetas de resumen para Revenue Kamina y Rebate Broker.
    Muestra: Descuento Total, Revenue (80%) y Rebate (20%).
    """
    st.markdown("---")
    st.subheader("📈 Evolución Diaria: Revenue Kamina vs. Rebate Broker")

    if "Descuento" not in df.columns:
        st.warning("No se encontró la columna 'Descuento' en los datos.")
        return

    # 1. Aplicamos el filtro de tiempo usando la fecha de dispersión
    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, 
        sufijo_key="revenue_rebate_dual", 
        date_column=date_column
    )

    if date_column not in df_filtrado.columns:
        st.warning(f"No se encontró la columna de fecha '{date_column}' en los datos.")
        return

    # 2. Cálculos para las TRES tarjetas en el periodo filtrado
    if not df_filtrado.empty:
        total_descuento = df_filtrado["Descuento"].sum()
        total_revenue = total_descuento * 0.80
        total_rebate = total_descuento * 0.20

        # Mostramos 3 columnas con las métricas claras
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label=f"Ingresos Kamina ({tipo_filtro})",
                value=f"${total_descuento:,.2f}",
            )
        with col2:
            st.metric(
                label=f"Utilidad Bruta ({tipo_filtro})",
                value=f"${total_revenue:,.2f}",
            )
        with col3:
            st.metric(
                label=f"Rebate/Costo Broker ({tipo_filtro})",
                value=f"${total_rebate:,.2f}",
            )

    # 3. Preparamos los datos diarios para la gráfica de dos líneas
    df_filtrado["Fecha_Dia"] = pd.to_datetime(df_filtrado[date_column], errors="coerce").dt.date
    df_filtrado["Revenue Kamina"] = df_filtrado["Descuento"] * 0.80
    df_filtrado["Rebate Broker"] = df_filtrado["Descuento"] * 0.20

    # Agrupamos por día cada concepto
    df_rev_grouped = df_filtrado.groupby("Fecha_Dia")["Revenue Kamina"].sum().reset_index()
    df_rev_grouped["Tipo_Flujo"] = "Revenue Kamina (80%)"
    df_rev_grouped["Monto"] = df_rev_grouped["Revenue Kamina"]

    df_reb_grouped = df_filtrado.groupby("Fecha_Dia")["Rebate Broker"].sum().reset_index()
    df_reb_grouped["Tipo_Flujo"] = "Rebate Broker (20%)"
    df_reb_grouped["Monto"] = df_reb_grouped["Rebate Broker"]

    # Unimos para Plotly
    df_final = pd.concat([df_rev_grouped[["Fecha_Dia", "Tipo_Flujo", "Monto"]], 
                          df_reb_grouped[["Fecha_Dia", "Tipo_Flujo", "Monto"]]])
    df_final = df_final.dropna(subset=["Fecha_Dia"])
    df_final = df_final.sort_values(by="Fecha_Dia")

    if not df_final.empty:
        df_final["Fecha_Str"] = pd.to_datetime(df_final["Fecha_Dia"]).dt.strftime("%Y-%m-%d")

        fig = px.line(
            df_final,
            x="Fecha_Str",
            y="Monto",
            color="Tipo_Flujo",
            markers=True,
            title=f"Revenue vs Rebate - Vista Diaria ({tipo_filtro})",
            labels={"Fecha_Str": "Día", "Monto": "Monto ($)", "Tipo_Flujo": "Concepto"},
            color_discrete_map={
                "Revenue Kamina": "#0047AB",  
                "Rebate Broker": "#E4A0F8"    
            }
        )

        fig.update_traces(
            line=dict(width=2),
            marker=dict(size=6),
            hovertemplate="Día: %{x}<br>Monto: $%{y:,.2f}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="Día",
            yaxis_title="Monto ($)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            legend_title="Concepto"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos diarios disponibles para graficar en este rango.")


def render_curva_clientes_activos_diarios(df, date_column="Fecha de Dispersión", columna_cliente="Cliente"):
    """
    Renderiza 3 tarjetas (Clientes Únicos, Total de Facturas/Dispersiones y Ticket Promedio) 
    y una gráfica de líneas diaria con la cantidad de clientes únicos operando por día.
    """
    st.markdown("---")
    st.subheader("📈 Actividad de Clientes y Dispersiones por Día")

    if date_column not in df.columns or columna_cliente not in df.columns:
        st.warning(f"Faltan columnas necesarias ('{date_column}' o '{columna_cliente}') en los datos.")
        return

    # 1. Aplicamos el filtro de tiempo general
    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, 
        sufijo_key="clientes_activos_diarios", 
        date_column=date_column
    )

    if df_filtrado.empty:
        st.warning("No hay datos disponibles para el filtro seleccionado.")
        return

    # 2. Cálculos para las TRES tarjetas superiores basados estrictamente en el filtro
    total_clientes_unicos = df_filtrado[columna_cliente].nunique()
    
    # Total de facturas / dispersiones (cada fila del df filtrado representa una operación/factura)
    total_facturas = len(df_filtrado)
    
    # Ticket promedio (calculado sobre la columna de monto dispersado o equivalente, validamos cuál existe)
    col_monto_ticket = "Monto Dispersado" if "Monto Dispersado" in df_filtrado.columns else ("Monto a Recibir" if "Monto a Recibir" in df_filtrado.columns else None)
    
    if col_monto_ticket and total_facturas > 0:
        ticket_promedio = df_filtrado[col_monto_ticket].sum() / total_facturas
    else:
        ticket_promedio = 0.0

    # Mostramos las 3 tarjetas en columnas separadas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=f"Clientes Únicos ({tipo_filtro})",
            value=f"{total_clientes_unicos:,}",
        )
    with col2:
        st.metric(
            label=f"Facturas / Dispersiones ({tipo_filtro})",
            value=f"{total_facturas:,}",
        )
    with col3:
        st.metric(
            label=f"Ticket Promedio ({tipo_filtro})",
            value=f"${ticket_promedio:,.2f}",
        )

    # 3. Agrupación diaria por conteo de clientes únicos para la gráfica
    df_filtrado["Fecha_Dia"] = pd.to_datetime(df_filtrado[date_column], errors="coerce").dt.date
    df_agrupado = df_filtrado.groupby("Fecha_Dia")[columna_cliente].nunique().reset_index()
    df_agrupado = df_agrupado.rename(columns={columna_cliente: "Cantidad_Clientes"})
    df_agrupado = df_agrupado.dropna(subset=["Fecha_Dia"])
    df_agrupado = df_agrupado.sort_values(by="Fecha_Dia")

    if not df_agrupado.empty:
        df_agrupado["Fecha_Str"] = pd.to_datetime(df_agrupado["Fecha_Dia"]).dt.strftime("%Y-%m-%d")

        # 4. Gráfica de líneas con Plotly
        fig = px.line(
            df_agrupado,
            x="Fecha_Str",
            y="Cantidad_Clientes",
            markers=True,
            title=f"Evolución Diaria de Clientes Activos ({tipo_filtro})",
            labels={"Fecha_Str": "Día", "Cantidad_Clientes": "Número de Clientes"},
            color_discrete_sequence=["#FF1493"] # Verde corporativo
        )

        fig.update_traces(
            line=dict(width=2),
            marker=dict(size=6),
            hovertemplate="Día: %{x}<br>Clientes operando: %{y:,}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="Día",
            yaxis_title="Clientes Únicos",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos diarios de clientes para mostrar en este rango.")


def render_curva_revenue_vs_intereses(df_consolidado, df_deuda, date_column_conv="Fecha de Dispersión", date_column_deuda="Mes"):
    """
    Renderiza tarjetas dinámicas y la gráfica comparativa (Revenue vs Intereses)
    utilizando la totalidad de los datos (sin filtros de tiempo).
    """
    st.markdown("---")
    st.subheader("📈 Evolución y Análisis: Revenue Kamina vs. Intereses Cobrados")

    if df_consolidado is None or df_consolidado.empty:
        st.warning("Faltan datos en el consolidado para generar la vista.")
        return

    # 1. CÁLCULO DE LAS TARJETAS SUPERIORES
    total_capital_fondeo = 0.0
    if df_deuda is not None and not df_deuda.empty and "Solicitudes Capital" in df_deuda.columns:
        total_capital_fondeo = pd.to_numeric(df_deuda["Solicitudes Capital"], errors="coerce").fillna(0).sum()

    col_pago_kamina = "Monto a Pagar a Kamina"
    col_estatus_pago = "Estatus Pago a Kamina"
    capital_en_calle_tobepaid = 0.0

    if col_pago_kamina in df_consolidado.columns and col_estatus_pago in df_consolidado.columns:
        mask_tobepaid = df_consolidado[col_estatus_pago].astype(str).str.strip() == "To be paid"
        capital_en_calle_tobepaid = pd.to_numeric(df_consolidado.loc[mask_tobepaid, col_pago_kamina], errors="coerce").fillna(0).sum()

    # Dinero Disponible Real
    capital_recuperado_paid = total_capital_fondeo - capital_en_calle_tobepaid 

    # Métricas superiores
    col1, col2, col3 = st.columns(3)
    col1.metric("Capital / Fondeo Total (Banco)", f"${total_capital_fondeo:,.2f}")
    col2.metric("Capital utilizado", f"${capital_en_calle_tobepaid:,.2f}")
    col3.metric("Dinero Disponible Real", f"${capital_recuperado_paid:,.2f}", delta_color="off")

    # 2. PROCESAR REVENUE KAMINA (Sobre df_consolidado completo)
    df_c_grouped = pd.DataFrame(columns=["Mes_Periodo", "Revenue_Kamina"])
    if "Descuento" in df_consolidado.columns and date_column_conv in df_consolidado.columns:
        rev_temp = df_consolidado[[date_column_conv, "Descuento"]].copy()
        rev_temp["Revenue_Kamina"] = pd.to_numeric(rev_temp["Descuento"], errors="coerce").fillna(0) * 0.80
        rev_temp["Mes_Periodo"] = pd.to_datetime(rev_temp[date_column_conv], errors="coerce").dt.to_period("M")
        
        df_c_grouped = rev_temp.groupby("Mes_Periodo", as_index=False)["Revenue_Kamina"].sum()

    # 3. PROCESAR INTERESES COBRADOS
    df_d_grouped = pd.DataFrame(columns=["Mes_Periodo", "Intereses_Cobrados"])
    if df_deuda is not None and not df_deuda.empty:
        col_interes = "Intereses cobrados"
        if col_interes in df_deuda.columns and date_column_deuda in df_deuda.columns:
            int_temp = df_deuda[[date_column_deuda, col_interes]].copy()
            int_temp["Intereses_Cobrados"] = pd.to_numeric(int_temp[col_interes], errors="coerce").fillna(0)
            int_temp["Mes_Periodo"] = pd.to_datetime(int_temp[date_column_deuda], errors="coerce").dt.to_period("M")
            
            df_d_grouped = int_temp.groupby("Mes_Periodo", as_index=False)["Intereses_Cobrados"].sum()

    # 4. FUSIONAR Y GRAFICAR
    if not df_c_grouped.empty:
        if not df_d_grouped.empty:
            df_final = pd.merge(df_c_grouped, df_d_grouped, on="Mes_Periodo", how="outer").fillna(0)
        else:
            df_final = df_c_grouped
            df_final["Intereses_Cobrados"] = 0.0

        df_final = df_final.sort_values(by="Mes_Periodo")
        df_final["Mes_Str"] = df_final["Mes_Periodo"].astype(str)

        fig = px.line(
            df_final,
            x="Mes_Str",
            y=["Revenue_Kamina", "Intereses_Cobrados"],
            markers=True,
            title="Comparativa Mensual: Revenue Kamina vs Intereses Cobrados",
            labels={"Mes_Str": "Mes", "value": "Monto ($)", "variable": "Concepto"},
            color_discrete_map={
                "Revenue_Kamina": "#0047AB",       
                "Intereses_Cobrados": "#FF8C00"    
            }
        )

        new_names = {"Revenue_Kamina": "Revenue Kamina (80%)", "Intereses_Cobrados": "Intereses Cobrados"}
        fig.for_each_trace(lambda t: t.update(name=new_names.get(t.name, t.name)))

        fig.update_traces(
            line=dict(width=2),
            marker=dict(size=6),
            hovertemplate="Mes: %{x}<br>Monto: $%{y:,.2f}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="Mes",
            yaxis_title="Monto ($)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            legend_title="Métrica"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay suficientes datos mensuales para graficar.")