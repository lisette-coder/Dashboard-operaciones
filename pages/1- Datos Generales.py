import io
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import (
    load_data_consolidado,
    load_data_deuda,
)

# Configuración inicial de la página
st.set_page_config(
    page_title="Resumen Ejecutivo", page_icon="📊", layout="wide"
)

# ==============================================================================
# 1. CONSTANTES Y CONFIGURACIONES GLOBALES
# ==============================================================================
NOMBRES_MESES = {
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


# ==============================================================================
# 2. FUNCIONES CALLBACK Y UTILIDADES
# ==============================================================================
def cambiar_vista(nueva_vista):
    """Actualiza la vista activa en la sesión de Streamlit."""
    st.session_state.vista_activa = nueva_vista



def render_filtros_tiempo(df, sufijo_key, date_column="Fecha de Dispersión"):
    """Renderiza controles interactivos de filtrado por Año, Rango de Meses o Mes Específico."""
    if date_column not in df.columns:
        st.warning(
            f"No se encontró la columna de fecha '{date_column}' en los datos."
        )
        return df.copy(), "Sin Filtro"

    df_copia = df.copy()
    df_copia[date_column] = pd.to_datetime(df_copia[date_column], errors="coerce")
    df_copia["_Anio_Filtro"] = df_copia[date_column].dt.year
    df_copia["_Mes_Filtro"] = df_copia[date_column].dt.month

    anos_disponibles = sorted(df_copia["_Anio_Filtro"].dropna().unique())
    if not anos_disponibles:
        return df_copia, "Sin Filtro"

    col_f1, col_f2 = st.columns([1, 2])

    with col_f1:
        tipo_filtro = st.radio(
            "Filtrar por:",
            ["Año Completo", "Rango de Meses", "Mes Específico"],
            index=0,
            key=f"radio_tiempo_{sufijo_key}",
        )

    with col_f2:
        if tipo_filtro == "Mes Específico":
            anio_sel = st.selectbox(
                "Selecciona el Año",
                anos_disponibles,
                key=f"anio_mes_{sufijo_key}",
            )
            meses_disponibles = sorted(
                df_copia[df_copia["_Anio_Filtro"] == anio_sel][
                    "_Mes_Filtro"
                ].dropna().unique()
            )
            mes_sel = st.selectbox(
                "Selecciona el Mes",
                meses_disponibles,
                format_func=lambda x: NOMBRES_MESES.get(x, x),
                key=f"mes_esp_{sufijo_key}",
            )
            df_filtrado = df_copia[
                (df_copia["_Anio_Filtro"] == anio_sel)
                & (df_copia["_Mes_Filtro"] == mes_sel)
            ].copy()

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
                    list(NOMBRES_MESES.keys()),
                    format_func=lambda x: NOMBRES_MESES[x],
                    index=0,
                    key=f"mes_ini_{sufijo_key}",
                )
            with col_m2:
                mes_fin = st.selectbox(
                    "Mes Final",
                    list(NOMBRES_MESES.keys()),
                    format_func=lambda x: NOMBRES_MESES[x],
                    index=len(NOMBRES_MESES) - 1,
                    key=f"mes_fin_{sufijo_key}",
                )
            df_filtrado = df_copia[
                (df_copia["_Anio_Filtro"] == anio_sel)
                & (df_copia["_Mes_Filtro"] >= mes_inicio)
                & (df_copia["_Mes_Filtro"] <= mes_fin)
            ].copy()

        else:
            anio_sel = st.selectbox(
                "Selecciona el Año Completo",
                anos_disponibles,
                key=f"anio_comp_{sufijo_key}",
            )
            df_filtrado = df_copia[df_copia["_Anio_Filtro"] == anio_sel].copy()

    df_filtrado = df_filtrado.drop(columns=["_Anio_Filtro", "_Mes_Filtro"])
    return df_filtrado, tipo_filtro


