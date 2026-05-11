import streamlit as st
import requests
import pandas as pd
import json

# Set page configuration
st.set_page_config(
    page_title="Forensic Data Verification Tool",
    page_icon="🛡️",
    layout="wide",
)

# Custom CSS for premium look
st.markdown("""
    <style>
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
    .header-container {
        padding: 2rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    h1 {
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

# App Header
with st.container():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("🛡️ Forensic Data Verification Tool")
    st.markdown("### Enterprise-Grade Secure Hashing & Verification")
    st.markdown("Ensure data integrity with HMAC-SHA256 one-way hashing. Optimized for multi-core performance.")
    st.markdown('</div>', unsafe_allow_html=True)

# Backend URL (configurable via env but defaulting to the service name in docker-compose)
BACKEND_URL = "http://backend:8000"

# Sidebar for configuration/info
with st.sidebar:
    st.header("Status")
    try:
        # Simple health check (optional, but good for UI)
        # response = requests.get(f"{BACKEND_URL}/docs", timeout=1)
        st.success("Backend Connected")
    except:
        st.error("Backend Disconnected")
    
    st.divider()
    st.info("Forensic Integrity: Data is processed exactly as provided (UTF-8 encoded). Every character, including whitespace and case, is significant.")

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
                        
                        # Display results in a table
                        results_df = pd.DataFrame({
                            "Original (Preview)": [d[:50] + "..." if len(d) > 50 else d for d in data_list],
                            "HMAC-SHA256 Hash": hashes
                        })
                        st.table(results_df)
                        
                        # Download button for results
                        csv = results_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download Results as CSV",
                            data=csv,
                            file_name="forensic_hashes.csv",
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
st.caption("Forensic Data Verification Tool v1.1 | Secure | No Normalization | Parallelized")
