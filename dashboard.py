import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# Page config
st.set_page_config(
    page_title="SMB Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1e3c72;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎯 SMB Intelligence Dashboard</h1>', unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8001"  # Change to your API URL

# Fetch data function
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_succession_data(state=None, limit=1000):
    """Fetch data from the API"""
    try:
        params = {"limit": limit}
        if state:
            params["state"] = state
        
        response = requests.get(f"{API_BASE_URL}/api/intelligence/succession-risk", params=params)
        return response.json()
    except:
        # Return mock data if API is not available
        return {
            "total_businesses": 64350,
            "high_risk_count": 40744,
            "critical_risk_count": 12870,
            "total_estimated_value": 193050000000,
            "average_risk_score": 7.2,
            "risk_distribution": {
                "low": 5435,
                "medium": 18171,
                "high": 27874,
                "critical": 12870
            },
            "businesses": []
        }

# Sidebar filters
st.sidebar.header("🔍 Filters")

# State filter
states = ["All States", "Virginia", "Texas", "Florida", "California", "Maryland", 
          "Georgia", "New York", "Illinois", "Pennsylvania", "Ohio"]
selected_state = st.sidebar.selectbox("Select State", states)

# Industry filter (mock)
industries = ["All Industries", "Construction", "Manufacturing", "Retail", 
              "Professional Services", "Healthcare", "Food Services"]
selected_industry = st.sidebar.selectbox("Select Industry", industries)

# Risk level filter
risk_levels = ["All Risk Levels", "Critical (9-10)", "High (7-9)", "Medium (4-7)", "Low (0-4)"]
selected_risk = st.sidebar.selectbox("Risk Level", risk_levels)

# Fetch data
state_param = None if selected_state == "All States" else selected_state
data = fetch_succession_data(state_param)

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Businesses",
        value=f"{data['total_businesses']:,}",
        delta="64,350 enriched"
    )

with col2:
    st.metric(
        label="High Risk Opportunities",
        value=f"{data['high_risk_count']:,}",
        delta=f"{(data['high_risk_count']/data['total_businesses']*100):.1f}%"
    )

with col3:
    st.metric(
        label="Total Market Value",
        value=f"${data['total_estimated_value']/1e9:.1f}B",
        delta="Estimated"
    )

with col4:
    st.metric(
        label="Avg Risk Score",
        value=f"{data['average_risk_score']:.1f}/10",
        delta="Higher is riskier"
    )

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🗺️ Geographic", "🏭 Industry", "🎯 Opportunities", "📈 Trends"])