# ==============================================================================
# 3. RENDERIZADORES DE VISTAS DINÁMICAS (GRÁFICAS Y DETALLES)
# ==============================================================================
def render_curva_financiera_generica(
    df,
    columna_metrica,
    titulo_base,
    color_linea="royalblue",
    date_column="Fecha de Dispersión",
    filtro_estatus_col=None,
    filtro_estatus_val=None,
):
    """Plantilla única reutilizable para curvas temporales sencillas."""
    st.markdown("---")
    st.subheader(f"📈 {titulo_base}")

    df_trabajo = df.copy()
    if filtro_estatus_col and filtro_estatus_val:
        df_trabajo = df_trabajo[df_trabajo[filtro_estatus_col] == filtro_estatus_val]

    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df_trabajo,
        sufijo_key=f"curva_{columna_metrica.lower().replace(' ', '_')}",
        date_column=date_column,
    )

    if date_column not in df_filtrado.columns:
        st.warning(
            f"No se encontró la columna de fecha '{date_column}' en los datos."
        )
        return

    if not df_filtrado.empty and columna_metrica in df_filtrado.columns:
        total_filtrado = df_filtrado[columna_metrica].sum()
        st.metric(
            label=f"Total Acumulado ({tipo_filtro})",
            value=f"${total_filtrado:,.2f}",
        )

    df_filtrado["Fecha_Dia"] = pd.to_datetime(
        df_filtrado[date_column], errors="coerce"
    ).dt.date
    df_agrupado = (
        df_filtrado.groupby("Fecha_Dia")[columna_metrica].sum().reset_index()
    )
    df_agrupado = df_agrupado.sort_values(by="Fecha_Dia")

    if not df_agrupado.empty:
        df_agrupado["Fecha_Str"] = pd.to_datetime(
            df_agrupado["Fecha_Dia"]
        ).dt.strftime("%Y-%m-%d")

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


def render_curva_cartera_dual(
    df, columna_metrica, titulo_base, date_column="Fecha Vencimiento"
):
    """Renderiza comparación de estatus de cobro diaria (Pendiente vs Pagado)."""
    st.markdown("---")
    st.subheader(f"📈 {titulo_base}")

    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, sufijo_key="curva_cartera_dual", date_column=date_column
    )

    if (
        date_column not in df_filtrado.columns
        or "Estatus Pago a Kamina" not in df_filtrado.columns
    ):
        st.warning(
            f"Faltan columnas necesarias ('{date_column}' o 'Estatus Pago a Kamina') en los datos."
        )
        return

    df_pendiente = df_filtrado[
        df_filtrado["Estatus Pago a Kamina"] == "To be paid"
    ].copy()
    df_pagado = df_filtrado[df_filtrado["Estatus Pago a Kamina"] == "PAID"].copy()

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

    df_pendiente["Fecha_Dia"] = pd.to_datetime(
        df_pendiente[date_column], errors="coerce"
    ).dt.date
    df_pagado["Fecha_Dia"] = pd.to_datetime(
        df_pagado[date_column], errors="coerce"
    ).dt.date

    df_pend_grouped = (
        df_pendiente.groupby("Fecha_Dia")[columna_metrica].sum().reset_index()
    )
    df_pend_grouped["Tipo_Flujo"] = "Pendiente / Por Pagar"

    df_pag_grouped = (
        df_pagado.groupby("Fecha_Dia")[columna_metrica].sum().reset_index()
    )
    df_pag_grouped["Tipo_Flujo"] = "Pagado / Liquidado"

    df_final = pd.concat([df_pend_grouped, df_pag_grouped]).dropna(
        subset=["Fecha_Dia"]
    )
    df_final = df_final.sort_values(by="Fecha_Dia")

    if not df_final.empty:
        df_final["Fecha_Str"] = pd.to_datetime(
            df_final["Fecha_Dia"]
        ).dt.strftime("%Y-%m-%d")

        fig = px.line(
            df_final,
            x="Fecha_Str",
            y=columna_metrica,
            color="Tipo_Flujo",
            markers=True,
            title=f"{titulo_base} - Vista Diaria ({tipo_filtro})",
            labels={
                "Fecha_Str": "Día",
                columna_metrica: f"{titulo_base} ($)",
                "Tipo_Flujo": "Estatus",
            },
            color_discrete_map={
                "Pendiente / Por Pagar": "darkorange",
                "Pagado / Liquidado": "forestgreen",
            },
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
            legend_title="Flujo",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "No hay datos diarios disponibles para graficar las dos líneas en este rango."
        )


