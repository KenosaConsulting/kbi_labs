import streamlit as st

st.set_page_config(page_title="SMB Intelligence", layout="wide")

st.title("🎯 SMB Intelligence Platform")
st.subheader("Real-time intelligence on 64,350 US small businesses")

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Businesses", "64,350")
col2.metric("High Risk", "40,744") 
col3.metric("Market Value", "$95.5B")
col4.metric("Avg Risk", "7.2/10")

# Info boxes
st.success("✅ System Status: **OPERATIONAL** | 64,350 businesses enriched | API running on port 8001")

# Quick links
st.markdown("""
### 🔗 Quick Links
- [API Documentation](http://3.143.232.123:8001/docs)
- [Get Florida Opportunities](http://3.143.232.123:8001/api/intelligence/succession-risk?state=Florida)
- [Landing Page](http://3.143.232.123:8001/)
""")

# Sample data
st.header("📊 Top Succession Opportunities")
st.markdown("""
| Company | State | Risk Score | Est. Revenue |
|---------|-------|------------|--------------|
| ABC Construction | Virginia | 9.2/10 | $3.2M |
| XYZ Manufacturing | Texas | 8.8/10 | $4.5M |
| Smith Services | Florida | 8.5/10 | $2.8M |
""")

st.info("💡 **Pro Tip**: Use the API to query specific states, industries, or risk levels")
