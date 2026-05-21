import streamlit as st
import requests
import pandas as pd
import json
import httpx
import urllib.parse
import os
import uuid
import time

from utils import load_logo, inject_global_css, render_header, render_sidebar

logo_img, logo_html = load_logo()

st.set_page_config(
    page_title="SHA-256 Hashing Tool",
    page_icon=logo_img,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_header(logo_html)

st.markdown("### Deterministic Data Integrity & Verification")
st.markdown("Redact sensitive data or verify integrity using deterministic SHA-256.")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")

render_sidebar(BACKEND_URL)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Single Hash", "Bulk Processing"])

# ── Single Hash ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Generate Single Hash")
    with st.form(key="single_hash_form", clear_on_submit=False, border=False):
        input_text = st.text_input("Enter text to hash:", placeholder="Type your data here...")
        st.caption("Press **Enter** to send hash")
        submit_single = st.form_submit_button("Generate Hash")

    if submit_single:
        if input_text:
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/hash",
                        json={"data": input_text},
                    )
                    if response.status_code == 200:
                        st.code(response.json()["hash"], language="text")
                        st.success("Hash generated successfully!")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
        else:
            st.warning("Please enter some text.")

# ── Bulk Processing ───────────────────────────────────────────────────────────
with tab2:
    st.subheader("Bulk Hash Processing")
    st.markdown("Upload a file or paste multiple strings (one per line).")

    uploaded_file = st.file_uploader("Upload a text file:", type=["txt", "csv", "log"])

    if uploaded_file:
        if st.session_state.get("last_uploaded_filename") != uploaded_file.name:
            st.session_state.pop("download_file_path", None)
            st.session_state.pop("download_file_name", None)
            st.session_state.last_uploaded_filename = uploaded_file.name

        st.info("File uploaded. Click below to begin processing.")

        if st.button("Process & Prepare Download", key="process_file_btn"):
            with st.spinner("Streaming file securely..."):
                uploaded_file.seek(0)
                file_id = str(uuid.uuid4())
                static_dir = "/app/shared"
                os.makedirs(static_dir, exist_ok=True)
                download_filename = f"{file_id}_hashes.csv"
                input_filename = f"input_{file_id}.txt"
                input_path = os.path.join(static_dir, input_filename)

                progress_bar = st.progress(0, text="Saving uploaded file to shared disk...")

                total_lines = 0
                with open(input_path, "wb") as f_out:
                    while True:
                        buf = uploaded_file.read(1024 * 1024)
                        if not buf:
                            break
                        f_out.write(buf)
                        total_lines += buf.count(b"\n")

                if total_lines == 0:
                    total_lines = 1

                try:
                    progress_bar.progress(0, text="Hashing on disk...")
                    start_time = time.time()
                    lines_processed = 0
                    last_update = start_time

                    payload = {"input_file": input_filename, "output_file": download_filename}

                    with httpx.stream("POST", f"{BACKEND_URL}/hash/file/disk", json=payload, timeout=None) as r:
                        if r.status_code == 200:
                            for chunk in r.iter_lines():
                                if not chunk:
                                    continue
                                try:
                                    lines_processed = json.loads(chunk).get("processed", lines_processed)
                                except Exception:
                                    pass

                                now = time.time()
                                if now - last_update >= 0.5:
                                    elapsed = now - start_time
                                    speed = lines_processed / elapsed if elapsed > 0 else 0
                                    eta = (total_lines - lines_processed) / speed if speed > 0 else 0
                                    progress_bar.progress(
                                        min(lines_processed / total_lines, 1.0),
                                        text=f"Processed {lines_processed:,} / {total_lines:,} lines | "
                                             f"{speed:,.0f} lines/s | ETA: {eta:,.0f}s",
                                    )
                                    last_update = now

                            st.session_state.download_file_name = download_filename
                            total_elapsed = time.time() - start_time
                            progress_bar.progress(
                                1.0,
                                text=f"Complete! {lines_processed:,} lines in {total_elapsed:.1f}s.",
                            )
                        else:
                            st.error(f"Error: {r.read().decode()}")
                except Exception as e:
                    st.error(f"Failed to stream to backend: {e}")

        if st.session_state.get("download_file_name"):
            st.success("Processing complete! Ready for download.")
            st.info(
                "💡 For large files (10MB+), your browser may be briefly unresponsive "
                "after clicking download while the file is prepared."
            )
            safe_orig_name = urllib.parse.quote(
                st.session_state.get("last_uploaded_filename", "hashes.csv")
            )
            download_url = (
                f"{PUBLIC_BACKEND_URL}/download/{st.session_state.download_file_name}"
                f"?original_name={safe_orig_name}"
            )
            st.markdown(
                f'''<a href="{download_url}" style="
                    display: block; background-color: #1e4620; color: #73d085;
                    padding: 10px 24px; text-align: center; text-decoration: none;
                    font-size: 16px; font-weight: 600; border-radius: 8px;
                    border: 1px solid #1e4620; transition: all 0.3s ease; margin-top: 10px;"
                    onmouseover="this.style.backgroundColor=\'#1a3d1c\'"
                    onmouseout="this.style.backgroundColor=\'#1e4620\'">
                    Download Processed File
                </a>''',
                unsafe_allow_html=True,
            )
            st.session_state.pop("download_file_path", None)

    st.divider()

    with st.form(key="bulk_paste_form", clear_on_submit=False, border=False):
        bulk_input = st.text_area(
            "Paste strings here:",
            height=200,
            placeholder="String 1\nString 2\nString 3...",
        )
        st.caption("Press **Ctrl+Enter** to send hash")
        submit_bulk = st.form_submit_button("Process Bulk Request")

    if submit_bulk:
        if bulk_input:
            data_list = [line for line in bulk_input.split("\n") if line]
            if data_list:
                with st.spinner(f"Processing {len(data_list)} items..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/hash/bulk",
                            json={"data_list": data_list},
                        )
                        if response.status_code == 200:
                            hashes = response.json()["hashes"]
                            results_df = pd.DataFrame({
                                "Original (Preview)": [
                                    d[:50] + "..." if len(d) > 50 else d for d in data_list
                                ],
                                "SHA-256 Hash / Redacted Form": hashes,
                            })
                            st.table(results_df)
                            csv = results_df.to_csv(index=False).encode("utf-8")
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
        else:
            st.warning("Please enter some text.")

st.divider()
st.caption("v2.0")
