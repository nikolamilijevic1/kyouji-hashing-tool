"""
Shared utilities for the Kyouji Streamlit multi-page app.
Centralises the logo loading, page config, and global CSS injection
so every page is visually consistent without duplication.
"""
import base64
import os
import streamlit as st
from PIL import Image


def load_logo() -> tuple[object, str]:
    """Return (logo_img, logo_html) — falls back to an emoji if the file is missing."""
    logo_path = os.path.join(os.path.dirname(__file__), "company_logo.svg.png")
    try:
        logo_img = Image.open(logo_path)
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
        logo_html = (
            f'<img src="data:image/png;base64,{logo_base64}" '
            'width="112" style="margin-right: 20px;">'
        )
    except Exception:
        logo_img = "🏮"
        logo_html = '<span style="font-size: 50px; margin-right: 20px;">🏮</span>'
    return logo_img, logo_html


def inject_global_css() -> None:
    """Inject the application-wide CSS that every page shares."""
    st.markdown("""
        <style>
        /* Transparent header keeps the sidebar collapse control visible */
        [data-testid="stHeader"] {
            background: transparent !important;
            color: #ffffff !important;
        }

        /* Style the collapsed sidebar expand control */
        [data-testid="collapsedSidebarCollapsedControl"] {
            background-color: #182848 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 5px !important;
            border: 1px solid #4b6cb7 !important;
            margin-left: 15px !important;
            margin-top: 10px !important;
        }

        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .stDeployButton {display: none;}
        div[data-testid="stStatusWidget"] {visibility: hidden !important;}

        .main {
            background-color: #0e1117;
            color: #ffffff;
        }
        .stButton>button {
            background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
            color: white;
            border: none;
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

        /* Enforce 16px minimum across all text surfaces */
        p, label, input, textarea, select, ::placeholder,
        button[role="tab"],
        div[data-testid="stCaptionContainer"],
        .stAlert p, table, th, td,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {
            font-size: 16px !important;
        }

        /* Soft premium grey-blue for caption helper text */
        div[data-testid="stCaptionContainer"] {
            color: #cbd5e1 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def render_header(logo_html: str, title: str = "SHA-256 Hashing and Redaction Tool") -> None:
    """Render the branded logo + gradient H1 header."""
    st.markdown(f"""
        <div class="header-flex">
            {logo_html}
            <h1>{title}</h1>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar(backend_url: str = "http://localhost:8000") -> None:
    """Render a fully customized, premium multi-page navigation sidebar."""
    import requests
    with st.sidebar:
        st.markdown(
            '<p style="font-weight: 800; font-size: 19px; letter-spacing: 1px; '
            'color: #4b6cb7; margin-bottom: 15px; margin-top: 5px;">'
            'Contents</p>',
            unsafe_allow_html=True
        )
        st.page_link("app.py", label="App")
        st.page_link("pages/1_Technical_Reference.py", label="Technical Reference")
        st.page_link("pages/2_Verification_Guide.py", label="Verification Guide")
        
        st.divider()
        st.header("Status")
        try:
            resp = requests.get(f"{backend_url}/health", timeout=2)
            if resp.status_code == 200:
                st.success("Backend Connected")
            else:
                st.error("Backend Unreachable")
        except Exception:
            st.error("Backend Disconnected")

