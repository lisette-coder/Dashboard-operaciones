from datetime import datetime
import pandas as pd
import streamlit as st
from utils import (
    load_data,
    mostrar_metrica,
    render_curva_financiera_generica,
    render_curva_cartera_dual,
    render_grafica_revenue_rebate_dual
)

#Importacion de Base de datos 
st.set_page_config(
    page_title="Resumen Ejecutivo", page_icon="📊", layout="wide"
)

st.title("Resumen Ejecutivo")
st.markdown(
    "Radiografía en tiempo real de la salud financiera, volúmenes de operación"
    " y estatus de cartera."
)

with st.spinner("Procesando datos financieros y ejecutivos..."):
    df = load_data()


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
    col1, col2, col3, col4 = st.columns(4)

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
            df_cartera = df[df[estatus_pago_col] == "To be paid"]
            total_cartera = df_cartera[pago_kamina_col].sum()
            
            total_hoy = 0.0
            if col_fecha_pago and not df_cartera.empty:
                hoy = datetime.now().date()
                fechas_pago = pd.to_datetime(
                    df_cartera[col_fecha_pago], errors="coerce"
                ).dt.date
                df_hoy = df_cartera[fechas_pago == hoy]
                total_hoy = df_hoy[pago_kamina_col].sum()
    
            col2.metric(
                label="Cartera de Clientes",
                value=f"${total_cartera:,.2f}",
                delta=f"Vence hoy: ${total_hoy:,.2f}",
            )
    else:
            col2.metric(label="Cartera Activa", value="Columnas no encontradas")
    
    if col2.button("Ver más", key="btn_cart"):
            st.session_state.vista_activa = "cartera"    

    # --- TARJETA 3: Revenue / Rebate ---
    mostrar_metrica(
            col3, 
            "Revenue / Rebate", 
            df_ytd, 
            df_mes_actual, 
            "Descuento"
        )
    if col3.button("Ver más", key="btn_desc"):
            st.session_state.vista_activa = "descuentos"

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
        render_grafica_revenue_rebate_dual(
            df=df, 
            date_column="Fecha de Dispersión"
        )
        

else:
    st.warning("No se pudieron cargar los datos o el archivo está vacío.")