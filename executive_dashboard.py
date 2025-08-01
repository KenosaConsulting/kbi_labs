import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="SMB Intelligence Executive Dashboard", layout="wide")

# API endpoints
API_BASE = "http://localhost:8003"

st.title("🎯 SMB Intelligence Executive Dashboard")
st.subheader("Enriched Data with Google Places + Domain Intelligence")

# Fetch data
@st.cache_data(ttl=300)
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE}{endpoint}")
        return response.json()
    except:
        return None

# Summary metrics
summary = fetch_data("/analytics/summary")
if summary:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Enriched",
            f"{summary['overview']['total_businesses']:,}",
            "With domain analysis"
        )
    
    with col2:
        st.metric(
            "High Risk Opportunities",
            f"{summary['overview']['high_risk_count']:,}",
            f"{summary['insights']['immediate_opportunities']/summary['overview']['total_businesses']*100:.0f}%"
        )
    
    with col3:
        st.metric(
            "Google Visibility",
            summary['insights']['google_visibility_rate'],
            "Found on Google"
        )
    
    with col4:
        st.metric(
            "Market Value at Risk",
            f"${summary['insights']['market_value_at_risk']/1e6:.1f}M",
            "Ready to transact"
        )

# Prime targets
st.header("🔥 Prime Acquisition Targets")
st.info("High risk + No digital presence = Immediate opportunities")

prime = fetch_data("/prime-targets")
if prime and prime['prime_targets']:
    df_prime = pd.DataFrame(prime['prime_targets'])
    
    # Display key columns
    display_cols = ['organization_name', 'city', 'state', 'succession_risk_score', 
                    'website_status', 'domain_age_years', 'estimated_revenue']
    
    available_cols = [col for col in display_cols if col in df_prime.columns]
    
    st.dataframe(
        df_prime[available_cols].rename(columns={
            'organization_name': 'Company',
            'succession_risk_score': 'Risk Score',
            'website_status': 'Website',
            'domain_age_years': 'Domain Age',
            'estimated_revenue': 'Est. Revenue'
        }),
        use_container_width=True
    )
    
    # Download button
    csv = df_prime.to_csv(index=False)
    st.download_button(
        "📥 Download Prime Targets CSV",
        csv,
        "prime_targets.csv",
        "text/csv"
    )

# Established businesses
st.header("🏛️ Established Businesses at Risk")
st.info("10+ year old domains with high succession risk")

established = fetch_data("/established-at-risk")
if established and established['businesses']:
    df_est = pd.DataFrame(established['businesses'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Count", established['count'])
    with col2:
        st.metric("Average Age", f"{established['avg_age']:.1f} years")
    
    st.dataframe(df_est, use_container_width=True)

# Technology insights
if summary and summary.get('technology_usage'):
    st.header("💻 Technology Stack Analysis")
    
    tech_df = pd.DataFrame(
        list(summary['technology_usage'].items()),
        columns=['Technology', 'Count']
    ).sort_values('Count', ascending=False)
    
    st.bar_chart(tech_df.set_index('Technology'))

# Action items
st.header("📋 Recommended Actions")

col1, col2 = st.columns(2)

with col1:
    st.success("""
    **Immediate Opportunities:**
    1. Contact businesses with no Google presence
    2. Target 10+ year domains with high risk
    3. Focus on businesses with DIY websites
    4. Prioritize no-website businesses
    """)

with col2:
    st.info("""
    **Data Insights:**
    - Low Google visibility = acquisition opportunity
    - Old domains = established businesses
    - No SSL = behind on technology
    - Domain age correlates with succession readiness
    """)

st.markdown("---")
st.caption("Data refreshes every 5 minutes | Powered by Google Places API + Domain Intelligence")
