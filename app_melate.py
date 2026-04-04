import streamlit as st
import pandas as pd
import random
import datetime
import numpy as np
from supabase import create_client, Client

# --- CONEXIÓN A LA BASE DE DATOS PROFESIONAL ---
@st.cache_resource
def iniciar_conexion():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = iniciar_conexion()

# --- INICIALIZACIÓN DE MEMORIA (SESSION STATE) ---
if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = False

if 'rol' not in st.session_state:
    st.session_state['rol'] = None

if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Optimizador Melate", page_icon="🎱", layout="centered")

# --- INYECCIÓN DE DISEÑO CSS (El toque del decorador) ---
st.markdown("""
    <style>
    /* Diseño para los boletos generados */
    .boleto-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2b2b2b 100%);
        border-left: 6px solid #ff4b4b;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
    }
    .boleto-titulo {
        color: #ff4b4b;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .boleto-numeros {
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# --- NUEVO MOTOR DE DATOS ---
@st.cache_data(ttl=600) # Guarda los datos en memoria por 10 min para que sea súper rápido
def cargar_datos():
    # 1. Extraer los datos de la bóveda
    respuesta = supabase.table("sorteos").select("*").order("concurso").execute()
    
    # 2. Convertirlos a Pandas (para que tu algoritmo estadístico siga funcionando intacto)
    df = pd.DataFrame(respuesta.data)
    
    # 3. Poner las columnas en MAYÚSCULAS para que tu código actual no note la diferencia
    df.columns = df.columns.str.upper()
    return df

# --- NUEVO SISTEMA DE USUARIOS REAL ---
def validar_usuario(username, password):
    # Busca en la bóveda si el usuario y la contraseña coinciden
    respuesta = supabase.table("usuarios").select("*").eq("username", username).eq("password", password).execute()
    
    if len(respuesta.data) > 0:
        return respuesta.data[0]["rol"] # Te devuelve 'Admin', 'Premium' o 'Gratis'
    return None

def cerrar_sesion():
    # Limpiamos la memoria para "cerrar la puerta"
    st.session_state['usuario_autenticado'] = False
    st.session_state['rol'] = None
    st.session_state['username'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['usuario_autenticado']:
    st.title("🔒 Acceso al Optimizador Melate")
    st.markdown("Inicia sesión para usar el motor estadístico.")
    with st.form("login_form"):
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        btn_login = st.form_submit_button("Entrar")
        
        if btn_login:
            # Mandamos llamar a nuestra nueva bóveda en Supabase
            rol_encontrado = validar_usuario(user, pwd)
            
            if rol_encontrado:
                st.session_state['usuario_autenticado'] = True
                st.session_state['rol'] = rol_encontrado
                st.session_state['username'] = user
                st.rerun() # Si todo está bien, recarga y te deja entrar
            else:
                st.error("Usuario o contraseña incorrectos. Intenta de nuevo.") # Mensaje de error si falla
    st.stop()

st.markdown("---")
st.subheader("🚀 Desbloquea el Motor VIP")
st.write("Deja de jugar a ciegas. Obtén acceso al filtro estadístico y generador de combinaciones Premium.")

# Tu botón de venta
st.markdown("""
<a href="https://mpago.la/1hAQ3xr" target="_blank">
    <button style="background-color:#009EE3; color:white; padding:10px 20px; border-radius:5px; border:none; font-weight:bold; cursor:pointer;">
        👉 Suscribirse por $99/mes
    </button>
</a>
""", unsafe_allow_html=True)

st.info("📲 **¿Ya pagaste?** Envía tu comprobante por WhatsApp al **+52 7771049944** y te enviaremos tu Usuario y Contraseña VIP en menos de 10 minutos.")
st.markdown("---")

# ==========================================
# --- 2. APLICACIÓN PRINCIPAL (La Bóveda) ---
# ==========================================
st.sidebar.title("🎱 Mi Cuenta")
st.sidebar.info(f"Nivel Actual: **{st.session_state['rol']}**")
if st.sidebar.button("Cerrar Sesión"):
    cerrar_sesion()
    st.rerun()

@st.cache_data
def cargar_historico():
    try:
        df = pd.read_csv('melate.csv')
        columnas_utiles = ['CONCURSO', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'FECHA']
        if not all(col in df.columns for col in columnas_utiles):
             return pd.DataFrame(columns=columnas_utiles), ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']
        df = df[columnas_utiles].copy()
        df = df.dropna()
        esferas = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']
        df[esferas] = df[esferas].astype(int)
        df['R7'] = df['R7'].astype(int)
        return df, esferas
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None, None

def es_combinacion_optimizada(combinacion, df_historico, columnas_esferas):
    if not (114 <= sum(combinacion) <= 192): return False
    pares = sum(1 for n in combinacion if n % 2 == 0)
    if pares not in [2, 3, 4]: return False
    for i in range(len(combinacion) - 2):
        if combinacion[i+2] - combinacion[i] == 2: return False
    if df_historico is not None and not df_historico.empty:
        ya_salio = (df_historico[columnas_esferas] == combinacion).all(axis=1).any()
        if ya_salio: return False 
    return True

def generar_boletos(cantidad, df_historico, columnas_esferas):
    boletos_aprobados = []
    intentos = 0
    while len(boletos_aprobados) < cantidad:
        intento = sorted(random.sample(range(1, 57), 6))
        intentos += 1
        if es_combinacion_optimizada(intento, df_historico, columnas_esferas):
            boletos_aprobados.append(intento)
    return boletos_aprobados, intentos

def guardar_nuevo_sorteo(concurso, fecha, r1, r2, r3, r4, r5, r6, r7):
    try:
        # 1. Empaquetamos los datos exactamente como Supabase los pide
        nuevo_registro = {
            "concurso": int(concurso),
            "r1": int(r1),
            "r2": int(r2),
            "r3": int(r3),
            "r4": int(r4),
            "r5": int(r5),
            "r6": int(r6),
            "r7": int(r7),
            "fecha": str(fecha) # Aseguramos formato de texto YYYY-MM-DD
        }
        
        # 2. Enviamos los datos a la bóveda en la nube
        supabase.table("sorteos").insert(nuevo_registro).execute()
        
        # 3. ¡Paso CRUCIAL! Le decimos a la app que olvide los datos viejos
        st.cache_data.clear() 
        
        return True, f"✅ ¡Sorteo {concurso} guardado exitosamente en la nube!"
        
    except Exception as e:
        # Si Supabase lo rechaza, esto nos dirá por qué (ej. concurso repetido)
        return False, f"❌ Error de base de datos: {str(e)}"

# --- INTERFAZ DEL DASHBOARD ---
st.title("🎱 Optimizador Estadístico Melate")
st.markdown("Plataforma avanzada de análisis probabilístico.")

df_melate, cols_esferas = cargar_historico()

# --- NUEVO: Panel de Métricas (Estilo Dashboard Financiero) ---
if df_melate is not None:
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Sorteos Analizados", value=f"{len(df_melate):,}")
    m2.metric(label="Estado del Motor", value="Óptimo", delta="Activo")
    m3.metric(label="Nivel de Acceso", value=st.session_state['rol'])

st.divider()

if st.session_state['rol'] == 'Admin':
    tab_gen, tab_add, tab_stats = st.tabs(["🎯 Generador VIP", "➕ Admin: Sorteos", "📊 Análisis Estadístico"])
else:
    tab_gen, tab_stats = st.tabs(["🎯 Generador VIP", "📊 Análisis Estadístico"])
    tab_add = None 

with tab_gen:
    # --- NUEVO: Acordeón para explicaciones ---
    with st.expander("ℹ️ ¿Cómo funciona nuestro motor estadístico?"):
        st.write("""
        1. **Campana de Gauss:** Descartamos combinaciones con sumas extremas (muy altas o muy bajas).
        2. **Equilibrio Par/Impar:** Filtramos para mantener la proporción histórica de mayor probabilidad (ej. 3P-3I).
        3. **Dispersión:** Evitamos aglomeraciones de números consecutivos.
        4. **Blindaje Histórico:** Verificamos que la combinación no haya ganado antes el premio mayor.
        """)
        
    if df_melate is not None:
        if st.session_state['rol'] == 'Gratis':
            st.warning("⚠️ Modo Prueba: Limitado a 1 boleto. ¡Actualiza tu cuenta para liberar el poder del algoritmo!")
            max_boletos = 1
        else:
            max_boletos = 20
            
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.subheader("⚙️ Panel de Control")
            cantidad_boletos = st.number_input("Boletos a generar:", min_value=1, max_value=max_boletos, value=1)
            generar_btn = st.button("Generar Serie Optimizada", type="primary", use_container_width=True)
            
        with col2:
            st.subheader("🎟️ Tus Series Ganadoras")
            if generar_btn:
                with st.spinner('Procesando millones de combinaciones...'):
                    boletos, intentos = generar_boletos(cantidad_boletos, df_melate, cols_esferas)
                    
                    for i, boleto in enumerate(boletos, 1):
                        numeros_str = " - ".join([f"{n:02d}" for n in boleto])
                        
                        # --- NUEVO: Inyectando las tarjetas CSS ---
                        tarjeta_html = f"""
                        <div class="boleto-card">
                            <div class="boleto-titulo">Serie Élite #{i}</div>
                            <div class="boleto-numeros">{numeros_str}</div>
                        </div>
                        """
                        st.markdown(tarjeta_html, unsafe_allow_html=True)
                        
                    st.caption(f"🛡️ El motor descartó **{intentos - cantidad_boletos}** combinaciones débiles para entregarte esta serie.")

if tab_add is not None:
    with tab_add:
        st.subheader("Actualizar Base de Datos")
        with st.form("form_nuevo_sorteo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nuevo_concurso = c1.number_input("Número de Concurso", min_value=1, step=1)
            nueva_fecha = c2.date_input("Fecha del Sorteo", datetime.date.today())
            st.write("**Esferas (De menor a mayor)**")
            e1, e2, e3, e4, e5, e6 = st.columns(6)
            r1 = e1.number_input("R1", min_value=1, max_value=56, step=1)
            r2 = e2.number_input("R2", min_value=1, max_value=56, step=1)
            r3 = e3.number_input("R3", min_value=1, max_value=56, step=1)
            r4 = e4.number_input("R4", min_value=1, max_value=56, step=1)
            r5 = e5.number_input("R5", min_value=1, max_value=56, step=1)
            r6 = e6.number_input("R6", min_value=1, max_value=56, step=1)
            r7 = st.number_input("Esfera Adicional (R7)", min_value=1, max_value=56, step=1)
            btn_guardar = st.form_submit_button("Guardar en Histórico", type="primary")
            
            if btn_guardar:
                if not (r1 < r2 < r3 < r4 < r5 < r6):
                    st.error("Error: Las esferas deben ir de menor a mayor.")
                else:
                    exito, mensaje = guardar_nuevo_sorteo(nuevo_concurso, nueva_fecha, r1, r2, r3, r4, r5, r6, r7)
                    if exito: st.success(mensaje)
                    else: st.error(mensaje)

with tab_stats:
    if df_melate is not None and not df_melate.empty:
        st.subheader("🔥 Top 10 Números Más Calientes")
        todos_los_numeros = df_melate[cols_esferas].values.flatten()
        frecuencias = pd.Series(todos_los_numeros).value_counts().head(10)
        st.bar_chart(frecuencias)
