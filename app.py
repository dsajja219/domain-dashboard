import streamlit as st
import pandas as pd
import dns.resolver
import socket
import tldextract

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
    .small-box input {
        width: 500px !important;
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
    """,
    unsafe_allow_html=True
)

# ------------------ Header ------------------
st.markdown("<h1 style='text-align:center;color:#2E4053;'>Durga's Domain Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;color:#34495E;'>Enter multiple domains separated by |</h4>", unsafe_allow_html=True)

# ------------------ Input ------------------
st.markdown("<div class='centered small-box'>", unsafe_allow_html=True)
domains_input = st.text_input(
    "",
    placeholder="example.com|example2.com|example3.com"
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

# ------------------ Button ------------------
st.markdown("<div class='centered'>", unsafe_allow_html=True)
check_button = st.button("Check Domains")
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Processing ------------------
if check_button:
    if not domains_input.strip():
        st.warning("⚠️ Please enter at least one domain.")
    else:
        domains = [d.strip() for d in domains_input.split("|") if d.strip()]
        result_dict = {}

        for d in domains:
            a_record = resolve_ip(d)
            mx_ips = get_mx_ips(d)
            main_domain = get_main_domain(d)
            a_record_main = resolve_ip(main_domain)

            # Add to horizontal dict
            result_dict[f"{d}"] = d
            result_dict[f"A Record ({d})"] = a_record
            result_dict[f"MX IPs ({d})"] = mx_ips
            result_dict[f"Main Domain ({d})"] = main_domain
            result_dict[f"A Record (Main {main_domain})"] = a_record_main

        # Convert to single-row DataFrame
        df = pd.DataFrame([result_dict])

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
            file_name="horizontal_domain_results.csv",
            mime="text/csv"
        )

# ------------------ Footer ------------------
st.markdown("<div style='text-align:center;margin-top:30px;color:#2E4053;'>Built with ❤️ by Durga</div>", unsafe_allow_html=True)
