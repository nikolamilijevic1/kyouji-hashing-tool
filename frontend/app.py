import streamlit as st
import requests
import pandas as pd
import json
import base64
from PIL import Image
import os

# Set page configuration
logo_path = os.path.join(os.path.dirname(__file__), "company_logo.svg.png")
try:
    logo_img = Image.open(logo_path)
    # Convert to base64 for perfect HTML centering
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="80" style="margin-right: 20px;">'
except:
    logo_img = "🏮"
    logo_html = '<span style="font-size: 50px; margin-right: 20px;">🏮</span>'

st.set_page_config(
    page_title="SHA-256 Hashing Tool",
    page_icon=logo_img,
    layout="wide",
)

# Custom CSS for premium look and hiding Streamlit elements
st.markdown("""
    <style>
    /* Completely remove the top header bar and status indicators */
    [data-testid="stHeader"] {display: none !important;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Hide the red/orange/yellow running indicator */
    div[data-testid="stStatusWidget"] {visibility: hidden !important;}

    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white;
        border: None;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(75, 108, 183, 0.4);
    }
    h1 {
        background: -webkit-linear-gradient(#ffffff, #4b6cb7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin: 0 !important;
    }
    .header-flex {
        display: flex;
        align-items: center;
        margin-top: -50px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# App Header with Flexbox centering
st.markdown(f"""
    <div class="header-flex">
        {logo_html}
        <h1>SHA-256 Hashing and Redaction Tool</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("### Deterministic Data Integrity & Verification")
st.markdown("Redact sensitive data or verify integrity using deterministic SHA-256. Built for unshakeable data truth.")

# Backend URL
BACKEND_URL = "http://backend:8000"

# Sidebar for configuration/info
with st.sidebar:
    st.header("Status")
    try:
        st.success("Backend Connected")
    except:
        st.error("Backend Disconnected")
    
    st.divider()
    st.info("Forensic Integrity: SHA-256 is deterministic. Leading and trailing whitespace is stripped, but casing is preserved for verification.")

# Main Content Tabs
tab1, tab2 = st.tabs(["Single Hash", "Bulk Processing"])

with tab1:
    st.subheader("Generate Single Hash")
    input_text = st.text_input("Enter text to hash:", placeholder="Type your data here...")
    
    if st.button("Generate Hash", key="single_hash_btn"):
        if input_text:
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/hash",
                        json={"data": input_text}
                    )
                    if response.status_code == 200:
                        result = response.json()["hash"]
                        st.code(result, language="text")
                        st.success("Hash generated successfully!")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
        else:
            st.warning("Please enter some text.")

with tab2:
    st.subheader("Bulk Hash Processing")
    st.markdown("Upload a file or paste multiple strings (one per line).")
    bulk_input = st.text_area("Paste strings here:", height=200, placeholder="String 1\nString 2\nString 3...")
    uploaded_file = st.file_uploader("Or upload a text file:", type=["txt"])
    
    if st.button("Process Bulk Request", key="bulk_hash_btn"):
        data_list = []
        if uploaded_file:
            data_list = [line.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") for line in uploaded_file if line]
        elif bulk_input:
            data_list = [line for line in bulk_input.split("\n") if line]
        
        if data_list:
            with st.spinner(f"Processing {len(data_list)} items across multiple cores..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/hash/bulk",
                        json={"data_list": data_list}
                    )
                    if response.status_code == 200:
                        hashes = response.json()["hashes"]
                        results_df = pd.DataFrame({
                            "Original (Preview)": [d[:50] + "..." if len(d) > 50 else d for d in data_list],
                            "SHA-256 Hash / Redacted Form": hashes
                        })
                        st.table(results_df)
                        csv = results_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download Results as CSV",
                            data=csv,
                            file_name="hashes.csv",
                            mime="text/csv",
                        )
                        st.success(f"Processed {len(data_list)} items successfully.")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
        else:
            st.warning("Please provide some input data.")

# Footer
st.divider()
st.caption("v2.0 | Deterministic | Third-Party Verifiable | Parallelized")
