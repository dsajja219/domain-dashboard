import streamlit as st
import pandas as pd
import dns.resolver
import socket
import tldextract
import whois
from datetime import datetime

st.set_page_config(
    page_title="Durga's Domain Dashboard",
    layout="wide"
)

# ------------------ Background & Styles ------------------
st.markdown("""
<style>
body {
    background-image: url("https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1950&q=80");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
.stApp {
    background-color: rgba(255, 255, 255, 0.85);
    padding: 30px;
    border-radius: 15px;
}
table th, table td {
    text-align: center;
    padding: 10px;
}
table th {
    background-color: #007BFF;
    color: white;
}
table td {
    background-color: #f9f9f9;
    color: black;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#2E4053;'>Durga's Domain Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;color:#34495E;'>Upload Excel file with Mailing, Tracking, and Image Hosting Domains</h4>", unsafe_allow_html=True)

# ------------------ Functions ------------------
def resolve_ip(host):
    try:
        return ",".join(list({ip[4][0] for ip in socket.getaddrinfo(host, None)}))
    except:
        return "Unresolved"

def get_main_domain(domain):
    ext = tldextract.extract(domain)
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    return domain

def get_mx_ips(domain):
    mx1_ip = "None"
    mx2_ip = "None"
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_records = sorted(
            [(str(r.exchange).rstrip("."), r.preference) for r in answers],
            key=lambda x: x[1]
        )
        if len(mx_records) >= 1:
            mx1_ip = resolve_ip(mx_records[0][0])
        if len(mx_records) >= 2:
            mx2_ip = resolve_ip(mx_records[1][0])
    except:
        pass
    return mx1_ip, mx2_ip

def get_expiry(domain):
    try:
        w = whois.whois(domain)
        exp = w.expiration_date
        if isinstance(exp, list):
            exp = exp[0]
        if isinstance(exp, datetime):
            return exp.date()
        return "Unknown"
    except:
        return "Unknown"

# ------------------ File Upload ------------------
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
if uploaded_file:
    df_input = pd.read_excel(uploaded_file)

    # Ensure columns exist
    required_cols = ["Mailing Domain", "Tracking Domain", "Image Hosting Domain"]
    if not all(col in df_input.columns for col in required_cols):
        st.error(f"Excel must have columns: {', '.join(required_cols)}")
    else:
        # ------------------ Process each row ------------------
        final_rows = []

        for _, row in df_input.iterrows():
            row_dict = {}

            # --- Mailing Domain (full details) ---
            mailing = str(row["Mailing Domain"]).strip()
            a_record_mailing = resolve_ip(mailing)
            mx1, mx2 = get_mx_ips(mailing)
            main_domain = get_main_domain(mailing)
            a_record_main = resolve_ip(main_domain)
            expiry = get_expiry(main_domain)

            row_dict["Mailing Domain"] = mailing
            row_dict["A Record"] = a_record_mailing
            row_dict["MX1 IP"] = mx1
            row_dict["MX2 IP"] = mx2

            # --- Tracking Domain (only A Record) ---
            tracking = str(row["Tracking Domain"]).strip()
            a_record_tracking = resolve_ip(tracking)
            row_dict["Tracking Domain"] = tracking
            row_dict["Tracking Domain A Record"] = a_record_tracking

            # --- Image Hosting Domain (only A Record) ---
            image = str(row["Image Hosting Domain"]).strip()
            a_record_image = resolve_ip(image)
            row_dict["Image Hosting Domain"] = image
            row_dict["Image Hosting Domain A Record"] = a_record_image

            # --- Main Domain details ---
            row_dict["Main Domain"] = main_domain
            row_dict["A Record (Main Domain)"] = a_record_main
            row_dict["Expiry Date"] = expiry

            final_rows.append(row_dict)

        df_output = pd.DataFrame(final_rows)

        st.markdown("### ✅ Results")
        st.dataframe(df_output, use_container_width=True)

        # ------------------ Download ------------------
        st.download_button(
            label="💾 Download Excel",
            data=df_output.to_csv(index=False),
            file_name="domain_dashboard_output.csv",
            mime="text/csv"
        )
