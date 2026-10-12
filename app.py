import streamlit as st
import pandas as pd
import re

# Configuración de la página
st.set_page_config(page_title="Catálogo Motech Miami", layout="wide", page_icon="💻")

# Ocultar marca de agua de Streamlit
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos(ruta_archivo):
    xls = pd.ExcelFile(ruta_archivo)
    datos_completos = []
    
    for hoja in xls.sheet_names:
        # El encabezado real de tu Excel está en la fila 1 (índice 1)
        df = pd.read_excel(ruta_archivo, sheet_name=hoja, header=1)
        df = df.dropna(subset=['MODEL AND DESCRIPTION'])
        df['Categoría General'] = hoja
        datos_completos.append(df)
        
    df_final = pd.concat(datos_completos, ignore_index=True)
    
    def extraer_specs(fila):
        desc = str(fila['MODEL AND DESCRIPTION']).upper()
        
        # Procesador
        cpu = "Otro"
        if "CORE I3" in desc: cpu = "Intel Core i3"
        elif "CORE I5" in desc: cpu = "Intel Core i5"
        elif "CORE I7" in desc: cpu = "Intel Core i7"
        elif "CORE I9" in desc: cpu = "Intel Core i9"
        elif "CORE ULTRA" in desc: cpu = "Intel Core Ultra"
        elif "RYZEN 3" in desc: cpu = "AMD Ryzen 3"
        elif "RYZEN 5" in desc: cpu = "AMD Ryzen 5"
        elif "RYZEN 7" in desc: cpu = "AMD Ryzen 7"
        elif "RYZEN 9" in desc: cpu = "AMD Ryzen 9"
        elif "APPLE M" in desc: cpu = "Apple Silicon"
        
        # RAM
        ram_match = re.search(r'(\d+)\s*GB(?:\s*RAM)?', desc)
        ram = f"{ram_match.group(1)}GB" if ram_match else "N/A"
        
        # Almacenamiento
        disco_match = re.search(r'(\d+)\s*(?:GB|TB)\s*(?:SSD|HDD|NVME)', desc)
        disco = disco_match.group(0) if disco_match else "N/A"
        
        # Pantalla
        pantalla_match = re.search(r'(\d{2}(?:\.\d)?)\s*(?:"|”|-INCH|INCH|’)', desc)
        pantalla = f"{pantalla_match.group(1)}\"" if pantalla_match else "N/A"
        
        return pd.Series([cpu, ram, disco, pantalla])

    df_final[['Procesador', 'RAM', 'Almacenamiento', 'Pantalla']] = df_final.apply(extraer_specs, axis=1)
    return df_final

archivo_excel = "PRICE LIST - MOTECH _Monday, October 12 📅✨.xlsx"
try:
    df = cargar_datos(archivo_excel)
except FileNotFoundError:
    st.error(f"Archivo no encontrado: {archivo_excel}")
    st.stop()

st.title("📦 Catálogo Mayorista - Motech Miami")

st.sidebar.header("🔍 Filtros Dinámicos")
lista_categorias = ["Ver Todo"] + list(df['Categoría General'].unique())
cat_seleccionada = st.sidebar.selectbox("Seleccionar Categoría", lista_categorias)

if cat_seleccionada != "Ver Todo":
    df_filtrado = df[df['Categoría General'] == cat_seleccionada]
else:
    df_filtrado = df.copy()

if cat_seleccionada in ["LAPTOPS ", "GAMING", "DESKTOP", "Ver Todo"]:
    marcas = st.sidebar.multiselect("Marca", df_filtrado['BRAND'].dropna().unique())
    if marcas: df_filtrado = df_filtrado[df_filtrado['BRAND'].isin(marcas)]
        
    cpus = st.sidebar.multiselect("Procesador", df_filtrado['Procesador'].unique())
    if cpus: df_filtrado = df_filtrado[df_filtrado['Procesador'].isin(cpus)]
        
    rams = st.sidebar.multiselect("Memoria RAM", df_filtrado['RAM'].unique())
    if rams: df_filtrado = df_filtrado[df_filtrado['RAM'].isin(rams)]
        
    discos = st.sidebar.multiselect("Almacenamiento", df_filtrado['Almacenamiento'].unique())
    if discos: df_filtrado = df_filtrado[df_filtrado['Almacenamiento'].isin(discos)]
        
    pantallas = st.sidebar.multiselect("Pantalla", df_filtrado['Pantalla'].unique())
    if pantallas: df_filtrado = df_filtrado[df_filtrado['Pantalla'].isin(pantallas)]

texto_busqueda = st.text_input("Buscar por modelo, marca o especificación...", "")
if texto_busqueda:
    df_filtrado = df_filtrado[df_filtrado['MODEL AND DESCRIPTION'].astype(str).str.contains(texto_busqueda, case=False, na=False)]

st.markdown(f"*Mostrando {len(df_filtrado)} productos disponibles*")

columnas_visibles = ['BRAND', 'MODEL AND DESCRIPTION', 'Procesador', 'RAM', 'Almacenamiento', 'Pantalla', 'PRICE', 'QTY', 'CONDITION']
df_mostrar = df_filtrado[columnas_visibles].copy()
df_mostrar['PRICE'] = df_mostrar['PRICE'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
