import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="VascCalc Pro - Gefäßchirurgie", layout="wide", initial_sidebar_state="expanded")

# --- CSS für besseres Styling ---
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .profit { color: #28a745; font-size: 20px; font-weight: bold; }
    .loss { color: #dc3545; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🩸 VascCalc Pro: Erlös- & Deckungsbeitragsrechner")
st.markdown("Interaktives Dashboard für gefäßchirurgische & endovaskuläre Eingriffe")

# --- 1. Sidebar: Globale Parameter & Sektor ---
with st.sidebar:
    st.header("⚙️ Abrechnungsszenario")
    fallart = st.radio(
        "Sektor wählen:",
        ["Stationär (DRG + ZE)", "Hybrid-DRG (§ 115f)", "Ambulant (AOP)"]
    )

    st.header("🏥 Klinik-Parameter")
    basisfallwert = st.number_input("Landesbasisfallwert (€)", value=4000, step=50, help="Gültiger Basisfallwert für das Bundesland")
    op_minuten_kosten = st.number_input("OP-Kosten pro Min (€)", value=18, step=1, help="Inkl. Personal & Saal")
    
    st.markdown("---")
    st.write("Pauschalen:")
    pauschale_hybrid = st.number_input("Hybrid-Pauschale (€)", value=2800, step=100)
    pauschale_ambulant = st.number_input("AOP-Pauschale (€)", value=850, step=50)

# --- Hauptbereich: Eingriff definieren ---
st.markdown("### 1. Klinischer Eingriff & Etagen")
col_eingriff, col_interv = st.columns(2)

with col_eingriff:
    basis_eingriff = st.selectbox(
        "Primärer Eingriff / Basis-DRG:",
        ["Nur Intervention (PTA/Stent)", 
         "Leisten-TEA & Patch (5-381.2)", 
         "Bypass (Fem-Pop / Crural) (5-393.*)"]
    )
    
    basis_cw, basis_sachkosten = 0.0, 0
    if basis_eingriff == "Leisten-TEA & Patch (5-381.2)": basis_cw, basis_sachkosten = 1.5, 350 
    elif basis_eingriff == "Bypass (Fem-Pop / Crural) (5-393.*)": basis_cw, basis_sachkosten = 2.4, 800 
    elif basis_eingriff == "Nur Intervention (PTA/Stent)": basis_cw, basis_sachkosten = 0.9, 150 

with col_interv:
    st.write("**Simultane Interventionen (Mehrebenen):**")
    c_b, c_o, c_u = st.columns(3)
    interv_becken = c_b.checkbox("Becken (Iliaca)")
    interv_os = c_o.checkbox("Oberschenkel (SFA)")
    interv_us = c_u.checkbox("Unterschenkel")

    zusatz_cw = sum([0.6 if interv_becken else 0, 0.4 if interv_os else 0, 0.5 if interv_us else 0])

# --- Material 1: Atherektomie & CTO ---
st.markdown("### 2. Spezial-Katheter (Atherektomie, Thrombektomie, CTO)")
col_ath1, col_ath2 = st.columns(2)
kosten_atherektomie, ze_atherektomie = 0, 0

with col_ath1:
    if st.checkbox("Jetstream (ca. 1.800 €)"): kosten_atherektomie += 1800; ze_atherektomie += 1200 if fallart == "Stationär (DRG + ZE)" else 0
    if st.checkbox("Rotarex (ca. 1.200 €)"): kosten_atherektomie += 1200; ze_atherektomie += 800 if fallart == "Stationär (DRG + ZE)" else 0
    if st.checkbox("ByCross (ca. 900 €)"): kosten_atherektomie += 900; ze_atherektomie += 500 if fallart == "Stationär (DRG + ZE)" else 0

with col_ath2:
    if st.checkbox("Phoenix (ca. 1.300 €)"): kosten_atherektomie += 1300; ze_atherektomie += 900 if fallart == "Stationär (DRG + ZE)" else 0
    anzahl_cto = st.number_input("CTO Katheter (z.B. Crosser, 350 €/St.)", 0, 5, 0)
    kosten_atherektomie += (anzahl_cto * 350)

# --- Material 2: Stents & Ballons ---
st.markdown("### 3. Stents & Ballons (Implantate)")
c1, c2, c3, c4 = st.columns(4)
anzahl_unbeschichtet = c1.number_input("Standard PTA Ballon", 0, 10, 0)
anzahl_dcb = c2.number_input("DCB Ballon (ZE)", 0, 10, 0)
anzahl_bms = c3.number_input("BMS / Nitinol", 0, 10, 0)
anzahl_gecovert = c4.number_input("Gecovert (VBX/Viabahn)", 0, 10, 0)

kosten_endo = (anzahl_unbeschichtet * 90) + (anzahl_dcb * 450) + (anzahl_bms * 800) + (anzahl_gecovert * 1600)
gesamt_sachkosten = basis_sachkosten + kosten_endo + kosten_atherektomie

ze_erloes = ze_atherektomie
if fallart == "Stationär (DRG + ZE)":
    ze_erloes += (anzahl_dcb * 600) + (anzahl_gecovert * 1300)

# --- OP Zeit & Personalkosten ---
st.markdown("### 4. OP-Zeit (Schnitt-Naht & Rüstzeit)")
schnitt_naht = st.slider("Schnitt-Naht-Zeit (Min)", 15, 360, 90, 15)
ruestzeit = st.slider("Rüst-/Anästhesiezeit (Min)", 15, 120, 45, 15)
personalkosten = (schnitt_naht + ruestzeit) * op_minuten_kosten

# --- Berechnungslogik ---
if fallart == "Stationär (DRG + ZE)":
    basis_erloes = (basis_cw + zusatz_cw) * basisfallwert
elif fallart == "Hybrid-DRG (§ 115f)":
    basis_erloes = pauschale_hybrid
else: 
    basis_erloes = pauschale_ambulant

gesamt_erloes = basis_erloes + ze_erloes
deckungsbeitrag = gesamt_erloes - (gesamt_sachkosten + personalkosten)

# --- 5. Dashboard & Auswertung ---
st.markdown("---")
st.markdown("<p class='big-font'>📊 Betriebswirtschaftliche Auswertung</p>", unsafe_allow_html=True)

if fallart != "Stationär (DRG + ZE)" and (ze_erloes > 0 or ze_atherektomie > 0 or anzahl_dcb > 0):
    st.error("🚨 **Sektor-Warnung:** Im ambulanten/Hybrid-Setting entfallen die Zusatzentgelte (ZE) für DCB, VBX und Atherektomie. Der Eingriff wird durch die Materialkosten stark defizitär!")

# Top Level Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Gesamterlös (inkl. ZE)", f"{gesamt_erloes:,.0f} €".replace(",", "."))
m2.metric("Personalkosten (OP)", f"- {personalkosten:,.0f} €".replace(",", "."))
m3.metric("Gesamte Sachkosten", f"- {gesamt_sachkosten:,.0f} €".replace(",", "."))

if deckungsbeitrag > 0:
    m4.metric("Deckungsbeitrag", f"{deckungsbeitrag:,.0f} €".replace(",", "."), "Profitabel")
else:
    m4.metric("Deckungsbeitrag", f"{deckungsbeitrag:,.0f} €".replace(",", "."), "- Defizit", delta_color="inverse")

# --- Interaktives Plotly Waterfall Chart ---
fig = go.Figure(go.Waterfall(
    name = "2026", orientation = "v",
    measure = ["relative", "relative", "relative", "relative", "relative", "total"],
    x = ["Basis-Erlös", "Zusatzentgelte (ZE)", "Sachkosten (Basis)", "Material (Endo/Ath)", "Personalkosten", "Deckungsbeitrag"],
    textposition = "outside",
    text = [f"+{basis_erloes:,.0f}", f"+{ze_erloes:,.0f}", f"-{basis_sachkosten:,.0f}", f"-{kosten_endo + kosten_atherektomie:,.0f}", f"-{personalkosten:,.0f}", f"{deckungsbeitrag:,.0f}"],
    y = [basis_erloes, ze_erloes, -basis_sachkosten, -(kosten_endo + kosten_atherektomie), -personalkosten, deckungsbeitrag],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
    decreasing = {"marker":{"color":"#dc3545"}},
    increasing = {"marker":{"color":"#28a745"}},
    totals = {"marker":{"color":"#007bff"}}
))

fig.update_layout(
    title = "Finanzieller Fluss (Wasserfalldiagramm)",
    waterfallgap = 0.3,
    height = 500,
    margin=dict(l=20, r=20, t=50, b=20)
)

st.plotly_chart(fig, use_container_width=True)
