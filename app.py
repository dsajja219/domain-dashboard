import streamlit as st
import pandas as pd
import dns.resolver
import socket
import tldextract
import time

st.set_page_config(
    page_title="Durga's Domain Dashboard",
    layout="wide"
)

# ------------------ UI & STYLES ------------------
st.markdown("""
<style>
body {
    background-image: url("https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1950&q=80");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

.stApp {
    background-color: rgba(255,255,255,0.92);
    padding: 30px;
    border-radius: 15px;
}

/* TABLE STYLING */
table {
    border-collapse: collapse;
    width: 100%;
}

table th {
    background-color: #0D6EFD;
    color: white;
    font-weight: 700;
    text-align: center;
    padding: 12px;
}

table td {
    background-color: #ffffff;
    color: black;
    text-align: center;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;color:#2E4053;'>Durga's Domain Dashboard</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h4 style='text-align:center;color:#34495E;'>Upload Excel file to check DNS & MX records</h4>",
    unsafe_allow_html=True
)

# ------------------ FUNCTIONS ------------------
@st.cache_data(ttl=86400)
def resolve_ip(host):
    try:
        return ",".join(sorted({ip[4][0] for ip in socket.getaddrinfo(host, None)}))
    except:
        return "Unresolved"

def get_main_domain(domain):
    ext = tldextract.extract(domain)
    return f"{ext.domain}.{ext.suffix}" if ext.domain and ext.suffix else domain

@st.cache_data(ttl=86400)
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

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx", "xls"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_cols = ["Mailing Domain", "Tracking Domain", "Image Hosting Domain"]
    if not all(col in df.columns for col in required_cols):
        st.error("Excel must contain: Mailing Domain | Tracking Domain | Image Hosting Domain")
    else:
        st.success("Excel uploaded successfully. Processing domains...")

        rows = []

        for _, r in df.iterrows():
            mailing = str(r["Mailing Domain"]).strip()
            tracking = str(r["Tracking Domain"]).strip()
            image = str(r["Image Hosting Domain"]).strip()
            main_domain = get_main_domain(mailing)

            rows.append({
                "Mailing Domain": mailing,
                "A Record": resolve_ip(mailing),
                "MX1 IP": get_mx_ips(mailing)[0],
                "MX2 IP": get_mx_ips(mailing)[1],

                "Tracking Domain": tracking,
                "Tracking A Record": resolve_ip(tracking),

                "Image Hosting Domain": image,
                "Image Hosting A Record": resolve_ip(image),

                "Main Domain": main_domain,
                "Main Domain A Record": resolve_ip(main_domain)
            })

        out = pd.DataFrame(rows)

        st.markdown("### ✅ Results")
        st.dataframe(out, use_container_width=True)

        # 🎈 OPTIONAL BALLOONS
        st.balloons()

        st.download_button(
            "💾 Download CSV",
            out.to_csv(index=False),
            "durga_domain_dashboard.csv",
            "text/csv"
        )
