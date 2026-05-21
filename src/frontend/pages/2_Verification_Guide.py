"""
Verification Guide — Kyouji SHA-256 Hashing Tool
Shows technical users exactly how to independently reproduce any hash produced by
this tool using standard Python or Linux shell utilities — no special software required.
"""
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import load_logo, inject_global_css, render_header, render_sidebar

logo_img, logo_html = load_logo()

st.set_page_config(
    page_title="Verification Guide — Kyouji",
    page_icon=logo_img,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_header(logo_html, title="Independent Verification Guide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
render_sidebar(BACKEND_URL)

st.markdown("---")

st.markdown("""
Every hash produced by this tool is **fully reproducible** using only a terminal and
standard system utilities. This page walks you through generating the same hash locally
so you can confirm the output is correct without relying on this tool at all.
""")

# ── Pre-processing Rules ───────────────────────────────────────────────────────
st.header("1. Pre-processing Rules")
st.info(
    "Before hashing, the backend applies exactly one transformation: "
    "**leading and trailing whitespace is stripped** (spaces, tabs, newlines). "
    "Everything else — capitalisation, internal spaces, punctuation, Unicode — is preserved exactly."
)

st.markdown("""
| Input | After stripping | Hash input |
|-------|-----------------|------------|
| `  John Smith  ` | `John Smith` | `John Smith` |
| `john smith` | `john smith` | `john smith` ← **different hash** |
| `JOHN SMITH` | `JOHN SMITH` | `JOHN SMITH` ← **different hash** |
| `John\\tSmith` | `John\\tSmith` | `John\\tSmith` (internal tab preserved) |

The output prefix `RCMP_REDACT_` is **not** part of the hash input — it is appended to
the raw 64-character hex digest after hashing.
""")

# ── Python ─────────────────────────────────────────────────────────────────────
st.header("2. Verify Using Python")
st.markdown("Works on any system with Python 3 installed. No third-party packages needed.")

st.code("""
import hashlib

# Replace this with the exact value you submitted to the tool
data = "John Smith"

# Replicate the backend pre-processing: strip leading/trailing whitespace
cleaned = data.strip()

# Compute SHA-256 and format the output exactly as the tool does
digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
result = f"RCMP_REDACT_{digest}"

print(result)
# → RCMP_REDACT_ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b7e23d900d944c536cd0
""", language="python")

st.markdown("**To run it:**")
st.code("""
python3 verify.py
""", language="bash")

st.markdown("""
> **Tip:** Save the snippet above as `verify.py`, edit the `data` variable, and run it.
> The printed value should match exactly what the tool returned.
""")

# ── Linux / Shell ──────────────────────────────────────────────────────────────
st.header("3. Verify Using Linux / macOS Shell")
st.markdown("""
`sha256sum` (Linux) and `shasum -a 256` (macOS) are available on all Unix-like systems
without any installation.
""")

st.subheader("3.1 Single value")
st.code("""
# The -n flag prevents echo from appending a newline (critical — a trailing newline
# would change the hash).  Strip whitespace manually if your input has any.
echo -n "John Smith" | sha256sum
# → ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b7e23d900d944c536cd0  -
""", language="bash")

st.markdown("""
Prepend `RCMP_REDACT_` to the 64-character hex string to get the full redacted form:
```
RCMP_REDACT_ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b7e23d900d944c536cd0
```
""")

st.subheader("3.2 Bulk — verify every line of a file")
st.code("""
#!/bin/bash
# verify_file.sh
# Usage: bash verify_file.sh input.txt
#
# Reads each line, strips leading/trailing whitespace, hashes it,
# and prints "Original → RCMP_REDACT_<hash>" to stdout.

INPUT="$1"
while IFS= read -r line || [[ -n "$line" ]]; do
    # Strip leading and trailing whitespace (mirrors the Go backend)
    stripped=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [[ -n "$stripped" ]]; then
        hash=$(printf '%s' "$stripped" | sha256sum | awk '{print $1}')
        echo "$stripped,RCMP_REDACT_$hash"
    fi
done < "$INPUT"
""", language="bash")

st.markdown("""
**To run it:**
```bash
bash verify_file.sh your_data.txt > local_hashes.csv
```
The output CSV can be diffed directly against the file downloaded from this tool.
""")

# ── macOS Specific ─────────────────────────────────────────────────────────────
st.subheader("3.3 macOS note")
st.code("""
# macOS ships shasum instead of sha256sum
echo -n "John Smith" | shasum -a 256
""", language="bash")

# ── PowerShell ─────────────────────────────────────────────────────────────────
st.header("4. Verify Using Windows PowerShell")
st.code("""
$data    = "John Smith"
$cleaned = $data.Trim()
$bytes   = [System.Text.Encoding]::UTF8.GetBytes($cleaned)
$digest  = [System.BitConverter]::ToString(
               [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
           ).Replace("-", "").ToLower()

Write-Output "RCMP_REDACT_$digest"
# → RCMP_REDACT_ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b7e23d900d944c536cd0
""", language="powershell")

# ── Common Pitfalls ────────────────────────────────────────────────────────────
st.header("5. Common Pitfalls")
st.warning("""
**Trailing newline from `echo`**  
Plain `echo "..."` appends a `\\n` to the string before piping it. Always use
`echo -n` or `printf '%s'` when testing a single value in the shell.
""")

st.warning("""
**Case sensitivity**  
`John Smith` and `john smith` produce entirely different hashes. Ensure the
value you pass locally is cased exactly as submitted to the tool.
""")

st.warning("""
**Encoding**  
The backend encodes input as **UTF-8** before hashing. If your local tool uses a
different encoding (e.g., Latin-1), the hash will differ for any non-ASCII character.
""")

st.divider()
st.caption("v2.0")
