import streamlit as st

st.set_page_config(
    page_title="Portal Factoraje Solistica", page_icon="🏢", layout="wide"
)

st.title("🏢 Portal Operativo y Financiero - Factoraje Solistica 2026")
st.markdown(
    "Bienvenida al sistema integral de análisis. Utiliza el **menú lateral"
    " izquierdo** para navegar entre los diferentes módulos especializados:"
)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
  st.info(
      "📊 **Datos Generales:** Visualización global de registros, filtros"
      " dinámicos y tabla completa."
  )
  st.info(
      "💸 **Dispersiones:** Análisis detallado de montos dispersados y"
      " disposiciones."
  )

with col2:
  st.success(
      "💳 **Cobranza:** Seguimiento de estatus de operación y control de"
      " cartera."
  )
  st.success(
      "📈 **Curva de Liquidación:** Comportamiento de colocación y tendencias"
      " temporales."
  )

st.markdown("---")
st.caption(
    "💡 *Consejo:* Cualquier cambio que realices en tu archivo de Excel en"
    " Google Drive se actualizará automáticamente en las páginas al recargar la"
    " vista."
)