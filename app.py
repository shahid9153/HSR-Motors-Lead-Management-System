import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import numpy as np
import time

# ===============================
# APP CONFIGURATION
# ===============================
st.set_page_config(
    layout="wide",
    page_title="LeadStream Pro+ Dashboard",
    page_icon="💼",
    initial_sidebar_state="expanded"
)

# ===============================
# GLOBAL SETTINGS
# ===============================
CSV_FILE = 'leads_data.csv'
STATUS_OPTIONS = ['New', 'Contacted', 'Qualified', 'Lost Sale', 'Sold', 'Disqualified', 'Unreachable']
INTEREST_OPTIONS = ['Interested', 'Holding', 'Not Interested', 'N/A']
SOURCE_OPTIONS = ['Google Ads', 'Facebook', 'Instagram', 'LinkedIn', 'Websites', 'Offline Events', 'Other']
DEFAULT_OWNER = "Unassigned"

# Enhanced Color Palette (gradient & premium tones)
COLOR_PRIMARY = "#6C63FF"        # Deep Violet
COLOR_SECONDARY = "#8E2DE2"      # Purple Gradient
COLOR_ACCENT = "#00C9A7"         # Teal Accent
COLOR_BG = "#F8F9FB"
COLOR_TEXT = "#1F1F39"

