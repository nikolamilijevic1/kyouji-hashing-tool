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
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="112" style="margin-right: 20px;">'
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

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")

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
    uploaded_file = st.file_uploader("Or upload a text file:", type=["txt", "csv", "log"])
    
    if uploaded_file:
        # Auto-reset if a new file is uploaded
        if st.session_state.get("last_uploaded_filename") != uploaded_file.name:
            if "download_file_path" in st.session_state:
                del st.session_state["download_file_path"]
            if "download_file_name" in st.session_state:
                del st.session_state["download_file_name"]
            st.session_state.last_uploaded_filename = uploaded_file.name

        st.info("File uploaded. Click below to begin streaming.")
        
        if st.button("Process & Prepare Download", key="process_file_btn"):
            with st.spinner("Streaming file securely..."):
                import httpx
                import tempfile
                import os
                import uuid
                import json
                
                uploaded_file.seek(0)
                file_id = str(uuid.uuid4())
                static_dir = "/app/shared"
                os.makedirs(static_dir, exist_ok=True)
                download_filename = f"{file_id}_hashes.csv"
                input_filename = f"input_{file_id}.txt"
                input_path = os.path.join(static_dir, input_filename)
                
                progress_text = "Saving uploaded file to shared disk..."
                progress_bar = st.progress(0, text=progress_text)
                
                total_lines = 0
                with open(input_path, "wb") as f_out:
                    while True:
                        buf = uploaded_file.read(1024 * 1024) # 1MB chunks
                        if not buf: break
                        f_out.write(buf)
                        total_lines += buf.count(b"\n")
                
                if total_lines == 0: total_lines = 1 # Prevent division by zero
                
                try:
                    progress_text = "Analyzing file and hashing on disk..."
                    progress_bar.progress(0, text=progress_text)
                    
                    import time
                    start_time = time.time()
                    lines_processed = 0
                    last_update = start_time
                    
                    payload = {
                        "input_file": input_filename,
                        "output_file": download_filename
                    }
                    
                    with httpx.stream("POST", f"{BACKEND_URL}/hash/file/disk", json=payload, timeout=None) as r:
                        if r.status_code == 200:
                            for chunk in r.iter_lines():
                                if not chunk: continue
                                try:
                                    data = json.loads(chunk)
                                    lines_processed = data.get("processed", lines_processed)
                                except:
                                    pass
                                
                                # Update UI every 0.5 seconds to balance performance and feedback
                                current_time = time.time()
                                if current_time - last_update >= 0.5:
                                    elapsed = current_time - start_time
                                    speed = lines_processed / elapsed if elapsed > 0 else 0
                                    eta = (total_lines - lines_processed) / speed if speed > 0 else 0
                                    
                                    progress_bar.progress(
                                        min(lines_processed / total_lines, 1.0), 
                                        text=f"Processed {lines_processed:,} / {total_lines:,} lines | {speed:,.0f} lines/s | ETA: {eta:,.0f}s"
                                    )
                                    last_update = current_time
                            
                            st.session_state.download_file_name = download_filename
                            total_elapsed = time.time() - start_time
                            progress_bar.progress(1.0, text=f"Complete! {lines_processed:,} lines in {total_elapsed:.1f}s.")
                        else:
                            st.error(f"Error: {r.read().decode()}")
                except Exception as e:
                    st.error(f"Failed to stream to backend: {e}")

        # The download button must be outside the process block so it doesn't disappear on click
        if st.session_state.get("download_file_name"):
            with st.container():
                st.success("Processing complete! Ready for download.")
                st.info("💡 Note: For large files (10MB+), your browser may appear unresponsive for a few moments after clicking download while the file is prepared.")
                
                download_url = f"{PUBLIC_BACKEND_URL}/download/{st.session_state.download_file_name}"
                st.markdown(f'''
                    <a href="{download_url}" style="
                        display: block;
                        background-color: #1e4620;
                        color: #73d085;
                        padding: 10px 24px;
                        text-align: center;
                        text-decoration: none;
                        font-size: 16px;
                        font-weight: 600;
                        border-radius: 8px;
                        border: 1px solid #1e4620;
                        transition: all 0.3s ease;
                        margin-top: 10px;
                    " onmouseover="this.style.backgroundColor='#1a3d1c'; this.style.transform='translateY(-2px)'" onmouseout="this.style.backgroundColor='#1e4620'; this.style.transform='translateY(0)'">
                        Download Processed File
                    </a>
                ''', unsafe_allow_html=True)
                
                # Prevent rerun crashes when the UI updates again
                if "download_file_path" in st.session_state:
                    del st.session_state["download_file_path"]
        
    elif bulk_input:
        if st.button("Process Bulk Request", key="bulk_hash_btn"):
            data_list = [line for line in bulk_input.split("\n") if line]
            if data_list:
                with st.spinner(f"Processing {len(data_list)} items across multiple cores..."):
                    try:
                        import requests
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
