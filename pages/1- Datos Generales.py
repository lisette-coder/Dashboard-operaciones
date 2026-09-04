from datetime import datetime
import pandas as pd
import streamlit as st
from utils import (
    load_data_consolidado,
    load_data_deuda,
    mostrar_metrica,
    nombres_meses,
    render_curva_financiera_generica,
    render_curva_cartera_dual,
    render_curva_revenue_rebate_dual,
    render_curva_clientes_activos_diarios,
    render_curva_revenue_vs_intereses
)

#Importacion de Base de datos 
st.set_page_config(
    page_title="Resumen Ejecutivo", page_icon="📊", layout="wide"
)
with st.spinner("Procesando datos financieros y ejecutivos..."):
    df = load_data_consolidado() 
    df_deuda =load_data_deuda()


#Asignacion de datos a las tarjetas
if df is not None and not df.empty:
    # Preparación local de fechas para las tarjetas superiores (YTD y Mes Actual)
    if "Descuento" in df.columns:
        df["Revenue Kamina"] = df["Descuento"] * 0.80
        df["Rebate Broker"] = df["Descuento"] * 0.20
    else:
        df["Revenue Kamina"] = 0.0
        df["Rebate Broker"] = 0.0
    
    date_col = "Fecha de Dispersión"
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["Año"] = df[date_col].dt.year
        df["Mes_Año"] = df[date_col].dt.to_period("M").astype(str)

        current_year = datetime.now().year
        current_month_str = datetime.now().strftime("%Y-%m")

        df_ytd = df[df["Año"] == current_year]
        df_mes_actual = df[df["Mes_Año"] == current_month_str]
    else:
        df_ytd = df
        df_mes_actual = df

    
    # --- INICIALIZAR EL ESTADO DE LA VISTA ACTIVA ---
    if "vista_activa" not in st.session_state:
        st.session_state.vista_activa = "dispersiones"  # Vista por defecto

    # KPIS PRINCIPALES (SIEMPRE VISIBLES ARRIBA)
    st.markdown("### 📈 Indicadores Clave de Rendimiento")
    col1, col2, col3, col4, col5 = st.columns(5)

    # --- TARJETA 1: Monto Total de Dispersiones ---
    mostrar_metrica(
        col1, 
        "Monto Total de Dispersiones", 
        df_ytd, 
        df_mes_actual, 
        "Monto Dispersado"
    )
    if col1.button("Ver más", key="btn_disp"):
        st.session_state.vista_activa = "dispersiones"

     # --- TARJETA 2: Cartera De clientes ---
    pago_kamina_col = "Monto a Pagar a Kamina"
    estatus_pago_col = "Estatus Pago a Kamina"
    col_fecha_pago = "Fecha Vencimiento"
    if pago_kamina_col in df.columns and estatus_pago_col in df.columns:
        df[estatus_pago_col] = df[estatus_pago_col].astype(str).str.strip()
        df_cartera = df[df[estatus_pago_col] == "To be paid"]
        total_cartera = df_cartera[pago_kamina_col].sum()
        
        total_acumulado_hasta_hoy = 0.0
        if col_fecha_pago and not df_cartera.empty:
            hoy = datetime.now().date()

            # Forzamos la conversión de fecha y limpiamos errores
            fechas_convertidas = pd.to_datetime(df_cartera[col_fecha_pago], errors="coerce")
            fechas_pago = fechas_convertidas.dt.date
            
            # Filtramos menor o igual a hoy (excluyendo los NaT para que no rompan la lógica)
            mask_hasta_hoy = (fechas_pago <= hoy) & (fechas_pago.notna())
            df_hasta_hoy = df_cartera[mask_hasta_hoy]
            total_acumulado_hasta_hoy = df_hasta_hoy[pago_kamina_col].sum()

        col2.metric(
            label="Cartera de Clientes",
            value=f"${total_cartera:,.2f}",
            delta=f"Vencido hasta hoy: ${total_acumulado_hasta_hoy:,.2f}",
        )
    else:
        col2.metric(label="Cartera Activa", value="Columnas no encontradas")
    
    if col2.button("Ver más", key="btn_cart"):
        st.session_state.vista_activa = "cartera"   

    # --- TARJETA 3: Revenue / Rebate ---
    if "Descuento" in df.columns:
        # YTD
        rev_ytd = df_ytd["Descuento"].sum() * 0.80
        reb_ytd = df_ytd["Descuento"].sum() * 0.20
        
        col3.metric(
            label="Revenue Kamina",
            value=f"${rev_ytd:,.2f}",
            delta=f"Rebate: ${reb_ytd:,.2f}",
            delta_color="off" # Mantiene un estilo limpio sin flechas de subida/bajada
        )
    else:
        col3.metric(label="Revenue / Rebate", value="Columna no encontrada")

    if col3.button("Ver más", key="btn_desc"):
            st.session_state.vista_activa = "descuentos"

    # --- TARJETA 4: Clientes Totales que han dispersado ---
    columna_cliente = "RFC Proveedor" # Asegúrate de que este sea el nombre exacto de tu columna en el Excel
    if columna_cliente in df.columns:
        total_clientes_historico = df[columna_cliente].nunique()
        # Opcional: calculamos cuántos operaron este año en el delta
        clientes_ytd = df_ytd[columna_cliente].nunique() if not df_ytd.empty else 0
        
        col4.metric(
            label="Total Clientes Únicos",
            value=f"{total_clientes_historico:,}",
            delta=f"Activos este año: {clientes_ytd:,}",
            delta_color="off"
        )
    else:
        col4.metric(label="Total Clientes", value="Columna no encontrada")

    if col4.button("Ver más", key="btn_clientes"):
        st.session_state.vista_activa = "clientes"

    # --- TARJETA 5: Costo de Intereses (Nuevo KPI) ---
    col_mes_deuda = "Mes"       
    col_interes_deuda = "Intereses cobrados"  
    
    if df_deuda is not None and not df_deuda.empty and col_interes_deuda in df_deuda.columns and col_mes_deuda in df_deuda.columns:
        
        current_month_num = datetime.now().month
        
        # Sumatoria total de intereses en todo el DataFrame de deuda (o filtrado por año si tienes columna de año)
        total_interes_ytd = df_deuda[col_interes_deuda].sum()

        df_deuda["_Fecha_Temp"] = pd.to_datetime(df_deuda[col_mes_deuda], errors="coerce")

        # 3. Obtenemos el año y mes actual del sistema
        current_year = datetime.now().year
        current_month = datetime.now().month

        # 4. Filtramos el DataFrame para que coincida exactamente con el mes y año actual
        df_deuda_mes = df_deuda[
            (df_deuda["_Fecha_Temp"].dt.year == current_year) & 
            (df_deuda["_Fecha_Temp"].dt.month == current_month)
        ]
            
        total_interes_mes = df_deuda_mes[col_interes_deuda].sum()
        
        # Limpiamos la columna auxiliar temporal
        df_deuda = df_deuda.drop(columns=["_Fecha_Temp"], errors="ignore")

        col5.metric(
            label="Intereses Cobrados",
            value=f"${total_interes_ytd:,.2f}",
            delta=f"Mes actual: ${total_interes_mes:,.2f}",
            delta_color="off"
        )
    else:
        col5.metric(label="Intereses Cobrados", value="Datos no encontrados")

    if col5.button("Ver más", key="btn_intereses"):
        st.session_state.vista_activa = "intereses"

    # --- 3. SECCIÓN DINÁMICA INFERIOR ---
    # Usamos siempre 'df' uniformemente sin llamados duplicados a load_data()
    if st.session_state.vista_activa == "dispersiones":
        render_curva_financiera_generica(
            df=df,
            columna_metrica="Monto a Recibir",
            titulo_base="Curva de Colocación Diaria",
            color_linea="royalblue",
            date_column="Fecha de Dispersión"
            )

    elif st.session_state.vista_activa == "cartera":
        # Llamamos a la nueva función de doble línea por día
        render_curva_cartera_dual(
            df=df,
            columna_metrica="Monto a Pagar a Kamina",
            titulo_base="Curva de Liquidación y Vencimientos",
            date_column="Fecha Vencimiento"
        )
    # --- 3. Agregamos la vista dinámica para Revenue / Rebate ---
    elif st.session_state.vista_activa == "descuentos":
        render_curva_revenue_rebate_dual(
            df=df, 
            date_column="Fecha de Dispersión"
        )

    elif st.session_state.vista_activa == "clientes":
        render_curva_clientes_activos_diarios(
            df=df,
            date_column="Fecha de Dispersión",
            columna_cliente="RFC Proveedor"  
        )

    elif st.session_state.vista_activa == "intereses":
        render_curva_revenue_vs_intereses(
            df_consolidado=df,
            df_deuda=df_deuda,
            date_column_conv="Fecha de Dispersión",
            date_column_deuda="Mes"
        )
        

else:
    st.warning("No se pudieron cargar los datos o el archivo está vacío.")