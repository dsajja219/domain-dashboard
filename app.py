import streamlit as st
import pandas as pd
import dns.resolver
import socket
import tldextract
import requests
import time
from datetime import datetime, timezone

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
    background-color: rgba(255,255,255,0.90);
    padding: 30px;
    border-radius: 15px;
}

/* TABLE */
table {
    border-collapse: collapse;
    width: 100%;
}

table th {
    background-color: #0D6EFD;
    color: white;
    font-weight: 700;
    font-size: 15px;
    text-align: center;
    padding: 12px;
    border: 1px solid #0B5ED7;
}

table td {
    background-color: #ffffff;
    color: #000000;
    text-align: center;
    padding: 10px;
    border: 1px solid #dee2e6;
}

/* Thumbs animation */
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.15); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;color:#2E4053;'>Durga's Domain Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<h4 style='text-align:center;color:#34495E;'>Excel → DNS → MX → Expiry Dashboard</h4>",
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

@st.cache_data(ttl=86400)
def get_expiry(domain):
    try:
        r = requests.get(f"https://rdap.org/domain/{domain}", timeout=10)
        if r.status_code != 200:
            return None
        for event in r.json().get("events", []):
            if event.get("eventAction") == "expiration":
                return event.get("eventDate")
    except:
        pass
    return None

def expiry_style(expiry):
    if not expiry or expiry == "Unknown":
        return "color:gray;"
    try:
        exp_date = datetime.fromisoformat(expiry.replace("Z","")).date()
        today = datetime.now(timezone.utc).date()
        days = (exp_date - today).days

        if days < 0:
            return "color:white;background-color:#dc3545;font-weight:bold;"
        elif days <= 30:
            return "color:#721c24;background-color:#f8d7da;font-weight:bold;"
        elif days <= 90:
            return "color:#856404;background-color:#fff3cd;font-weight:bold;"
        else:
            return "color:#155724;background-color:#d4edda;font-weight:bold;"
    except:
        return "color:gray;"

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
        # 👍 Thumbs-up animation
        st.markdown("""
        <div style="display:flex;justify-content:center;margin-top:20px;">
            <div style="font-size:80px;animation:pulse 1.2s infinite;">👍</div>
        </div>
        """, unsafe_allow_html=True)

        st.success("Excel uploaded successfully! Processing domains...")

        rows = []

        for _, r in df.iterrows():
            mailing = str(r["Mailing Domain"]).strip()
            tracking = str(r["Tracking Domain"]).strip()
            image = str(r["Image Hosting Domain"]).strip()

            main_domain = get_main_domain(mailing)
            expiry = get_expiry(main_domain)

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
                "Main Domain A Record": resolve_ip(main_domain),
                "Expiry Date": expiry or "Unknown"
            })

        out = pd.DataFrame(rows)

        st.markdown("### ✅ Results")
        st.dataframe(
            out.style.applymap(expiry_style, subset=["Expiry Date"]),
            use_container_width=True
        )

        # 🎆 Crackers / celebration for ~5 seconds
        st.markdown(
            "<h3 style='text-align:center;color:#198754;'>Processing Complete 🎉</h3>",
            unsafe_allow_html=True
        )

        end_time = time.time() + 5
        while time.time() < end_time:
            st.balloons()
            time.sleep(1)

        st.download_button(
            "💾 Download CSV",
            out.to_csv(index=False),
            "durga_domain_dashboard.csv",
            "text/csv"
        )