def render_curva_revenue_rebate_dual(df, date_column="Fecha de Dispersión"):
    """Renderiza evolución y desglose diario de Revenue (80%) y Rebate (20%)."""
    st.markdown("---")
    st.subheader("📈 Evolución Diaria: Revenue Kamina vs. Rebate Broker")

    if "Descuento" not in df.columns:
        st.warning("No se encontró la columna 'Descuento' en los datos.")
        return

    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, sufijo_key="revenue_rebate_dual", date_column=date_column
    )

    if date_column not in df_filtrado.columns:
        st.warning(
            f"No se encontró la columna de fecha '{date_column}' en los datos."
        )
        return

    if not df_filtrado.empty:
        total_descuento = df_filtrado["Descuento"].sum()
        total_revenue = total_descuento * 0.80
        total_rebate = total_descuento * 0.20

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

    df_filtrado["Fecha_Dia"] = pd.to_datetime(
        df_filtrado[date_column], errors="coerce"
    ).dt.date
    df_filtrado["Revenue Kamina"] = df_filtrado["Descuento"] * 0.80
    df_filtrado["Rebate Broker"] = df_filtrado["Descuento"] * 0.20

    df_rev_grouped = (
        df_filtrado.groupby("Fecha_Dia")["Revenue Kamina"].sum().reset_index()
    )
    df_rev_grouped["Tipo_Flujo"] = "Revenue Kamina (80%)"
    df_rev_grouped["Monto"] = df_rev_grouped["Revenue Kamina"]

    df_reb_grouped = (
        df_filtrado.groupby("Fecha_Dia")["Rebate Broker"].sum().reset_index()
    )
    df_reb_grouped["Tipo_Flujo"] = "Rebate Broker (20%)"
    df_reb_grouped["Monto"] = df_reb_grouped["Rebate Broker"]

    df_final = pd.concat(
        [
            df_rev_grouped[["Fecha_Dia", "Tipo_Flujo", "Monto"]],
            df_reb_grouped[["Fecha_Dia", "Tipo_Flujo", "Monto"]],
        ]
    ).dropna(subset=["Fecha_Dia"])
    df_final = df_final.sort_values(by="Fecha_Dia")

    if not df_final.empty:
        df_final["Fecha_Str"] = pd.to_datetime(
            df_final["Fecha_Dia"]
        ).dt.strftime("%Y-%m-%d")

        fig = px.line(
            df_final,
            x="Fecha_Str",
            y="Monto",
            color="Tipo_Flujo",
            markers=True,
            title=f"Revenue vs Rebate - Vista Diaria ({tipo_filtro})",
            labels={
                "Fecha_Str": "Día",
                "Monto": "Monto ($)",
                "Tipo_Flujo": "Concepto",
            },
            color_discrete_map={
                "Revenue Kamina (80%)": "#0047AB",
                "Rebate Broker (20%)": "#8A2BE2",
            },
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
            legend_title="Concepto",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos diarios disponibles para graficar en este rango.")


def render_curva_clientes_activos_diarios(
    df, date_column="Fecha de Dispersión", columna_cliente="RFC Proveedor"
):
    """Renderiza actividad diaria, ticket promedio y conteo de clientes únicos."""
    st.markdown("---")
    st.subheader("📈 Actividad de Clientes y Dispersiones por Día")

    if date_column not in df.columns or columna_cliente not in df.columns:
        st.warning(
            f"Faltan columnas necesarias ('{date_column}' o '{columna_cliente}') en los datos."
        )
        return

    df_filtrado, tipo_filtro = render_filtros_tiempo(
        df, sufijo_key="clientes_activos_diarios", date_column=date_column
    )

    if df_filtrado.empty:
        st.warning("No hay datos disponibles para el filtro seleccionado.")
        return

    total_clientes_unicos = df_filtrado[columna_cliente].nunique()
    total_facturas = len(df_filtrado)

    col_monto_ticket = (
        "Monto Dispersado"
        if "Monto Dispersado" in df_filtrado.columns
        else (
            "Monto a Recibir"
            if "Monto a Recibir" in df_filtrado.columns
            else None
        )
    )

    ticket_promedio = (
        (df_filtrado[col_monto_ticket].sum() / total_facturas)
        if (col_monto_ticket and total_facturas > 0)
        else 0.0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=f"Clientes Únicos ({tipo_filtro})",
            value=f"{total_clientes_unicos:,}",
        )
    with col2:
        st.metric(
            label=f"Facturas ({tipo_filtro})",
            value=f"{total_facturas:,}",
        )
    with col3:
        st.metric(
            label=f"Ticket Promedio ({tipo_filtro})",
            value=f"${ticket_promedio:,.2f}",
        )

    df_filtrado["Fecha_Dia"] = pd.to_datetime(
        df_filtrado[date_column], errors="coerce"
    ).dt.date
    df_agrupado = (
        df_filtrado.groupby("Fecha_Dia")[columna_cliente]
        .nunique()
        .reset_index()
    )
    df_agrupado = df_agrupado.rename(
        columns={columna_cliente: "Cantidad_Clientes"}
    ).dropna(subset=["Fecha_Dia"])
    df_agrupado = df_agrupado.sort_values(by="Fecha_Dia")

    if not df_agrupado.empty:
        df_agrupado["Fecha_Str"] = pd.to_datetime(
            df_agrupado["Fecha_Dia"]
        ).dt.strftime("%Y-%m-%d")

        fig = px.line(
            df_agrupado,
            x="Fecha_Str",
            y="Cantidad_Clientes",
            markers=True,
            title=f"Evolución Diaria de Clientes Activos ({tipo_filtro})",
            labels={
                "Fecha_Str": "Día",
                "Cantidad_Clientes": "Número de Clientes",
            },
            color_discrete_sequence=["#FF1493"],
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
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos diarios de clientes para mostrar en este rango.")


def render_curva_revenue_vs_intereses(
    df_consolidado,
    df_deuda,
    date_column_conv="Fecha de Dispersión",
    date_column_deuda="Mes",
):
    """Renderiza de forma global la comparativa de Revenue vs Intereses de Deuda."""
    st.markdown("---")
    st.subheader("📈 Evolución y Análisis: Revenue Kamina vs. Intereses Cobrados")

    if df_consolidado is None or df_consolidado.empty:
        st.warning("Faltan datos en el consolidado para generar la vista.")
        return

    total_capital_fondeo = 0.0
    if (
        df_deuda is not None
        and not df_deuda.empty
        and "SC" in df_deuda.columns
    ):
        total_capital_fondeo = (
            pd.to_numeric(df_deuda["SC"], errors="coerce")
            .fillna(0)
            .sum()
        )

    col_pago_kamina = "Monto a Pagar a Kamina"
    col_estatus_pago = "Estatus Pago a Kamina"
    capital_en_calle_tobepaid = 0.0

    if (
        col_pago_kamina in df_consolidado.columns
        and col_estatus_pago in df_consolidado.columns
    ):
        mask_tobepaid = (
            df_consolidado[col_estatus_pago].astype(str).str.strip()
            == "To be paid"
        )
        capital_en_calle_tobepaid = (
            pd.to_numeric(
                df_consolidado.loc[mask_tobepaid, col_pago_kamina],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

    capital_recuperado_paid = total_capital_fondeo - capital_en_calle_tobepaid

    col1, col2, col3 = st.columns(3)
    col1.metric("Capital / Fondeo Total", f"${total_capital_fondeo:,.2f}")
    col2.metric("Capital en uso", f"${capital_en_calle_tobepaid:,.2f}")
    col3.metric(
        "Capital disponible",
        f"${capital_recuperado_paid:,.2f}",
        delta_color="off",
    )

    df_c_grouped = pd.DataFrame(columns=["Mes_Periodo", "Revenue_Kamina"])
    if (
        "Descuento" in df_consolidado.columns
        and date_column_conv in df_consolidado.columns
    ):
        rev_temp = df_consolidado[[date_column_conv, "Descuento"]].copy()
        rev_temp["Revenue_Kamina"] = (
            pd.to_numeric(rev_temp["Descuento"], errors="coerce").fillna(0)
            * 0.80
        )
        rev_temp["Mes_Periodo"] = pd.to_datetime(
            rev_temp[date_column_conv], errors="coerce"
        ).dt.to_period("M")

        df_c_grouped = rev_temp.groupby("Mes_Periodo", as_index=False)[
            "Revenue_Kamina"
        ].sum()

    df_d_grouped = pd.DataFrame(columns=["Mes_Periodo", "IP"])
    if df_deuda is not None and not df_deuda.empty:
        col_interes = "IP"
        if (
            col_interes in df_deuda.columns
            and date_column_deuda in df_deuda.columns
        ):
            int_temp = df_deuda[[date_column_deuda, col_interes]].copy()
            int_temp["Intereses_Cobrados"] = pd.to_numeric(
                int_temp[col_interes], errors="coerce"
            ).fillna(0)
            int_temp["Mes_Periodo"] = pd.to_datetime(
                int_temp[date_column_deuda], errors="coerce"
            ).dt.to_period("M")

            df_d_grouped = int_temp.groupby("Mes_Periodo", as_index=False)[
                "IP"
            ].sum()

    if not df_c_grouped.empty:
        if not df_d_grouped.empty:
            df_final = pd.merge(
                df_c_grouped, df_d_grouped, on="Mes_Periodo", how="outer"
            ).fillna(0)
        else:
            df_final = df_c_grouped
            df_final["IP"] = 0.0

        df_final = df_final.sort_values(by="Mes_Periodo")
        df_final["Mes_Str"] = df_final["Mes_Periodo"].astype(str)

        fig = px.line(
            df_final,
            x="Mes_Str",
            y=["Revenue_Kamina", "IP"],
            markers=True,
            title="Comparativa Mensual: Revenue Kamina vs Intereses Cobrados",
            labels={
                "Mes_Str": "Mes",
                "value": "Monto ($)",
                "variable": "Concepto",
            },
            color_discrete_map={
                "Revenue_Kamina": "#0047AB",
                "Intereses_Cobrados": "#8A2BE2",
            },
        )

        new_names = {
            "Revenue_Kamina": "Utilidad Bruta",
            "Intereses_Cobrados": "Intereses Cobrados",
        }
        fig.for_each_trace(
            lambda t: t.update(name=new_names.get(t.name, t.name))
        )

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
            legend_title="Métrica",
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay suficientes datos mensuales para graficar.")


# ==============================================================================
# 4. CONTROLADOR PRINCIPAL DE LA VISTA GENERAL
# ==============================================================================
def render_datos_generales(df, df_deuda):
    """Función orquestadora que renderiza el Dashboard principal de Datos Generales."""
    if df is None or df.empty:
        st.warning("No se pudieron cargar los datos o el archivo está vacío.")
        return

    # --- SECCIÓN DE FILTRO PARA TARJETAS SUPERIORES ---
    st.markdown("### 📊 Indicadores Clave de Rendimiento")
    
    # Preparación de fechas para el filtro superior
    df_copia = df.copy()
    if "Fecha de Dispersión" in df_copia.columns:
        df_copia["_Fecha_Temp"] = pd.to_datetime(df_copia["Fecha de Dispersión"], errors="coerce")
        df_copia["_Anio"] = df_copia["_Fecha_Temp"].dt.year
        df_copia["_Mes"] = df_copia["_Fecha_Temp"].dt.month
    else:
        df_copia["_Anio"] = datetime.now().year
        df_copia["_Mes"] = datetime.now().month

    anios_disponibles = sorted(df_copia["_Anio"].dropna().unique())
    if not anios_disponibles:
        anios_disponibles = [datetime.now().year]

    col_kpi_filt1, col_kpi_filt2, _ = st.columns([1, 1, 2])
    
    with col_kpi_filt1:
        anio_kpi = st.selectbox(
            "Año KPI",
            anios_disponibles,
            index=len(anios_disponibles) - 1,
            key="kpi_anio_filter"
        )

    meses_disponibles = sorted(
        df_copia[df_copia["_Anio"] == anio_kpi]["_Mes"].dropna().unique()
    )
    if not meses_disponibles:
        meses_disponibles = list(NOMBRES_MESES.keys())

    # Seleccionar por defecto el mes actual o el último mes disponible
    mes_actual_idx = datetime.now().month
    default_mes_idx = meses_disponibles.index(mes_actual_idx) if mes_actual_idx in meses_disponibles else len(meses_disponibles) - 1

    with col_kpi_filt2:
        mes_kpi = st.selectbox(
            "Filtrar Tarjetas por Mes",
            meses_disponibles,
            index=default_mes_idx,
            format_func=lambda x: NOMBRES_MESES.get(x, f"Mes {x}"),
            key="kpi_mes_filter"
        )

    # Filtrar dataframes YTD (Año actual seleccionado) y Mes (Año y Mes seleccionados)
    df_ytd = df_copia[df_copia["_Anio"] == anio_kpi]
    df_mes_actual = df_copia[(df_copia["_Anio"] == anio_kpi) & (df_copia["_Mes"] == mes_kpi)]
    nombre_mes_sel = NOMBRES_MESES.get(mes_kpi, "Mes sel.")

    # KPIS PRINCIPALES
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)

    # --- TARJETA 1: Monto Total de Dispersiones ---
    monto_mes_actual = 0.0
    monto_dia_anterior = 0.0

    if "Monto Dispersado" in df_copia.columns and "_Fecha_Temp" in df_copia.columns:
        hoy = datetime.now().date()
        
        # 1. Si el año y mes seleccionados coinciden con el año y mes actual en curso
        if anio_kpi == hoy.year and mes_kpi == hoy.month:
            # Sumamos lo acumulado del mes hasta el día de hoy
            df_hasta_hoy = df_mes_actual[df_mes_actual["_Fecha_Temp"].dt.date <= hoy]
            monto_mes_actual = df_hasta_hoy["Monto Dispersado"].sum()
            
            # Buscamos únicamente lo dispersado el día de ayer
            fecha_ayer = hoy - pd.Timedelta(days=1)
            monto_dia_anterior = df_mes_actual[
                df_mes_actual["_Fecha_Temp"].dt.date == fecha_ayer
            ]["Monto Dispersado"].sum()
        else:
            # Si se selecciona un mes/año pasado, muestra el total del mes y el último día con registros de ese mes
            monto_mes_actual = df_mes_actual["Monto Dispersado"].sum()
            if not df_mes_actual.empty:
                ultima_fecha_mes = df_mes_actual["_Fecha_Temp"].dt.date.max()
                monto_dia_anterior = df_mes_actual[
                    df_mes_actual["_Fecha_Temp"].dt.date == ultima_fecha_mes
                ]["Monto Dispersado"].sum()

        col1.metric(
            label=f"Dispersiones ({nombre_mes_sel} {anio_kpi})",
            value=f"${monto_mes_actual:,.2f}",
            delta=f"Día anterior: ${monto_dia_anterior:,.2f}",
            delta_color="off"
        )
    else:
        col1.metric(label="Dispersiones", value="Columna no encontrada")

    col1.button(
        "Ver más",
        key="btn_disp",
        on_click=cambiar_vista,
        args=("dispersiones",),
    )

    # --- TARJETA 2: Cartera De clientes ---
    pago_kamina_col = "Monto a Pagar a Kamina"
    estatus_pago_col = "Estatus Pago a Kamina"
    col_fecha_pago = "Fecha Vencimiento"

    if pago_kamina_col in df.columns and estatus_pago_col in df.columns:
        df_copia_cartera = df.copy()
        df_copia_cartera[estatus_pago_col] = (
            df_copia_cartera[estatus_pago_col].astype(str).str.strip()
        )
        df_cartera = df_copia_cartera[
            df_copia_cartera[estatus_pago_col] == "To be paid"
        ]
        total_cartera = df_cartera[pago_kamina_col].sum()

        total_acumulado_hasta_hoy = 0.0
        if col_fecha_pago and not df_cartera.empty:
            hoy = datetime.now().date()
            fechas_convertidas = pd.to_datetime(
                df_cartera[col_fecha_pago], errors="coerce"
            )
            fechas_pago = fechas_convertidas.dt.date

            mask_hasta_hoy = (fechas_pago <= hoy) & (fechas_pago.notna())
            df_hasta_hoy = df_cartera[mask_hasta_hoy]
            total_acumulado_hasta_hoy = df_hasta_hoy[pago_kamina_col].sum()

        col2.metric(
            label="Cartera de Clientes",
            value=f"${total_cartera:,.2f}",
            delta=f"Vencido hoy: ${total_acumulado_hasta_hoy:,.2f}",
        )
    else:
        col2.metric(label="Cartera Activa", value="Columnas no encontradas")

    col2.button(
        "Ver más", key="btn_cart", on_click=cambiar_vista, args=("cartera",)
    )

    # --- TARJETA 3: Revenue / Rebate ---
    if "Descuento" in df.columns:
        rev_ytd = df_ytd["Descuento"].sum() * 0.80
        reb_mes = df_mes_actual["Descuento"].sum() * 0.80

        col3.metric(
            label=f"Gross Profit ({anio_kpi})",
            value=f"${rev_ytd:,.2f}",
            delta=f"{nombre_mes_sel}: ${reb_mes:,.2f}",
            delta_color="off",
        )
    else:
        col3.metric(label="Revenue / Rebate", value="Columna no encontrada")

    col3.button(
        "Ver más", key="btn_desc", on_click=cambiar_vista, args=("descuentos",)
    )

    # --- TARJETA 4: Clientes Totales que han dispersado ---
    columna_cliente = "RFC Proveedor"
    if columna_cliente in df.columns:
        total_clientes_historico = df[columna_cliente].nunique()
        clientes_mes = (
            df_mes_actual[columna_cliente].nunique() if not df_mes_actual.empty else 0
        )

        col4.metric(
            label="Clientes Históricos",
            value=f"{total_clientes_historico:,}",
            delta=f"Activos {nombre_mes_sel}: {clientes_mes:,}",
            delta_color="off",
        )
    else:
        col4.metric(label="Total Clientes", value="Columna no encontrada")

    col4.button(
        "Ver más",
        key="btn_clientes",
        on_click=cambiar_vista,
        args=("clientes",),
    )

    # --- TARJETA 5: Costo de Intereses ---
    col_mes_deuda = "Mes"
    col_interes_deuda = "IM"

    if (
        df_deuda is not None
        and not df_deuda.empty
        and col_interes_deuda in df_deuda.columns
        and col_mes_deuda in df_deuda.columns
    ):
        df_deuda_temp = df_deuda.copy()
        df_deuda_temp["_Fecha_Temp"] = pd.to_datetime(
            df_deuda_temp[col_mes_deuda], errors="coerce"
        )

        # 1. Obtener la fila única del mes seleccionado
        df_deuda_mes = df_deuda_temp[
            (df_deuda_temp["_Fecha_Temp"].dt.year == anio_kpi)
            & (df_deuda_temp["_Fecha_Temp"].dt.month == mes_kpi)
        ]

        # Extraemos directamente el valor de la fila si existe
        if not df_deuda_mes.empty:
            total_interes_mes = df_deuda_mes[col_interes_deuda].iloc[0]

            # 2. Cálculo de días totales y transcurridos
            dias_en_mes = pd.Period(f"{anio_kpi}-{mes_kpi:02d}").days_in_month
            hoy = datetime.now()

            if anio_kpi == hoy.year and mes_kpi == hoy.month:
                dias_transcurridos = hoy.day
            elif datetime(anio_kpi, mes_kpi, 1) < datetime(hoy.year, hoy.month, 1):
                dias_transcurridos = dias_en_mes  # Mes pasado completado
            else:
                dias_transcurridos = 0  # Mes futuro

            # 3. Prorrateo proporcional a hoy
            interes_acumulado_hoy = (
                (total_interes_mes / dias_en_mes) * dias_transcurridos
                if dias_en_mes > 0
                else 0.0
            )
        else:
            interes_acumulado_hoy = 0.0

        # 4. Cálculo del mes anterior para el Delta
        if mes_kpi == 1:
            mes_ant = 12
            anio_ant = anio_kpi - 1
        else:
            mes_ant = mes_kpi - 1
            anio_ant = anio_kpi

        df_deuda_mes_ant = df_deuda_temp[
            (df_deuda_temp["_Fecha_Temp"].dt.year == anio_ant)
            & (df_deuda_temp["_Fecha_Temp"].dt.month == mes_ant)
        ]
        total_interes_mes_ant = df_deuda_mes_ant[col_interes_deuda].sum()
        nombre_mes_ant = NOMBRES_MESES.get(mes_ant, f"Mes {mes_ant}")

        # Renderizado de la tarjeta
        col5.metric(
            label=f"Linea de deuda ({nombre_mes_sel})",
            value=f"${interes_acumulado_hoy:,.2f}",
            delta=f"Mes ant. ({nombre_mes_ant}): ${total_interes_mes_ant:,.2f}",
            delta_color="off",
        )
    else:
        col5.metric(label="Intereses Cobrados", value="Datos no encontrados")

    col5.button(
        "Ver más",
        key="btn_intereses",
        on_click=cambiar_vista,
        args=("intereses",),
    )


# ==============================================================================
# 5. BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================

# Inicialización del estado de navegación si no existe
if "vista_activa" not in st.session_state:
    st.session_state.vista_activa = "dispersiones"

# Carga de datos mediante tus funciones de utils.py
with st.spinner("Procesando datos financieros y ejecutivos..."):
    df = load_data_consolidado()
    df_deuda = load_data_deuda()

# Verificación e invocación del dashboard
if df is not None and not df.empty:
    # 1. Muestra siempre la fila de 5 tarjetas KPI superiores
    render_datos_generales(
        df=df,
        df_deuda=df_deuda,
    )

    # 2. Conmutador de vistas dinámicas según el estado
    vista = st.session_state.vista_activa

    if vista == "dispersiones":
        render_curva_financiera_generica(
            df=df,
            columna_metrica="Monto Dispersado",
            titulo_base="Evolución de Dispersiones",
            color_linea="royalblue",
            date_column="Fecha de Dispersión",
        )
    elif vista == "cartera":
        render_curva_cartera_dual(
            df=df,
            columna_metrica="Monto a Pagar a Kamina",
            titulo_base="Estado de Cartera de Clientes",
            date_column="Fecha Vencimiento",
        )
    elif vista == "descuentos":
        render_curva_revenue_rebate_dual(
            df=df,
            date_column="Fecha de Dispersión",
        )
    elif vista == "clientes":
        render_curva_clientes_activos_diarios(
            df=df,
            date_column="Fecha de Dispersión",
            columna_cliente="RFC Proveedor",
        )
    elif vista == "intereses":
        render_curva_revenue_vs_intereses(
            df_consolidado=df,
            df_deuda=df_deuda,
            date_column_conv="Fecha de Dispersión",
            date_column_deuda="Mes",
        )

        # --- TABLA EXCLUSIVA PARA LÍNEA DE DEUDA ---
        st.markdown("---")
        st.markdown("### 📋 Detalle de Línea de Deuda")
        
        if df_deuda is not None and not df_deuda.empty:
            df_tabla_deuda = df_deuda.copy()
            
            # 1. Asegurar formato datetime para filtrar y formatear
            if "Mes" in df_tabla_deuda.columns:
                df_tabla_deuda["_Fecha_Temp"] = pd.to_datetime(df_tabla_deuda["Mes"], errors="coerce")
                
                # 2. Filtrar solo los registros hasta el mes actual
                hoy = datetime.now()
                primer_dia_mes_siguiente = (
                    datetime(hoy.year, hoy.month + 1, 1) if hoy.month < 12 
                    else datetime(hoy.year + 1, 1, 1)
                )
                
                df_tabla_deuda = df_tabla_deuda[df_tabla_deuda["_Fecha_Temp"] < primer_dia_mes_siguiente].copy()

            columnas_deuda = [
                "Mes",
                "SC",
                "SC (acum)",
                "TM",
                "IP",
                "AI",
            ]

            # Seleccionar únicamente las columnas que existan
            cols_existentes = [col for col in columnas_deuda if col in df_tabla_deuda.columns]

            if cols_existentes:
                # 3. Formatear la columna 'Mes' a MES-AAAA (ej. ENE-2026)
                if "Mes" in cols_existentes and "_Fecha_Temp" in df_tabla_deuda.columns:
                    # Mapeo corto de meses
                    
                    df_tabla_deuda["Mes"] = df_tabla_deuda["_Fecha_Temp"].apply(
                        lambda dt: f"{NOMBRES_MESES.get(dt.month, '')}-{dt.year}" if pd.notna(dt) else ""
                    )

                # 4. Formatear las columnas numéricas como moneda $0,000.00 y porcentaje
                
                # Excluimos 'Mes' y 'Tasa Mensual' de las columnas monetarias
                cols_moneda = [col for col in cols_existentes if col not in ["Mes", "TM"]]
                
                # Formato $0,000.00 para Dinero
                for col in cols_moneda:
                    df_tabla_deuda[col] = pd.to_numeric(df_tabla_deuda[col], errors="coerce").fillna(0)
                    df_tabla_deuda[col] = df_tabla_deuda[col].apply(lambda x: f"${x:,.2f}")

                # Formato 0.00% para Tasa Mensual
                if "TM" in cols_existentes:
                    df_tabla_deuda["TM"] = pd.to_numeric(df_tabla_deuda["TM"], errors="coerce").fillna(0)
                    
                    # NOTA: Si en tus datos el 2% viene como 0.02, usa: f"{x * 100:,.2f}%"
                    # Si en tus datos ya viene como 2.0, usa: f"{x:,.2f}%"
                    df_tabla_deuda["TM"] = df_tabla_deuda["TM"].apply(
                        lambda x: f"{x * 100:,.2f}%" if x <= 1 and x > 0 else f"{x:,.2f}%"
                    )

                # Renderizar tabla final con estilos aplicados
                st.dataframe(
                    df_tabla_deuda[cols_existentes],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.warning("No se encontraron las columnas especificadas en los datos de deuda.")
        else:
            st.warning("No hay datos disponibles para la línea de deuda.")