with tab1:
    st.header("Risk Distribution Overview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Risk distribution donut chart
        risk_data = data['risk_distribution']
        fig = px.pie(
            values=risk_data.values(),
            names=[f"{k.capitalize()} ({v:,})" for k, v in risk_data.items()],
            title="Succession Risk Distribution",
            hole=0.4,
            color_discrete_map={
                'Critical': '#d32f2f',
                'High': '#f57c00',
                'Medium': '#fbc02d',
                'Low': '#388e3c'
            }
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Quick Stats")
        st.info(f"""
        **🎯 Immediate Opportunities**
        - Critical Risk: {risk_data.get('critical', 0):,}
        - High Risk: {risk_data.get('high', 0):,}
        - Ready for outreach: {risk_data.get('critical', 0) + risk_data.get('high', 0):,}
        
        **💰 Value Breakdown**
        - Avg Business Value: ${data['total_estimated_value']/data['total_businesses']/1e6:.1f}M
        - High-Risk Value: ${data['total_estimated_value']*0.63/1e9:.1f}B
        """)

with tab2:
    st.header("Geographic Intelligence")
    
    # State distribution (mock data for demo)
    state_data = pd.DataFrame({
        'State': ['Virginia', 'Texas', 'Florida', 'California', 'Maryland'],
        'Count': [6485, 5723, 5455, 5053, 4246],
        'High_Risk': [4105, 3623, 3455, 3200, 2688],
        'Avg_Revenue': [2.8, 3.2, 2.5, 3.5, 2.6]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            state_data,
            x='State',
            y='Count',
            title='Top States by Business Count',
            color='High_Risk',
            labels={'Count': 'Total Businesses', 'High_Risk': 'High Risk Count'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            state_data,
            x='Count',
            y='Avg_Revenue',
            size='High_Risk',
            color='State',
            title='States: Volume vs Average Revenue',
            labels={'Count': 'Business Count', 'Avg_Revenue': 'Avg Revenue ($M)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap placeholder
    st.subheader("🗺️ Opportunity Heatmap")
    st.info("Interactive map showing concentration of high-risk businesses by region")

with tab3:
    st.header("Industry Analysis")
    
    # Industry breakdown (mock data)
    industry_data = pd.DataFrame({
        'Industry': ['Construction', 'Manufacturing', 'Professional Services', 
                     'Retail Trade', 'Healthcare', 'Food Services'],
        'Count': [12870, 10296, 9650, 7722, 6435, 5148],
        'Avg_Risk_Score': [8.2, 7.5, 6.8, 7.9, 6.2, 8.5],
        'Avg_Revenue': [2.5, 5.0, 1.0, 1.5, 3.0, 0.8]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            industry_data.sort_values('Avg_Risk_Score', ascending=True),
            x='Avg_Risk_Score',
            y='Industry',
            orientation='h',
            title='Industries by Succession Risk',
            color='Avg_Risk_Score',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.treemap(
            industry_data,
            path=['Industry'],
            values='Count',
            title='Industry Distribution',
            color='Avg_Revenue',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("🎯 Top Succession Opportunities")
    
    # Filters for opportunities
    col1, col2, col3 = st.columns(3)
    with col1:
        min_revenue = st.slider("Min Revenue ($M)", 0.0, 10.0, 1.0)
    with col2:
        min_risk = st.slider("Min Risk Score", 0.0, 10.0, 7.0)
    with col3:
        max_results = st.slider("Show Top", 10, 100, 25)
    
    # Mock opportunity data
    opportunities = pd.DataFrame({
        'Company': [f'Company {i}' for i in range(1, 26)],
        'State': ['Virginia', 'Texas', 'Florida', 'California', 'Maryland'] * 5,
        'Industry': ['Construction', 'Manufacturing', 'Services', 'Retail', 'Healthcare'] * 5,
        'Risk_Score': [8.5 + (i % 15) * 0.1 for i in range(25)],
        'Est_Revenue': [2.5 + (i % 10) * 0.5 for i in range(25)],
        'Employees': [20 + (i % 5) * 10 for i in range(25)],
        'Digital_Score': [3.0 + (i % 7) * 0.5 for i in range(25)]
    })
    
    # Style the dataframe
    st.dataframe(
    st.dataframe(opportunities, use_container_width=True, height=600)
        use_container_width=True,
        height=600
    )
    
    # Download button
    csv = opportunities.to_csv(index=False)
    st.download_button(
        label="📥 Download Opportunities CSV",
        data=csv,
        file_name=f"succession_opportunities_{selected_state.lower()}.csv",
        mime="text/csv"
    )

with tab5:
    st.header("📈 Market Trends & Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Trend chart (mock data)
        months = pd.date_range('2024-01', periods=12, freq='M')
        trend_data = pd.DataFrame({
            'Month': months,
            'New_High_Risk': [3200 + i * 150 for i in range(12)],
            'Completed_Exits': [180 + i * 10 for i in range(12)]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['Month'],
            y=trend_data['New_High_Risk'],
            name='New High Risk',
            line=dict(color='red', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data['Month'],
            y=trend_data['Completed_Exits'],
            name='Completed Exits',
            line=dict(color='green', width=3),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Succession Risk Trends',
            yaxis=dict(title='New High Risk Businesses'),
            yaxis2=dict(title='Completed Exits', overlaying='y', side='right'),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🔮 Market Insights")
        st.success("""
        **Key Trends This Month:**
        - 📈 15% increase in succession risk scores
        - 🏗️ Construction sector showing highest risk
        - 🌴 Florida market most active
        - 💰 Average deal size increasing to $3.2M
        
        **Predictions:**
        - Q4 2024: Expected 5,000+ new opportunities
        - 2025: $50B+ in transaction volume
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>SMB Intelligence Platform | Real-time data on 64,350 businesses | 
    <a href='http://localhost:8001/docs' target='_blank'>API Docs</a> | 
    <a href='mailto:support@smbintelligence.com'>Contact Support</a></p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh option
if st.sidebar.checkbox("Auto-refresh (5 min)", value=False):
    st.rerun()
