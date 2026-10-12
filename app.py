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
        # Header is on row 1 (index 1)
        df = pd.read_excel(file_path, sheet_name=sheet, header=1)
        df = df.dropna(subset=['MODEL AND DESCRIPTION'])
        df['Main Category'] = sheet
        all_data.append(df)
        
    df_final = pd.concat(all_data, ignore_index=True)
    
    def extract_specs(row):
        desc = str(row['MODEL AND DESCRIPTION']).upper()
        
        # Processor
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
        
        # RAM
        ram_match = re.search(r'(\d+)\s*GB(?:\s*RAM)?', desc)
        ram = f"{ram_match.group(1)}GB" if ram_match else "N/A"
        
        # Storage
        storage_match = re.search(r'(\d+)\s*(?:GB|TB)\s*(?:SSD|HDD|NVME)', desc)
        storage = storage_match.group(0) if storage_match else "N/A"
        
        # Screen Size
        screen_match = re.search(r'(\d{2}(?:\.\d)?)\s*(?:"|”|-INCH|INCH|’)', desc)
        screen = f"{screen_match.group(1)}\"" if screen_match else "N/A"
        
        return pd.Series([cpu, ram, storage, screen])

    df_final[['Processor', 'RAM', 'Storage', 'Screen Size']] = df_final.apply(extract_specs, axis=1)
    return df_final

excel_file = "PRICE LIST - MOTECH _Monday, October 12 📅✨.xlsx"
try:
    df = load_data(excel_file)
except FileNotFoundError:
    st.error(f"File not found: {excel_file}")
    st.stop()

st.title("📦 Wholesale Catalog - Motech Miami")

# --- MAIN PAGE FILTERS ---
st.markdown("### 🔍 Search & Filters")

# First row: Category and General Search
col1, col2 = st.columns(2)
with col1:
    category_list = ["View All"] + list(df['Main Category'].unique())
    selected_category = st.selectbox("Select Category", category_list)

if selected_category != "View All":
    filtered_df = df[df['Main Category'] == selected_category]
else:
    filtered_df = df.copy()
    
with col2:
    search_text = st.text_input("Search by model, brand, or specification...", "")
    if search_text:
        filtered_df = filtered_df[filtered_df['MODEL AND DESCRIPTION'].astype(str).str.contains(search_text, case=False, na=False)]

# Second row: Advanced Filters (Only for tech categories)
if selected_category in ["LAPTOPS ", "GAMING", "DESKTOP", "View All"]:
    with st.expander("🛠️ Advanced Specifications Filters", expanded=True):
        # We create 5 columns for the specific hardware filters
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
            screens = st.multiselect("Screen Size", filtered_df['Screen Size'].
