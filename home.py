import streamlit as st
from datetime import datetime

def verificar_credenciales(usuario, password):
    # Puedes definir aquí tus usuarios o usar st.secrets para mayor seguridad en el deploy
    usuarios_permitidos = {
        "admin": "kamina2026",
    }
    
    if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == password:
        return True
    return False

def render_login():
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Acceso al Portal Financiero")
        st.markdown("Por favor, ingresa tus credenciales para continuar.")
        
        with st.form("form_login"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseñá", type="password")
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                if verificar_credenciales(usuario, password):
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = usuario
                    st.success("¡Acceso concedido! Redirigiendo...")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")








# 1. Configuración inicial de la página
st.set_page_config(
    page_title="Portal Factoraje Solistica", page_icon="🏢", layout="wide"
)

# 2. Inicializar el estado de autenticación en la sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Importamos la función de login (si la pusiste en auth.py o la tienes en el mismo archivo)
# from auth import render_login

# 3. Control de acceso principal
if not st.session_state.autenticado:
    st.title("🏢 Portal Operativo y Financiero - Kamina Credit")
    # Mostramos la pantalla de login si NO está autenticado
    render_login()
    
else:
    # --- CONTENIDO NORMAL DE TU HOME SI YA ESTÁ LOGUEADO ---
    st.title("🏢 Portal Operativo y Financiero - Kamina Credit")
    st.markdown(
        f"Bienvenida al sistema integral de análisis, **{st.session_state.get('usuario_actual', 'Usuario')}**. "
        "Utiliza el **menú lateral izquierdo** para navegar entre los diferentes módulos especializados:"
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
    
    # Botón opcional para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    st.caption(
        "💡 *Consejo:* Cualquier cambio que realices en tu archivo de Excel en"
        " Google Drive se actualizará automáticamente en las páginas al recargar la"
        " vista."
    )
