import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Advanced COVID-19 Analytics Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #F5F7FA;
        color: #1B263B;
    }
    .metric-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(63, 81, 181, 0.08);
        border-left: 6px solid #3F51B5;
    }
    h1, h2, h3, h4 {
        color: #3F51B5;
    }
    .stButton>button {
        background-color: #3F51B5;
        color: #fff;
        border-radius: 25px;
        border: none;
        padding: 0.6em 2em;
        font-weight: bold;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background: #283593;
        color: #FFC107;
    }
    .custom-download-button button {
        background: linear-gradient(90deg, #3F51B5 0%, #FFC107 100%);
        color: #fff;
        border: none;
        border-radius: 25px;
        padding: 0.8em 2.2em;
        font-size: 1.1em;
        font-weight: bold;
        box-shadow: 0 4px 14px 0 rgba(63,81,181,0.10);
        transition: background 0.2s, color 0.2s, transform 0.1s;
        margin-top: 1.5em;
        margin-bottom: 1.5em;
        cursor: pointer;
        outline: none;
    }
    .custom-download-button button:hover {
        background: linear-gradient(90deg, #283593 0%, #FFD54F 100%);
        color: #3F51B5;
        transform: translateY(-2px) scale(1.03);
        box-shadow: 0 8px 24px 0 rgba(63,81,181,0.18);
    }
    </style>
""", unsafe_allow_html=True)

# Data loading with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    url = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
    df = pd.read_csv(url, parse_dates=['date'])
    return df

# Data preprocessing
def preprocess_data(df):
    # Calculate additional metrics
    df['case_fatality_rate'] = (df['total_deaths'] / df['total_cases'] * 100).round(2)
    df['vaccination_rate'] = (df['people_vaccinated'] / df['population'] * 100).round(2)
    return df

# Load and preprocess data
try:
    with st.spinner('Loading data...'):
        df = load_data()
        df = preprocess_data(df)
    st.success('Data loaded successfully!')
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Sidebar
st.sidebar.header("📊 Dashboard Controls")

# Country selection with search
countries = sorted(df['location'].unique())
country = st.sidebar.selectbox(
    "Select Country",
    countries,
    index=countries.index("United States") if "United States" in countries else 0
)

# Date range selection
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(df['date'].min().date(), df['date'].max().date()),
    min_value=df['date'].min().date(),
    max_value=df['date'].max().date()
)

# Metrics selection
metrics = st.sidebar.multiselect(
    "Select Metrics to Display",
    ["New cases", "New deaths", "New vaccinations", "Case fatality rate"],
    default=["New cases", "New deaths"]
)

# Rolling average adjustment
rolling = st.sidebar.slider(
    "Rolling Average (days)", 
    min_value=1, 
    max_value=14, 
    value=7
)

# Main content
st.title(f"🦠 COVID-19 Analytics Dashboard: {country}")
st.markdown(f"*Last updated: {df['date'].max().strftime('%B %d, %Y')}*")

# Filter data
mask = (
    (df['location'] == country) & 
    (df['date'].dt.date >= date_range[0]) & 
    (df['date'].dt.date <= date_range[1])
)
country_df = df.loc[mask].copy()

# Display key metrics in columns
col1, col2, col3, col4 = st.columns(4)

# Latest values
latest = country_df.iloc[-1]

with col1:
    st.markdown(
        """
        <div class="metric-card">
        <h3 style="color: #3F51B5;">Total Cases</h3>
        <h2>{:,.0f}</h2>
        </div>
        """.format(latest['total_cases'] if pd.notna(latest['total_cases']) else 0),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="metric-card">
        <h3 style="color: #E53935;">Total Deaths</h3>
        <h2>{:,.0f}</h2>
        </div>
        """.format(latest['total_deaths'] if pd.notna(latest['total_deaths']) else 0),
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="metric-card">
        <h3 style="color: #43A047;">Vaccination Rate</h3>
        <h2>{:.1f}%</h2>
        </div>
        """.format(latest['vaccination_rate'] if pd.notna(latest['vaccination_rate']) else 0),
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        """
        <div class="metric-card">
        <h3 style="color: #FFC107;">Case Fatality Rate</h3>
        <h2>{:.2f}%</h2>
        </div>
        """.format(latest['case_fatality_rate'] if pd.notna(latest['case_fatality_rate']) else 0),
        unsafe_allow_html=True
    )

# Trends visualization
st.subheader("📈 Trend Analysis")

# Create figure with secondary y-axis
fig = go.Figure()

colors = {
    "New cases": "#3F51B5",         # Indigo
    "New deaths": "#E53935",        # Crimson
    "New vaccinations": "#43A047",  # Emerald
    "Case fatality rate": "#FFC107" # Amber
}

for metric in metrics:
    if metric == "New cases":
        y = country_df['new_cases'].rolling(rolling).mean()
        name = f"New Cases ({rolling}-day avg)"
    elif metric == "New deaths":
        y = country_df['new_deaths'].rolling(rolling).mean()
        name = f"New Deaths ({rolling}-day avg)"
    elif metric == "New vaccinations":
        y = country_df['new_vaccinations'].rolling(rolling).mean()
        name = f"New Vaccinations ({rolling}-day avg)"
    else:  # Case fatality rate
        y = country_df['case_fatality_rate']
        name = "Case Fatality Rate (%)"

    fig.add_trace(
        go.Scatter(
            x=country_df['date'],
            y=y,
            name=name,
            line=dict(color=colors[metric]),
            hovertemplate="%{y:,.0f}<br>%{x|%B %d, %Y}<extra></extra>"
        )
    )

fig.update_layout(
    title=f"COVID-19 Trends in {country}",
    xaxis_title="Date",
    yaxis_title="Count",
    hovermode="x unified",
    template="plotly_white",
    height=600,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        font=dict(size=16, color="#1B263B")
    ),
    font=dict(
        family="Cinzel, Crimson Text, serif",
        size=16,
        color="#1B263B"
    ),
    title_font=dict(
        size=22,
        color="#3F51B5"
    ),
    xaxis=dict(
        tickangle=-45,
        tickfont=dict(size=14, color="#1B263B"),
        title_font=dict(size=18, color="#3F51B5"),
        nticks=12
    ),
    yaxis=dict(
        tickfont=dict(size=14, color="#1B263B"),
        title_font=dict(size=18, color="#3F51B5")
    ),
    plot_bgcolor="#F5F7FA",
    paper_bgcolor="#F5F7FA"
)

st.plotly_chart(fig, use_container_width=True)

# Weekly changes
st.subheader("📊 Weekly Changes")

# Calculate weekly statistics
weekly_stats = country_df.set_index('date').resample('W').agg({
    'new_cases': 'sum',
    'new_deaths': 'sum',
    'new_vaccinations': 'sum'
}).tail(4)

# Calculate week-over-week changes
weekly_changes = weekly_stats.pct_change() * 100

# Display weekly changes
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Weekly New Cases",
        f"{weekly_stats['new_cases'].iloc[-1]:,.0f}",
        f"{weekly_changes['new_cases'].iloc[-1]:+.1f}%"
    )

with col2:
    st.metric(
        "Weekly Deaths",
        f"{weekly_stats['new_deaths'].iloc[-1]:,.0f}",
        f"{weekly_changes['new_deaths'].iloc[-1]:+.1f}%"
    )

with col3:
    st.metric(
        "Weekly Vaccinations",
        f"{weekly_stats['new_vaccinations'].iloc[-1]:,.0f}",
        f"{weekly_changes['new_vaccinations'].iloc[-1]:+.1f}%"
    )

# Data table
st.subheader("📋 Detailed Data")
if st.checkbox("Show raw data"):
    st.dataframe(
        country_df[['date', 'new_cases', 'new_deaths', 'new_vaccinations', 
                   'case_fatality_rate', 'vaccination_rate']]
        .sort_values('date', ascending=False)
    )

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
    <p>Data source: <a href="https://ourworldindata.org/covid-cases">Our World in Data</a></p>
    <p>Updated daily | Last refresh: {}</p>
    </div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

# Download button
if st.button("Download Data"):
    csv = country_df.to_csv(index=False)
    st.markdown('<div class="custom-download-button">', unsafe_allow_html=True)
    st.download_button(
        label="⬇️ Download Data as CSV",
        data=csv,
        file_name=f'covid_data_{country}_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )
    st.markdown('</div>', unsafe_allow_html=True)