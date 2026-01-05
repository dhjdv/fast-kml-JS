import streamlit as st
import pdfplumber
import pandas as pd
import re
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="FAST-KML-JS // WHITE_LAB",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. WHITE FUTURISTIC CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');

    /* BASE STYLES */
    .stApp {
        background-color: #f8f9fb;
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,0) 0, hsla(253,16%,7%,0) 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,0) 0, hsla(225,39%,30%,0) 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,0) 0, hsla(339,49%,30%,0) 50%);
        background-attachment: fixed;
    }
    
    .stApp, .stMarkdown, .stTextInput, .stButton, .stSelectbox, .stRadio {
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #1a1c24;
        font-weight: 700;
        letter-spacing: -1px;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        box-shadow: 5px 0 15px rgba(0,0,0,0.03);
        border-right: none;
    }
    
    /* GRADIENT TEXT */
    .gradient-text {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    
    /* INPUTS */
    .stTextInput > div > div > input {
        border-radius: 12px;
        background-color: #f1f5f9;
        border: 1px solid transparent;
        color: #334155;
    }
    .stTextInput > div > div > input:focus {
        background-color: #ffffff;
        border: 1px solid #7c3aed;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
    }

    /* --- NAVIGATION BAR STYLING --- */
    
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #f0f2f6; 
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }

    /* Radio Button Group (The Tabs) */
    div[role="radiogroup"] {
        background: transparent;
        display: flex;
        gap: 10px;
        border: none;
        box-shadow: none;
        padding: 0;
    }
    
    div[role="radiogroup"] label {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 6px 20px;
        margin: 0 !important;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    
    div[role="radiogroup"] label:hover {
        border-color: #2563eb;
        color: #2563eb;
    }

    div[role="radiogroup"] label[data-checked="true"] {
        background: #2563eb !important;
        color: white !important;
        border-color: #2563eb !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
    }
    
    div[role="radiogroup"] label > div:first-child {
        display: none;
    }

    /* NEXT BUTTON */
    .stButton button {
        background-color: #1a1c24;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        border: none;
        font-weight: 600;
        transition: all 0.3s;
        height: 100%;
        margin-top: 0px;
    }
    .stButton button:hover {
        background-color: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    /* DATAFRAME */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def clean_cell_text(text):
    if not text: return ""
    text = str(text)
    text = text.replace("-\n", "-")
    text = re.sub(r'(?<=[\d.])\n\s*(?=[\d.])', '', text)
    text = text.replace("\n", " ")
    return text.strip()

def extract_data(pdf_file, use_lattice=True):
    all_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"} if use_lattice else {})
            except:
                tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2: continue
                headers = [clean_cell_text(h) for h in table[0]]
                
                if any(k in str(headers) for k in ["Latitude", "Distance", "Bearing", "Area From"]):
                    clean_headers = []
                    for h in headers:
                        h_lower = h.lower()
                        if "area from" in h_lower: clean_headers.append("Area From")
                        elif "area to" in h_lower: clean_headers.append("Area To")
                        elif "bearing" in h_lower: clean_headers.append("Bearing")
                        elif "distance" in h_lower: clean_headers.append("Distance")
                        elif "pillar" in h_lower: clean_headers.append("Pillar Type")
                        elif "latitude" in h_lower: clean_headers.append("Latitude")
                        elif "longitude" in h_lower: clean_headers.append("Longitude")
                        else: clean_headers.append(h)
                    
                    for row in table[1:]:
                        cleaned_row = [clean_cell_text(cell) for cell in row]
                        row_dict = {clean_headers[i]: val for i, val in enumerate(cleaned_row) if i < len(clean_headers)}
                        if any(row_dict.values()):
                            all_data.append(row_dict)
    return pd.DataFrame(all_data)

def parse_coordinate(coord_str):
    try:
        if not isinstance(coord_str, str) or not coord_str.strip(): return 0, 0, 0.0
        clean_str = coord_str.replace(" ", "")
        parts = clean_str.split('-')
        if len(parts) >= 3:
            d = int(parts[0])
            m = int(parts[1])
            s = float(re.sub(r'[^\d.]', '', parts[2]))
            return d, m, s
        return 0, 0, 0.0
    except:
        return 0, 0, 0.0

# --- 4. CALLBACKS & STATE ---

def sync_fields():
    # Get values from session state directly
    prefix = st.session_state.get('kml_prefix', "").upper()
    suffix = st.session_state.get('kml_suffix', "").upper()
    
    # LOGIC UPDATE:
    # 1. Full Code = Prefix + SPACE + Suffix (Space is fixed)
    # 2. Polygon = Prefix ONLY + " POLYGON"
    
    # Ensure there is a space in the final folder name if suffix exists
    if suffix:
        full_code = f"{prefix} {suffix}" 
    else:
        full_code = prefix

    st.session_state.folder_input = full_code
    st.session_state.poly_input = f"{prefix} POLYGON"

def next_phase():
    """Logic to move to the next tab"""
    current = st.session_state.get('nav_phase', "1. Data Repair")
    if current == "1. Data Repair":
        st.session_state['nav_phase'] = "2. Logic Verification"
    elif current == "2. Logic Verification":
        st.session_state['nav_phase'] = "3. Final Export"

# Initialize Navigation State
if 'nav_phase' not in st.session_state:
    st.session_state['nav_phase'] = "1. Data Repair"

# --- 5. SIDEBAR CONFIG ---
with st.sidebar:
    st.markdown("### 💠 CONFIGURATION")
    st.caption("PROJECT IDENTITY")
    
    # Split Project Code into two columns
    col_p1, col_p2 = st.columns([1.5, 1])
    with col_p1:
        # First Box: Prefix (Used for Polygon Label)
        kml_prefix = st.text_input("Prefix", value="ML NO.", key="kml_prefix", on_change=sync_fields)
    with col_p2:
        # Second Box: Village/District (Fixed space prefix logic handled in sync_fields)
        kml_suffix = st.text_input("Village/District", value="", key="kml_suffix", on_change=sync_fields)
    
    # Initialize session state for slave fields if missing
    if 'folder_input' not in st.session_state: st.session_state.folder_input = "ML NO."
    if 'poly_input' not in st.session_state: st.session_state.poly_input = "ML NO. POLYGON"
        
    folder_val = st.text_input("Folder Name", key="folder_input")
    poly_val = st.text_input("Polygon Label", key="poly_input")
    
    # Determine Final Values for processing
    # The space is added here for the final variable used in the dataframe
    final_prefix = kml_prefix.upper()
    final_suffix = kml_suffix.upper()
    
    if final_suffix:
        final_kml = f"{final_prefix} {final_suffix}" # Force the space here
    else:
        final_kml = final_prefix
        
    final_folder = folder_val.upper()
    final_poly = poly_val.upper()
    
    st.divider()
    st.caption("EXTRACTION ENGINE")
    use_lattice = st.toggle("Lattice Mode (Grid)", value=True)
    
    st.markdown("""
        <div style="margin-top: 50px; padding: 15px; background: #f1f5f9; border-radius: 10px; font-size: 0.8rem; color: #64748b;">
        <strong>System Status:</strong><br>
        Ready for ingestion.<br>
        v2.5 Lab Build
        </div>
    """, unsafe_allow_html=True)

# --- 6. MAIN CONTENT ---

st.markdown(f"""
    <div style="margin-bottom: 30px;">
        <h1 style="font-size: 3rem; margin-bottom: 0;">fast-kml<span class="gradient-text">.JS</span></h1>
        <p style="color: #64748b; font-size: 1.1rem;">Advanced Mining Report Digitization System</p>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload PDF Report", type=["pdf"], label_visibility="collapsed")

if not uploaded_file:
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 60px;">
            <div style="font-size: 4rem; margin-bottom: 20px;">📂</div>
            <h3 style="color: #334155;">Awaiting Document</h3>
            <p style="color: #94a3b8; max-width: 400px; margin: 0 auto;">
                Drag and drop your Jan Soochna Mining Report PDF here to initiate the coordinate extraction sequence.
            </p>
        </div>
    """, unsafe_allow_html=True)

else:
    # --- PROCESSING ---
    if 'raw_df' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        with st.spinner("Processing data stream..."):
            time.sleep(0.5)
            df = extract_data(uploaded_file, use_lattice)
            st.session_state['raw_df'] = df
            st.session_state['last_file'] = uploaded_file.name
            st.session_state['nav_phase'] = "1. Data Repair"
        
        if not df.empty:
            st.markdown(f"""
            <div style="padding: 15px; border: 1px solid #4ade80; background: #f0fdf4; border-radius: 12px; margin-bottom: 20px; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem; margin-right: 15px;">✅</div>
                <div>
                    <strong style="color: #166534;">Scan Complete</strong><br>
                    <span style="font-size: 0.9rem; color: #15803d;">Successfully extracted {len(df)} coordinate points.</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if st.session_state['raw_df'].empty:
        st.error("No data detected. Please enable 'Lattice Mode' in the sidebar.")
    else:
        raw_df = st.session_state['raw_df']
        
        # --- NAVIGATION PANEL ---
        st.write("")
        with st.container(border=True):
            col_nav, col_action = st.columns([5, 1])
            with col_nav:
                st.radio(
                    "Navigation", 
                    ["1. Data Repair", "2. Logic Verification", "3. Final Export"], 
                    horizontal=True,
                    label_visibility="collapsed",
                    key="nav_phase" 
                )
            with col_action:
                if st.session_state['nav_phase'] != "3. Final Export":
                    st.button("Next ➡", on_click=next_phase, use_container_width=True)
            
        st.write("") 

        # --- VIEW 1: DATA CLEANING ---
        if st.session_state['nav_phase'] == "1. Data Repair":
            st.markdown("**Data Repair Interface**")
            st.caption("Review the grid below. Correct any text artifacts (e.g. split numbers) before processing.")
            
            c1, c2 = st.columns([3,1])
            with c2:
                cols_to_drop = st.multiselect("Hide Columns", raw_df.columns, key="drop_raw")
            
            display_df = raw_df.drop(columns=cols_to_drop)
            edited_raw_df = st.data_editor(display_df, num_rows="dynamic", use_container_width=True, height=400, key="editor_main")
            
            st.session_state['edited_df'] = edited_raw_df
            
            avail_cols = edited_raw_df.columns.tolist()
            default_idx = 0
            for p in ["Area To", "Area From", "Pillar Type"]:
                if p in avail_cols:
                    default_idx = avail_cols.index(p)
                    break
            
            st.write("")
            name_col = st.selectbox("Select Point Name Column", avail_cols, index=default_idx)
            st.session_state['name_col'] = name_col

        # --- PREPARE DATA ---
        if 'edited_df' in st.session_state:
            process_df = st.session_state['edited_df']
            name_col = st.session_state.get('name_col', process_df.columns[0])
        else:
            process_df = raw_df
            name_col = raw_df.columns[0]

        final_rows = []
        comparison_rows = []
        avail_cols = process_df.columns.tolist()

        for i, (_, row) in enumerate(process_df.iterrows()):
            raw_lat = row.get("Latitude", "") if "Latitude" in avail_cols else ""
            raw_lng = row.get("Longitude", "") if "Longitude" in avail_cols else ""
            ld, lm, ls = parse_coordinate(raw_lat)
            lgd, lgm, lgs = parse_coordinate(raw_lng)
            name = row.get(name_col, "")
            
            # Use the calculated final values
            if i == 0:
                r_kml, r_poly, r_fold = final_kml, final_poly, final_folder
            else:
                r_kml, r_poly, r_fold = "", "", ""

            final_rows.append({
                'name': name,
                'lat_deg': ld, 'lat_min': lm, 'lat_sec': ls, 'lat_dir': 'N',
                'lng_deg': lgd, 'lng_min': lgm, 'lng_sec': lgs, 'lng_dir': 'E',
                'kml_name': r_kml, 'poly_name': r_poly, 'folder_name': r_fold  
            })
            
            comparison_rows.append({
                'Point': name, 'Raw Latitude': raw_lat, '➜ Lat': f"{ld}° {lm}' {ls}\"",
                'Raw Longitude': raw_lng, '➜ Lng': f"{lgd}° {lgm}' {lgs}\""
            })

        final_df = pd.DataFrame(final_rows)
        compare_df = pd.DataFrame(comparison_rows)

        # --- VIEW 2: VERIFICATION ---
        if st.session_state['nav_phase'] == "2. Logic Verification":
            st.markdown("**Logic Verification**")
            def highlight_errors(val):
                return 'background-color: #fef2f2; color: #dc2626; font-weight: bold;' if "0° 0' 0.0" in str(val) else ''
            st.dataframe(compare_df.style.map(highlight_errors, subset=['➜ Lat', '➜ Lng']), use_container_width=True, height=500)
            
        # --- VIEW 3: EXPORT ---
        if st.session_state['nav_phase'] == "3. Final Export":
            st.markdown("**Final Export**")
            
            col_ex1, col_ex2 = st.columns([1, 1])
            with col_ex1:
                st.markdown(f"""
                <div style="padding: 15px; border-left: 4px solid #2563eb; background: #eff6ff; border-radius: 0 10px 10px 0;">
                    <h4 style="margin:0; color: #1e40af;">Ready to Download</h4>
                    <p style="margin:0; font-size: 0.9rem; color: #60a5fa;">File ID: <strong>{final_kml}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_ex2:
                final_cols_drop = st.multiselect("Exclude Output Columns", final_df.columns, key="drop_final")

            final_df_clean = final_df.drop(columns=final_cols_drop)
            
            # --- AUTO MIN SIZE ---
            st.dataframe(
                final_df_clean, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    col: st.column_config.Column(width=None) for col in final_df_clean.columns
                }
            )
            
            csv = final_df_clean.to_csv(index=False).encode('utf-8')
            st.write("")
            st.download_button(
                label="📥 Download CSV File",
                data=csv,
                file_name=f"{final_kml}_COORDS.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )