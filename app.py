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
st.markdown(
    """
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
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .small-box textarea {
        width: 600px !important;
        height: 150px !important;
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
    .first-domain {
        background-color: #D6EAF8 !important; /* Slightly darker for first domain columns */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------ Header ------------------
st.markdown("<h1 style='text-align:center;color:#2E4053;'>Durga's Domain Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;color:#34495E;'>Enter multiple rows of domains. Each row separated by a newline, domains within a row separated by |</h4>", unsafe_allow_html=True)

# ------------------ Input ------------------
st.markdown("<div class='centered small-box'>", unsafe_allow_html=True)
domains_input = st.text_area(
    "",
    placeholder="get.topincomejobs.com|trk.topincomejobs.com|img.topincomejobs.com\nexample.com|www.example2.com"
)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Functions ------------------
def resolve_ip(host):
    try:
        return ",".join(list({ip[4][0] for ip in socket.getaddrinfo(host, None)}))
    except Exception:
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
    except Exception:
        pass
    return f"{mx1_ip},{mx2_ip}"

def get_expiry(domain):
    try:
        w = whois.whois(domain)
        exp = w.expiration_date
        if isinstance(exp, list):
            exp = exp[0]
        if isinstance(exp, datetime):
            return exp.date()
        return "Unknown"
    except Exception:
        return "Unknown"

# ------------------ Button ------------------
st.markdown("<div class='centered'>", unsafe_allow_html=True)
check_button = st.button("Check Domains")
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Processing ------------------
if check_button:
    if not domains_input.strip():
        st.warning("⚠️ Please enter at least one row of domains.")
    else:
        all_rows = [line.strip() for line in domains_input.splitlines() if line.strip()]
        final_rows = []

        for row_line in all_rows:
            domains = [d.strip() for d in row_line.split("|") if d.strip()]
            row_dict = {}
            for i, d in enumerate(domains):
                a_record = resolve_ip(d)

                if i == 0:
                    # First domain: full details + expiry
                    mx_ips = get_mx_ips(d)
                    main_domain = get_main_domain(d)
                    a_record_main = resolve_ip(main_domain)
                    expiry_date = get_expiry(main_domain)

                    row_dict[f"{d}"] = d
                    row_dict[f"A Record ({d})"] = a_record
                    row_dict[f"MX IPs ({d})"] = mx_ips
                    row_dict[f"Main Domain ({d})"] = main_domain
                    row_dict[f"A Record (Main {main_domain})"] = a_record_main
                    row_dict[f"Expiry Date ({main_domain})"] = expiry_date
                else:
                    # Subsequent domains: only domain & A record
                    row_dict[f"{d}"] = d
                    row_dict[f"A Record ({d})"] = a_record

            final_rows.append(row_dict)

        # Convert all rows to DataFrame
        df = pd.DataFrame(final_rows)

        # ------------------ Display Table ------------------
        st.markdown("### ✅ Results")
        st.markdown(
            df.to_html(index=False, escape=False),
            unsafe_allow_html=True
        )

        # CSV Download
        st.download_button(
            label="💾 Download CSV",
            data=df.to_csv(index=False),
            file_name="domain_dashboard_horizontal.csv",
            mime="text/csv"
        )

# ------------------ Footer ------------------
st.markdown("<div style='text-align:center;margin-top:30px;color:#2E4053;'>Built with ❤️ by Durga</div>", unsafe_allow_html=True)
