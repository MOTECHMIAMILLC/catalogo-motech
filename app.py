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

# Function to add visual stock indicators
def get_stock_indicator(qty):
    try:
        if pd.isna(qty): return "⚪ N/A"
        # Extract the number even if it has a '+' sign (like '50+')
        qty_str = str(qty).replace('+', '').strip()
        qty_num = int(qty_str)
        if qty_num >= 50: 
            return f"🟢 {qty}"
        elif qty_num >= 10: 
            return f"🟡 {qty}"
        else: 
            return f"🔴 {qty}"
    except:
        return f"⚪ {qty}"

excel_file = "PRICE LIST - MOTECH _Monday, October 12 📅✨.xlsx"
try:
    df = load_data(excel_file)
except FileNotFoundError:
    st.error(f"File not found:
