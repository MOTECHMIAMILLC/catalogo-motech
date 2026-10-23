import streamlit as st
import pandas as pd
import re

# Page configuration
st.set_page_config(page_title="Motech Miami Catalog", layout="wide", page_icon="💻")

# Hide Streamlit watermark and padding for better iframe integration
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    all_data = []
    
    for sheet in xls.sheet_names:
        df_raw = pd.read_excel(file_path, sheet_name=sheet)
        if df_raw.empty:
            continue
            
        # 1. Detectar automáticamente en qué fila se encuentran las cabeceras
        header_row = None
        for r_idx in range(min(10, len(df_raw))):
            row_str = " ".join([str(v).upper() for v in df_raw.iloc[r_idx].values if pd.notna(v)])
            if any(k in row_str for k in ['MODEL', 'DESCRIPTION', 'ITEM', 'BRAND', 'PRICE']):
                header_row = r_idx
                break
                
        # 2. Ajustar las columnas según la fila de cabecera encontrada
        if header_row is not None:
            df = df_raw.iloc[header_row + 1:].copy()
            df.columns = [str(c).strip() for c in df_raw.iloc[header_row].values]
        else:
            df = df_raw.copy()
            df.columns = [str(c).strip() for c in df.columns]

        # 3. Encontrar la columna de modelo y descripción (sin importar espacios extra)
        col_desc = next(
            (c for c in df.columns if any(k in str(c).upper() for k in ['MODEL AND DESCRIPTION', 'DESCRIPTION', 'MODEL', 'ITEM'])), 
            None
        )
        
        if col_desc:
            df = df.dropna(subset=[col_desc])
            df = df.rename(columns={col_desc: 'MODEL AND DESCRIPTION'})
            df['Main Category'] = sheet
            all_data.append(df)
        
    if not all_data:
        st.error("No se encontraron datos de productos en el archivo Excel.")
        st.stop()
        
    df_final = pd.concat(all_data, ignore_index=True)
    
    # Estandarizar nombre de columnas principales si tienen ligeras variaciones
    cols_rename = {}
    for c in df_final.columns:
        cu = str(c).upper().strip()
        if cu == 'BRAND': cols_rename[c] = 'BRAND'
        elif cu == 'ITEM': cols_rename[c] = 'ITEM'
        elif cu == 'PRICE': cols_rename[c] = 'PRICE'
        elif cu == 'QTY': cols_rename[c] = 'QTY'
        elif cu == 'MOQ': cols_rename[c] = 'MOQ'
        elif cu == 'ETA': cols_rename[c] = 'ETA'
        elif cu == 'CONDITION': cols_rename[c] = 'CONDITION'
    df_final = df_final.rename(columns=cols_rename)
    
    # Eliminar columnas duplicadas si existen en el origen
    df_final = df_final.loc[:, ~df_final.columns.duplicated()]

    # Asegurarnos de que MOQ y ETA existan en el dataframe
    if 'MOQ' not in df_final.columns:
        df_final['MOQ'] = "1"
    if 'ETA' not in df_final.columns:
        df_final['ETA'] = "In Stock"
    if 'CONDITION' not in df_final.columns:
        df_final['CONDITION'] = "NEW"

    def extract_specs(row):
        desc = str(row['MODEL AND DESCRIPTION']).upper()
        
        cpu = "Other"
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
        
        ram_match = re.search(r'(\d+)\s*GB(?:\s*RAM)?', desc)
        ram = f"{ram_match.group(1)}GB" if ram_match else "N/A"
        
        storage_match = re.search(r'(\d+)\s*(?:GB|TB)\s*(?:SSD|HDD|NVME)', desc)
        storage = storage_match.group(0) if storage_match else "N/A"
        
        screen_match = re.search(r'(\d{2}(?:\.\d)?)\s*(?:"|”|-INCH|INCH|’)', desc)
        screen = f"{screen_match.group(1)}\"" if screen_match else "N/A"
        
        return pd.Series([cpu, ram, storage, screen])

    # Se mantienen estas columnas internamente para los filtros avanzados
    df_final[['Processor', 'RAM', 'Storage', 'Screen Size']] = df_final.apply(extract_specs, axis=1)
    return df_final

def get_stock_indicator(qty):
    try:
        if pd.isna(qty): return "⚪ N/A"
        qty_str = str(qty).replace('+', '').strip()
        qty_num = int(qty_str)
        if qty_num >= 50: return f"🟢 {qty} in stock"
        elif qty_num >= 10: return f"🟡 {qty} in stock"
        else: return f"🔴 {qty} in stock"
    except:
        return f"⚪ {qty}"

# --- VENTANA EMERGENTE (DIALOG) ---
@st.dialog("Product Details")
def show_product_details(row, price_display):
    # Título principal
    st.markdown(f"#### {row['MODEL AND DESCRIPTION']}")
    
    # Precio destacado
    st.markdown(f"<h2 style='color: #2e7d32;'>{price_display}</h2>", unsafe_allow_html=True)
    
    # Indicadores de stock, MOQ, ETA y condición
    st.markdown(f"**Stock:** {row['QTY']} &nbsp; • &nbsp; **MOQ:** {row.get('MOQ', 'N/A')} &nbsp; • &nbsp; **ETA:** {row.get('ETA', 'N/A')} &nbsp; • &nbsp; **Condition:** {row.get('CONDITION', 'NEW')}")
    
    st.divider()
    
    # Detalles estructurados con 2 columnas
    col_label, col_value = st.columns([1, 2])
    
    with col_label:
        st.write("**Brand**")
        st.write("**SKU / Item**")
        st.write("**Processor**")
        st.write("**RAM Memory**")
        st.write("**Storage**")
        st.write("**Screen Size**")
        
    with col_value:
        st.write(str(row.get('BRAND', 'N/A')))
        st.code(str(row.get('ITEM', 'N/A')), language=None)
        st.write(str(row.get('Processor', 'N/A')))
        st.write(str(row.get('RAM', 'N/A')))
        st.write(str(row.get('Storage', 'N/A')))
        st.write(str(row.get('Screen Size', 'N/A')))

