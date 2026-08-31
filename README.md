Windows: 
# 1. Crear el entorno virtual
python -m venv venv

# 2. Activar el entorno (verás un "(venv)" al inicio de la terminal)
source venv/Scripts/activate

# 3. Instalar todas las librerías requeridas (Streamlit, Pandas, etc.)
pip install -r requirements.txt


Mac: 
# 1. Crear el entorno virtual
python3 -m venv venv

# 2. Activar el entorno
source venv/bin/activate

# 3. Instalar todas las librerías
pip install -r requirements.txt




Para ambos casos: 
streamlit run home.py