# ===============================
# CUSTOM STYLING
# ===============================
st.markdown(
    f"""
    <style>
    body {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: 'Inter', sans-serif;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLOR_SECONDARY} 0%, #6C63FF 100%);
        color: white;
    }}

    .sidebar-title {{
        font-weight: 800;
        font-size: 1.5rem;
        text-align: center;
        margin-top: -10px;
        color: white;
    }}

    /* Titles */
    .main-title {{
        text-align: center;
        color: {COLOR_SECONDARY};
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 10px;
    }}

    /* Metrics */
    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 15px 25px;
        border-radius: 12px;
        border-left: 5px solid {COLOR_ACCENT};
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}

    /* Data Table */
    div[data-testid="stDataFrameResizable"] {{
        border-radius: 10px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        background-color: white;
    }}

    /* Section headers */
    h2, h3 {{
        color: {COLOR_SECONDARY};
        font-weight: 700;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ===============================
# DATA INITIALIZATION
# ===============================
def initialize_data():
    time.sleep(0.5)
    expected_columns = [
        'LeadID', 'FullName', 'Location', 'Status', 'Phone', 'Email',
        'LeadSource', 'CreatedDate', 'InterestStatus', 'Notes',
        'EngagementScore', 'Owner'
    ]
    try:
        if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
            df = pd.DataFrame(columns=expected_columns)
            df.to_csv(CSV_FILE, index=False)
        df = pd.read_csv(CSV_FILE)
        df['CreatedDate'] = pd.to_datetime(df['CreatedDate'], errors='coerce')
        for col, default in [('Owner', DEFAULT_OWNER), ('LeadSource', 'Other'), ('InterestStatus', 'N/A')]:
            if col not in df.columns:
                df[col] = default
            df[col] = df[col].fillna(default)
        if 'LeadID' not in df.columns or df['LeadID'].isnull().any():
            df.insert(0, 'LeadID', range(1, 1 + len(df)))
        df = df.dropna(subset=['FullName', 'Status'])
        df = df.set_index('LeadID', drop=False)
    except Exception as e:
        st.error(f"Error initializing data: {e}")
        return pd.DataFrame()
    return df.copy()

if 'df_leads' not in st.session_state:
    st.session_state['df_leads'] = initialize_data()
df_leads = st.session_state['df_leads']

# ===============================
# UTILITY FUNCTIONS
# ===============================
def save_data(df):
    try:
        df.to_csv(CSV_FILE, index=False)
        st.toast("✅ Changes saved successfully.")
    except Exception as e:
        st.error(f"Save failed: {e}")

def update_main_dataframe(edited_df, original_df):
    df_to_update = original_df.copy()
    df_to_update.update(edited_df)
    st.session_state['df_leads'] = df_to_update
    save_data(df_to_update)
    st.rerun()

# ===============================
# PAGE 1: OVERALL DASHBOARD
# ===============================
def render_overall_dashboard(df):
    st.markdown("<div class='main-title'>📊 Overall Performance Dashboard</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available to display.")
        return

    # --- KPIs ---
    total_leads = len(df)
    contacted = len(df[df['Status'] == 'Contacted'])
    interested = len(df[df['InterestStatus'] == 'Interested'])
    qualified = len(df[df['Status'] == 'Qualified'])
    sold = len(df[df['Status'] == 'Sold'])
    conversion_rate = (qualified / total_leads) * 100 if total_leads else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Leads", total_leads)
    col2.metric("Contacted", contacted)
    col3.metric("Interested", interested)
    col4.metric("Qualified", qualified)
    col5.metric("Sold", sold, f"{conversion_rate:.1f}%")

    st.markdown("---")

    # --- 🎯 Lead Source Distribution ---
    st.subheader("🎯 Lead Source Distribution")

    all_sources = ['Google Ads', 'Facebook', 'Instagram', 'LinkedIn', 'Websites', 'Offline Events', 'Other']
    source_counts = df['LeadSource'].value_counts().reindex(all_sources, fill_value=0).reset_index()
    source_counts.columns = ['Lead Source', 'Count']

    color_map = {
        'Google Ads': '#4285F4',
        'Facebook': '#1877F2',
        'Instagram': '#E1306C',
        'LinkedIn': '#0A66C2',
        'Websites': '#34A853',
        'Offline Events': '#F4B400',
        'Other': '#9E9E9E'
    }

    fig_pie = px.pie(
        source_counts,
        names='Lead Source',
        values='Count',
        color='Lead Source',
        color_discrete_map=color_map,
        title="Lead Acquisition Sources",
        hole=0.4
    )

    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label',
        pull=[0.03 if c > 0 else 0 for c in source_counts['Count']],
        marker=dict(line=dict(color='white', width=2))
    )

    fig_pie.update_layout(
        showlegend=True,
        legend_title_text="Sources",
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=13),
        margin=dict(t=50, b=20)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Monthly Trends ---
    st.subheader("📈 Monthly Lead Trends")
    df['Month'] = df['CreatedDate'].dt.to_period('M').astype(str)
    trend = df.groupby('Month').size().reset_index(name='Count')
    fig_trend = px.line(
        trend, x='Month', y='Count', markers=True,
        title="Leads Created Over Time",
        color_discrete_sequence=['#6C63FF']
    )
    fig_trend.update_layout(xaxis_title="Month", yaxis_title="Number of Leads", hovermode='x unified')
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Lead Status Summary ---
    st.subheader("📊 Lead Status Overview")
    status_summary = df['Status'].value_counts().reset_index()
    status_summary.columns = ['Status', 'Count']
    fig_bar = px.bar(
        status_summary, x='Status', y='Count', text='Count',
        color='Status', color_discrete_sequence=px.colors.qualitative.Pastel1,
        title="Lead Status Summary"
    )
    fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)

# ===============================
# PAGE 2: LEAD LISTINGS
# ===============================
def render_lead_listing(df):
    st.markdown("<div class='main-title'>📋 Lead Listings</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No leads to display.")
        return

    # --- Search and Filter ---
    col_search, col_filter = st.columns([0.7, 0.3])
    search_query = col_search.text_input("🔍 Search by Name or ID", placeholder="e.g., John or 102")

    df_filtered = df.copy()
    if search_query:
        df_filtered = df_filtered[
            df_filtered['FullName'].str.contains(search_query, case=False, na=False) |
            df_filtered['LeadID'].astype(str).str.contains(search_query, case=False, na=False)
        ]

    st.sidebar.subheader("Filter by Lead Status")
    lead_status_filter = st.sidebar.multiselect(
        "Select Status:",
        options=STATUS_OPTIONS,
        default=['New', 'Contacted', 'Qualified']
    )

    df_filtered = df_filtered[df_filtered['Status'].isin(lead_status_filter)]

    st.subheader(f"Active Leads ({len(df_filtered)} records)")

    editable_cols = ['Status', 'InterestStatus', 'Notes', 'LeadSource']
    disabled_cols = [c for c in df_filtered.columns if c not in editable_cols]

    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        column_order=(
            "LeadID", "FullName", "Location", "Phone", "Email",
            "LeadSource", "Status", "InterestStatus", "EngagementScore", "Notes", "Owner"
        ),
        disabled=disabled_cols,
        column_config={
            "LeadSource": st.column_config.SelectboxColumn("Lead Source", options=SOURCE_OPTIONS),
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
            "InterestStatus": st.column_config.SelectboxColumn("Interest", options=INTEREST_OPTIONS),
            "EngagementScore": st.column_config.ProgressColumn("Score", help="Engagement level 0–100"),
            "Notes": st.column_config.TextColumn("Notes / Remarks")
        },
        hide_index=True,
        key="lead_editor"
    )

    if not edited_df.equals(df_filtered):
        update_main_dataframe(edited_df, df)

# ===============================
# PAGE 3: SALESPERSON DASHBOARD
# ===============================
def render_salesperson_dashboard(df):
    st.markdown("<div class='main-title'>👤 Salesperson Dashboard</div>", unsafe_allow_html=True)

    salespersons = sorted(df['Owner'].unique().tolist())
    selected_person = st.selectbox("Select Salesperson:", salespersons)

    df_person = df[df['Owner'] == selected_person]
    if df_person.empty:
        st.warning("No leads assigned.")
        return

    total_leads = len(df_person)
    qualified = len(df_person[df_person['Status'] == 'Qualified'])
    interested = len(df_person[df_person['InterestStatus'] == 'Interested'])
    conversion_rate = (qualified / total_leads) * 100 if total_leads else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assigned Leads", total_leads)
    col2.metric("Interested Leads", interested)
    col3.metric("Qualification Rate", f"{conversion_rate:.1f}%")

    st.markdown("---")
    st.subheader("📊 Lead Status Distribution")
    status_data = df_person['Status'].value_counts().reset_index()
    status_data.columns = ['Status', 'Count']
    fig = px.bar(status_data, x='Status', y='Count',
                 color='Status', color_discrete_sequence=px.colors.qualitative.Set2,
                 title=f"Leads by Status for {selected_person}")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗂️ Assigned Leads Details")
    st.dataframe(df_person[['FullName', 'Location', 'Status', 'InterestStatus', 'LeadSource', 'EngagementScore']],
                 use_container_width=True, hide_index=True)

# ===============================
# SIDEBAR NAVIGATION
# ===============================
st.sidebar.markdown(f"<p class='sidebar-title'>📍 Navigation</p>", unsafe_allow_html=True)
page = st.sidebar.radio(
    "",
    ["Overall Dashboard", "Lead Listings", "Salesperson Dashboard"],
    index=0
)

if page == "Overall Dashboard":
    render_overall_dashboard(df_leads)
elif page == "Lead Listings":
    render_lead_listing(df_leads)
elif page == "Salesperson Dashboard":
    render_salesperson_dashboard(df_leads)