# --- CARGA DE DATOS ---
excel_file = "PRICE LIST - MOTECH MIAMI.xlsx"
try:
    df = load_data(excel_file)
except FileNotFoundError:
    st.error(f"File not found: {excel_file}")
    st.stop()

# --- CABECERA Y CONTRASEÑA DESTACADA ---
col_title, col_auth = st.columns([1.5, 1.5], vertical_alignment="center")

with col_title:
    st.title("📦 Wholesale Catalog - Motech Miami")

with col_auth:
    WHOLESALE_PASSWORD = "MOTECHB2B"
    
    st.markdown("""
        <style>
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: 1px solid rgba(168, 85, 247, 0.7) !important;
                background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(13, 12, 19, 0.85) 100%) !important;
                border-radius: 14px !important;
                padding: 12px 18px !important;
                box-shadow: 0 0 18px rgba(168, 85, 247, 0.3) !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<div style='color: #c084fc; font-weight: 800; font-size: 13px; letter-spacing: 1px; margin-bottom: 4px;'>🔑 B2B WHOLESALE ACCESS</div>", unsafe_allow_html=True)
        user_password = st.text_input(
            "Enter Wholesale Code to view pricing:", 
            type="password",
            placeholder="Enter access code here...",
            label_visibility="visible"
        )

# --- FILTROS ---
st.markdown("### 🔍 Search & Filters")
col1, col2 = st.columns(2)
with col1:
    category_list = ["View All"] + list(df['Main Category'].unique())
    selected_category = st.selectbox("Select Category", category_list)

if selected_category != "View All":
    filtered_df = df[df['Main Category'] == selected_category]
else:
    filtered_df = df.copy()
    
with col2:
    search_text = st.text_input("Search by Item/SKU, model, brand, or specification...", "")
    if search_text:
        filtered_df = filtered_df[
            filtered_df['ITEM'].astype(str).str.contains(search_text, case=False, na=False) |
            filtered_df['MODEL AND DESCRIPTION'].astype(str).str.contains(search_text, case=False, na=False) |
            filtered_df['BRAND'].astype(str).str.contains(search_text, case=False, na=False)
        ]

if selected_category in ["LAPTOPS ", "GAMING", "DESKTOP", "View All"]:
    with st.expander("🛠️ Advanced Specifications Filters", expanded=True):
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        with col_a:
            brands = st.multiselect("Brand", filtered_df['BRAND'].dropna().unique())
            if brands: filtered_df = filtered_df[filtered_df['BRAND'].isin(brands)]
        with col_b:
            cpus = st.multiselect("Processor", filtered_df['Processor'].unique())
            if cpus: filtered_df = filtered_df[filtered_df['Processor'].isin(cpus)]
        with col_c:
            rams = st.multiselect("RAM", filtered_df['RAM'].unique())
            if rams: filtered_df = filtered_df[filtered_df['RAM'].isin(rams)]
        with col_d:
            storages = st.multiselect("Storage", filtered_df['Storage'].unique())
            if storages: filtered_df = filtered_df[filtered_df['Storage'].isin(storages)]
        with col_e:
            screens = st.multiselect("Screen Size", filtered_df['Screen Size'].unique())
            if screens: filtered_df = filtered_df[filtered_df['Screen Size'].isin(screens)]

# --- PREPARAR TABLA ---
st.markdown(f"**Showing {len(filtered_df)} available products.** 👆 *Click on any Model and Description to view full details and SKU.*")

visible_columns = ['BRAND', 'ITEM', 'MODEL AND DESCRIPTION', 'QTY', 'MOQ', 'ETA', 'PRICE', 'CONDITION']

# Filtrar solo columnas existentes y asegurar que NO existan duplicadas
available_visible_cols = []
for col in visible_columns:
    if col in filtered_df.columns and col not in available_visible_cols:
        available_visible_cols.append(col)

display_df = filtered_df[available_visible_cols].copy()
display_df = display_df.loc[:, ~display_df.columns.duplicated()]

if 'QTY' in display_df.columns:
    display_df['QTY'] = display_df['QTY'].apply(get_stock_indicator)

if user_password == WHOLESALE_PASSWORD:
    if 'PRICE' in display_df.columns:
        display_df['PRICE'] = display_df['PRICE'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
else:
    if 'PRICE' in display_df.columns:
        display_df['PRICE'] = "🔒 Hidden"

# Mostrar la tabla permitiendo selección (on_select)
event = st.dataframe(
    display_df, 
    use_container_width=True, 
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    height=800
)

# Si el usuario hace clic en una fila, abrimos la ventana emergente con los detalles
if len(event.selection.rows) > 0:
    selected_index = event.selection.rows[0]
    selected_row = filtered_df.iloc[selected_index]
    
    price_val = display_df.iloc[selected_index]['PRICE'] if 'PRICE' in display_df.columns else "🔒 Hidden"
    show_product_details(selected_row, price_val)
