import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. APP CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="fast-kml-JS", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a beautiful header
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #4A90E2;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 20px;
    }
    .highlight {
        color: #E24A4A;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---

def clean_cell_text(text):
    """Heals broken text and numbers split across lines."""
    if not text: return ""
    text = str(text)
    # Heal "26-31-\n 8.3" -> "26-31-8.3"
    text = text.replace("-\n", "-")
    # Heal "59.9\n 00" -> "59.900" (Split numbers)
    text = re.sub(r'(?<=[\d.])\n\s*(?=[\d.])', '', text)
    # Remove remaining newlines
    text = text.replace("\n", " ")
    return text.strip()

def extract_data(pdf_file, use_lattice=True):
    """Extracts tables from PDF."""
    all_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            try:
                # Lattice is default (better for grids), fallback to stream
                flavor = "lattice" if use_lattice else "stream"
                tables = page.extract_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"} if use_lattice else {})
            except:
                tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2: continue
                
                # Normalize headers
                headers = [clean_cell_text(h) for h in table[0]]
                
                # Identify Mining Table Keywords
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
                        # Map values to headers
                        row_dict = {clean_headers[i]: val for i, val in enumerate(cleaned_row) if i < len(clean_headers)}
                        if any(row_dict.values()):
                            all_data.append(row_dict)
    return pd.DataFrame(all_data)

def parse_coordinate(coord_str):
    """Robustly parses coordinates into D-M-S."""
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

# --- 3. AUTO-SYNC LOGIC ---
def sync_names():
    """
    Callback: When KML Name changes, auto-update Folder and Polygon names.
    Folder = KML Name
    Polygon = KML Name + " POLYGON" (Space, no underscore)
    """
    if st.session_state.kml_input:
        base_name = st.session_state.kml_input.upper()
        st.session_state.folder_input = base_name
        st.session_state.poly_input = f"{base_name} POLYGON"

# --- 4. SIDEBAR UI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=60)
    st.title("fast-kml-JS")
    st.caption("Jan Soochna Mining Report Tool")
    
    st.divider()
    
    # FILE UPLOAD
    uploaded_file = st.file_uploader("📂 Upload PDF Report", type=["pdf"])
    
    st.divider()
    st.subheader("⚙️ Project Details")
    
    # INPUTS WITH SYNC LOGIC
    # 1. KML Name (Master)
    kml_val = st.text_input(
        "KML Name (Master)", 
        value="MY_MINE", 
        key="kml_input", 
        on_change=sync_names,
        help="Type here to auto-fill Folder and Polygon names."
    )
    
    # 2. Folder Name (Slave)
    folder_val = st.text_input("Folder Name", value="MY_MINE", key="folder_input")
    
    # 3. Polygon Name (Slave + Space Suffix)
    poly_val = st.text_input("Polygon Name", value="MY_MINE POLYGON", key="poly_input")
    
    # Ensure Uppercase for output
    kml_final = kml_val.upper()
    folder_final = folder_val.upper()
    poly_final = poly_val.upper()
    
    st.divider()
    with st.expander("🔧 Advanced Settings"):
        use_lattice = st.toggle("Grid Extraction Mode", value=True, help="Best for tables with visible lines.")

# --- 5. MAIN APP INTERFACE ---

# Header
st.markdown('<p class="main-header">🚀 fast-kml-JS</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Convert Jan Soochna Portal PDFs to Survey CSVs in seconds.</p>', unsafe_allow_html=True)

if uploaded_file:
    # --- PROCESSING ---
    if 'raw_df' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        with st.spinner("⚡ Extracting and repairing data..."):
            df = extract_data(uploaded_file, use_lattice)
            st.session_state['raw_df'] = df
            st.session_state['last_file'] = uploaded_file.name

    if st.session_state['raw_df'].empty:
        st.error("❌ No data found. Try opening the 'Advanced Settings' in the sidebar and toggling Extraction Mode.")
    else:
        # --- TABS LAYOUT ---
        tab1, tab2, tab3 = st.tabs(["1️⃣ Clean Data", "2️⃣ Verify Logic", "3️⃣ Export CSV"])

        # TAB 1: EDIT RAW
        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("👇 **Edit Raw Text:** Fix any numbers that look broken (e.g., '26-\n31').")
            with col2:
                raw_df = st.session_state['raw_df']
                cols_to_drop = st.multiselect("Hide Columns", raw_df.columns, key="drop_raw")
            
            display_df = raw_df.drop(columns=cols_to_drop)
            
            # FIX 1: Replaced use_container_width with width='stretch'
            edited_raw_df = st.data_editor(
                display_df, 
                num_rows="dynamic", 
                width="stretch", 
                key="raw_editor", 
                height=400
            )
            
            # Smart Column Detection
            avail_cols = edited_raw_df.columns.tolist()
            default_idx = 0
            for priority in ["Area To", "Area From", "Pillar Type"]:
                if priority in avail_cols:
                    default_idx = avail_cols.index(priority)
                    break
            
            st.write("---")
            name_col = st.selectbox("📌 Select the Column containing Point Names:", avail_cols, index=default_idx)

        # --- DATA PROCESSING LOOP ---
        final_rows = []
        comparison_rows = []

        for i, (_, row) in enumerate(edited_raw_df.iterrows()):
            # Parse
            raw_lat = row.get("Latitude", "") if "Latitude" in avail_cols else ""
            raw_lng = row.get("Longitude", "") if "Longitude" in avail_cols else ""
            ld, lm, ls = parse_coordinate(raw_lat)
            lgd, lgm, lgs = parse_coordinate(raw_lng)
            name = row.get(name_col, "")
            
            # Apply Naming Logic (First Row Only)
            if i == 0:
                r_kml, r_poly, r_fold = kml_final, poly_final, folder_final
            else:
                r_kml, r_poly, r_fold = "", "", ""

            # Build Row
            final_rows.append({
                'name': name,
                'lat_deg': ld, 'lat_min': lm, 'lat_sec': ls, 'lat_dir': 'N',
                'lng_deg': lgd, 'lng_min': lgm, 'lng_sec': lgs, 'lng_dir': 'E',
                'kml_name': r_kml,       
                'poly_name': r_poly,     
                'folder_name': r_fold  
            })
            
            # Build Comparison
            comparison_rows.append({
                'Point': name,
                'Raw Latitude': raw_lat,
                '➜ Lat': f"{ld}° {lm}' {ls}\"",
                'Raw Longitude': raw_lng,
                '➜ Lng': f"{lgd}° {lgm}' {lgs}\""
            })

        final_df = pd.DataFrame(final_rows)
        compare_df = pd.DataFrame(comparison_rows)

        # TAB 2: VERIFY
        with tab2:
            st.warning("👀 **Verification:** Check side-by-side if the Raw Text became the Correct Coordinate.")
            
            # Highlight invalid zeros
            def highlight_errors(val):
                return 'background-color: #ffcccc' if "0° 0' 0.0" in str(val) else ''
            
            # FIX 2: Replaced use_container_width with width='stretch'
            # FIX 3: Replaced .applymap() with .map()
            st.dataframe(
                compare_df.style.map(highlight_errors, subset=['➜ Lat', '➜ Lng']), 
                width="stretch", 
                height=500
            )

        # TAB 3: EXPORT
        with tab3:
            st.success("✅ **Ready!** Your data is formatted and ready for the KML tool.")
            
            # Final clean up
            final_cols_drop = st.multiselect("Exclude Columns from Output", final_df.columns, key="drop_final")
            final_df_clean = final_df.drop(columns=final_cols_drop)
            
            # FIX 4: Replaced use_container_width with width='stretch'
            st.dataframe(final_df_clean, width="stretch")
            
            csv = final_df_clean.to_csv(index=False).encode('utf-8')
            
            # FIX 5: Removed use_container_width (not valid for buttons in this context usually, or implied default)
            st.download_button(
                label="📥 Download Final CSV",
                data=csv,
                file_name=f"{kml_final}_COORDS.csv",
                mime="text/csv",
                type="primary"
            )

else:
    # Empty State (Welcome Screen)
    st.info("👈 **Start here:** Upload your PDF report from the sidebar.")
    st.markdown("""
    ### How to use:
    1. **Upload** the Jan Soochna Mining Report.
    2. **Name It** in the sidebar (Type 'MyMine' → Auto-fills Folder & Polygon).
    3. **Download** the cleaned CSV.
    """)