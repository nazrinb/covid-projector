import streamlit as st
import pandas as pd
import plotly.express as px
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="COVID-19 Trends Dashboard", layout="wide")

st.title("🦠 COVID-19 Trends Dashboard")
st.markdown("""
Explore COVID-19 case and vaccination trends by country, powered by [Our World in Data](https://ourworldindata.org/covid-cases).
""")

@st.cache_data
def load_data():
    url = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
    df = pd.read_csv(url, parse_dates=['date'])
    return df

df = load_data()

# Sidebar for user input
st.sidebar.header("Filter")
countries = df['location'].dropna().unique()
country = st.sidebar.selectbox("Select Country", sorted(countries), index=list(countries).index("United States") if "United States" in countries else 0)
metric = st.sidebar.selectbox("Metric", ["New cases", "New deaths", "New vaccinations"])
rolling = st.sidebar.slider("Rolling Average (days)", 1, 14, 7)

# Filter data
country_df = df[df['location'] == country].copy()
country_df = country_df.sort_values('date')

if metric == "New cases":
    y = country_df['new_cases'].rolling(rolling).mean()
    y_label = "New Cases (Rolling Avg)"
elif metric == "New deaths":
    y = country_df['new_deaths'].rolling(rolling).mean()
    y_label = "New Deaths (Rolling Avg)"
else:
    y = country_df['new_vaccinations'].rolling(rolling).mean()
    y_label = "New Vaccinations (Rolling Avg)"

# Plot
fig = px.line(
    x=country_df['date'],
    
    y=y,
    labels={'x': 'Date', 'y': y_label},
    title=f"{metric} in {country}"
)
fig.update_layout(hovermode="x unified", template="plotly_white")

st.plotly_chart(fig, use_container_width=True)

# Show summary stats
st.subheader(f"Latest Data for {country}")
latest = country_df.iloc[-1]
st.write(f"**Date:** {latest['date'].date()}")
st.write(f"**Total Cases:** {int(latest['total_cases']) if pd.notna(latest['total_cases']) else 'N/A'}")
st.write(f"**Total Deaths:** {int(latest['total_deaths']) if pd.notna(latest['total_deaths']) else 'N/A'}")
st.write(f"**Total Vaccinations:** {int(latest['total_vaccinations']) if pd.notna(latest['total_vaccinations']) else 'N/A'}")