#!/usr/bin/env python3
"""
KBI Labs ML Dashboard - Streamlit Interface
Interactive dashboard for procurement intelligence ML models
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from quick_start_ml_prototype import KBIProcurementMLPrototype
except ImportError:
    st.error("Could not import ML prototype. Make sure quick_start_ml_prototype.py is in the same directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="KBI Labs ML Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-high { color: #28a745; font-weight: bold; }
    .success-medium { color: #ffc107; font-weight: bold; }
    .success-low { color: #dc3545; font-weight: bold; }
    .risk-low { color: #28a745; }
    .risk-medium { color: #ffc107; }
    .risk-high { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_sample_data():
    """Load or generate sample data"""
    ml_prototype = KBIProcurementMLPrototype()
    data = ml_prototype.prepare_synthetic_data(n_samples=500)
    features_df = ml_prototype.prepare_features(data)
    return data, features_df, ml_prototype

@st.cache_resource
def train_models():
    """Train ML models (cached)"""
    data, features_df, ml_prototype = load_sample_data()
    
    # Train models
    success_results = ml_prototype.train_contract_success_model(features_df)
    fraud_results = ml_prototype.train_fraud_detection_model(features_df)
    
    return ml_prototype, success_results, fraud_results, data, features_df

def main():
    # Header
    st.markdown('<h1 class="main-header">🎯 KBI Labs ML-Enhanced Procurement Intelligence</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Overview", "🎯 Contract Success Prediction", "🚨 Fraud Detection", 
         "📊 Data Analysis", "🔬 Model Performance", "⚙️ Settings"]
    )
    
    # Load models
    with st.spinner("Loading ML models..."):
        ml_prototype, success_results, fraud_results, data, features_df = train_models()
    
    if page == "🏠 Overview":
        show_overview(success_results, fraud_results, data)
    elif page == "🎯 Contract Success Prediction":
        show_contract_prediction(ml_prototype, success_results)
    elif page == "🚨 Fraud Detection":
        show_fraud_detection(ml_prototype, fraud_results)
    elif page == "📊 Data Analysis":
        show_data_analysis(data, features_df)
    elif page == "🔬 Model Performance":
        show_model_performance(success_results, fraud_results)
    elif page == "⚙️ Settings":
        show_settings()

def show_overview(success_results, fraud_results, data):
    """Overview dashboard"""
    st.header("📊 System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Contract Success Model Accuracy",
            value=f"{success_results['accuracy']:.1%}",
            delta="Production Ready" if success_results['accuracy'] > 0.8 else "Needs Improvement"
        )
    
    with col2:
        st.metric(
            label="Fraud Detection Precision",
            value=f"{fraud_results['precision']:.1%}",
            delta="Anomalies Detected"
        )
    
    with col3:
        st.metric(
            label="Companies Analyzed",
            value=f"{len(data):,}",
            delta="Synthetic Data"
        )
    
    with col4:
        contract_success_rate = data['contract_success'].mean()
        st.metric(
            label="Overall Success Rate",
            value=f"{contract_success_rate:.1%}",
            delta="Market Benchmark"
        )
    
    # Feature importance chart
    st.subheader("🎯 Most Important Factors for Contract Success")
    
    feature_importance = success_results['feature_importance']
    top_features = dict(list(feature_importance.items())[:10])
    
    fig_importance = px.bar(
        x=list(top_features.values()),
        y=list(top_features.keys()),
        orientation='h',
        title="Feature Importance for Contract Success Prediction",
        labels={'x': 'Importance Score', 'y': 'Features'}
    )
    fig_importance.update_layout(height=400)
    st.plotly_chart(fig_importance, use_container_width=True)
    
    # Success rate by key factors
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Success Rate by System Presence")
        
        system_success = []
        for system in ['gsa_calc_found', 'fpds_found', 'sam_opportunities_found', 'sam_entity_found']:
            success_rate = data[data[system] == True]['contract_success'].mean()
            system_success.append({
                'System': system.replace('_', ' ').title().replace('Found', ''),
                'Success Rate': success_rate
            })
        
        system_df = pd.DataFrame(system_success)
        fig_systems = px.bar(
            system_df, x='System', y='Success Rate',
            title="Contract Success Rate by Government System Presence"
        )
        st.plotly_chart(fig_systems, use_container_width=True)
    
    with col2:
        st.subheader("🌍 Success Rate by State")
        
        state_success = data.groupby('state')['contract_success'].mean().reset_index()
        state_success.columns = ['State', 'Success Rate']
        
        fig_states = px.bar(
            state_success, x='State', y='Success Rate',
            title="Contract Success Rate by State"
        )
        st.plotly_chart(fig_states, use_container_width=True)

def show_contract_prediction(ml_prototype, success_results):
    """Contract success prediction interface"""
    st.header("🎯 Contract Success Prediction")
    
    st.write("Enter company information to predict contract success probability:")
    
    # Input form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Basic Information")
        procurement_score = st.slider("Procurement Intelligence Score", 0, 100, 50)
        years_business = st.number_input("Years in Business", 1, 50, 10)
        state = st.selectbox("State", ['CA', 'TX', 'NY', 'FL', 'VA', 'MD', 'DC'])
        naics = st.selectbox("Primary NAICS", [541511, 541512, 541519, 541330, 541990])
    
    with col2:
        st.subheader("System Presence")
        gsa_calc = st.checkbox("Found in GSA CALC", value=False)
        fpds_found = st.checkbox("Found in FPDS", value=False)
        sam_opportunities = st.checkbox("SAM Opportunities Found", value=False)
        sam_entity = st.checkbox("SAM Entity Registered", value=True)
    
    with col3:
        st.subheader("Performance Metrics")
        gsa_rate = st.number_input("GSA Average Rate ($)", 0.0, 500.0, 100.0)
        fpds_value = st.number_input("Total FPDS Contract Value ($)", 0, 10000000, 100000)
        fpds_contracts = st.number_input("Number of FPDS Contracts", 0, 100, 5)
        sam_matches = st.number_input("SAM Opportunity Matches", 0, 50, 3)
    
    # Additional features
    with st.expander("Additional Business Characteristics"):
        col1, col2 = st.columns(2)
        with col1:
            small_business = st.checkbox("Small Business", value=True)
            veteran_owned = st.checkbox("Veteran Owned", value=False)
        with col2:
            woman_owned = st.checkbox("Woman Owned", value=False)
            agency_diversity = st.number_input("Agency Diversity", 0, 20, 2)
    
    # Predict button
    if st.button("🔮 Predict Contract Success", type="primary"):
        # Prepare company data
        company_data = {
            'procurement_intelligence_score': procurement_score,
            'gsa_calc_found': gsa_calc,
            'fpds_found': fpds_found,
            'sam_opportunities_found': sam_opportunities,
            'sam_entity_found': sam_entity,
            'gsa_avg_rate': gsa_rate,
            'fpds_total_value': fpds_value,
            'fpds_total_contracts': fpds_contracts,
            'sam_total_matches': sam_matches,
            'agency_diversity': agency_diversity,
            'contractor_network_size': 10,  # Default
            'years_in_business': years_business,
            'small_business': small_business,
            'veteran_owned': veteran_owned,
            'woman_owned': woman_owned,
            'state': state,
            'primary_naics': naics
        }
        
        try:
            # Make prediction
            prediction = ml_prototype.predict_contract_success(company_data)
            
            # Display results
            st.success("Prediction Complete!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                prob = prediction['success_probability']
                st.metric(
                    label="Success Probability",
                    value=f"{prob:.1%}",
                    delta="High Chance" if prob > 0.7 else "Medium Chance" if prob > 0.4 else "Low Chance"
                )
            
            with col2:
                confidence = prediction['confidence']
                color = "success" if confidence == "High" else "warning" if confidence == "Medium" else "error"
                st.metric(
                    label="Prediction Confidence",
                    value=confidence,
                    delta="Model Certainty"
                )
            
            with col3:
                recommendation = "Pursue Actively" if prob > 0.7 else "Consider Carefully" if prob > 0.4 else "High Risk"
                st.metric(
                    label="Recommendation",
                    value=recommendation,
                    delta="Business Action"
                )
            
            # Probability gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prob * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Contract Success Probability"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 40], 'color': "lightgray"},
                        {'range': [40, 70], 'color': "yellow"},
                        {'range': [70, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        except Exception as e:
            st.error(f"Prediction error: {str(e)}")

def show_fraud_detection(ml_prototype, fraud_results):
    """Fraud detection interface"""
    st.header("🚨 Fraud & Anomaly Detection")
    
    st.write("Analyze companies for potential fraud or unusual patterns:")
    
    # Similar input form but focused on fraud detection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Company Metrics")
        total_value = st.number_input("Total Contract Value ($)", 0, 50000000, 500000)
        num_contracts = st.number_input("Number of Contracts", 0, 200, 10)
        network_size = st.number_input("Contractor Network Size", 0, 100, 15)
        proc_score = st.slider("Procurement Score", 0, 100, 60)
    
    with col2:
        st.subheader("Performance Indicators")
        years = st.number_input("Years Active", 1, 50, 8)
        agency_count = st.number_input("Agencies Worked With", 0, 50, 5)
        avg_rate = st.number_input("Average Hourly Rate ($)", 0.0, 1000.0, 150.0)
        
    if st.button("🔍 Analyze for Anomalies", type="primary"):
        # Prepare data
        company_data = {
            'procurement_intelligence_score': proc_score,
            'gsa_calc_found': True,
            'fpds_found': True,
            'sam_opportunities_found': True,
            'sam_entity_found': True,
            'gsa_avg_rate': avg_rate,
            'fpds_total_value': total_value,
            'fpds_total_contracts': num_contracts,
            'sam_total_matches': 5,
            'agency_diversity': agency_count,
            'contractor_network_size': network_size,
            'years_in_business': years,
            'small_business': True,
            'veteran_owned': False,
            'woman_owned': False,
            'state': 'VA',
            'primary_naics': 541511
        }
        
        try:
            anomaly_result = ml_prototype.detect_anomalies(company_data)
            
            st.success("Analysis Complete!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                risk_level = anomaly_result['risk_level']
                color = "🟢" if risk_level == "Low" else "🟡" if risk_level == "Medium" else "🔴"
                st.metric(
                    label="Risk Level",
                    value=f"{color} {risk_level}",
                    delta="Anomaly Status"
                )
            
            with col2:
                anomaly_score = anomaly_result['anomaly_score']
                st.metric(
                    label="Anomaly Score",
                    value=f"{anomaly_score:.3f}",
                    delta="Lower is More Anomalous"
                )
            
            with col3:
                is_anomaly = anomaly_result['is_anomaly']
                status = "⚠️ FLAGGED" if is_anomaly else "✅ NORMAL"
                st.metric(
                    label="Status",
                    value=status,
                    delta="Model Classification"
                )
            
            # Risk indicators
            if is_anomaly:
                st.warning("🚨 This company shows anomalous patterns that warrant further investigation.")
                
                with st.expander("Possible Risk Factors"):
                    st.write("• Unusually high contract values relative to company profile")
                    st.write("• Unexpected network connections or relationships")
                    st.write("• Performance metrics outside normal ranges")
                    st.write("• Rapid growth or sudden changes in activity")
            else:
                st.success("✅ This company appears to have normal procurement patterns.")
                
        except Exception as e:
            st.error(f"Analysis error: {str(e)}")

def show_data_analysis(data, features_df):
    """Data analysis and exploration"""
    st.header("📊 Data Analysis & Insights")
    
    # Data overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dataset Overview")
        st.write(f"Total Records: {len(data):,}")
        st.write(f"Features: {len(features_df.columns)-2}")  # Excluding target variables
        st.write(f"Success Rate: {data['contract_success'].mean():.1%}")
        st.write(f"Potential Fraud Rate: {data['potential_fraud'].mean():.1%}")
    
    with col2:
        st.subheader("Data Quality")
        missing_data = data.isnull().sum().sum()
        st.write(f"Missing Values: {missing_data}")
        st.write(f"Data Completeness: {(1 - missing_data / data.size):.1%}")
        
    # Distribution analysis
    st.subheader("📈 Key Metrics Distribution")
    
    metric_choice = st.selectbox(
        "Choose metric to analyze:",
        ['procurement_intelligence_score', 'fpds_total_value', 'gsa_avg_rate', 
         'fpds_total_contracts', 'years_in_business']
    )
    
    fig_dist = px.histogram(
        data, x=metric_choice, color='contract_success',
        title=f"Distribution of {metric_choice.replace('_', ' ').title()}",
        marginal="box"
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Correlation analysis
    st.subheader("🔗 Feature Correlations")
    
    numeric_columns = data.select_dtypes(include=[np.number]).columns
    correlation_matrix = data[numeric_columns].corr()
    
    fig_corr = px.imshow(
        correlation_matrix,
        title="Feature Correlation Matrix",
        color_continuous_scale="RdBu"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

def show_model_performance(success_results, fraud_results):
    """Model performance metrics"""
    st.header("🔬 Model Performance Analysis")
    
    # Contract Success Model Performance
    st.subheader("🎯 Contract Success Model")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Model Metrics:**")
        st.write(f"• Accuracy: {success_results['accuracy']:.3f}")
        st.write(f"• Model Type: {success_results['model_type']}")
        st.write(f"• Training Size: {success_results['train_size']:,}")
        st.write(f"• Test Size: {success_results['test_size']:,}")
    
    with col2:
        # Classification report
        report = success_results['classification_report']
        st.write("**Classification Report:**")
        st.write(f"• Precision: {report['weighted avg']['precision']:.3f}")
        st.write(f"• Recall: {report['weighted avg']['recall']:.3f}")
        st.write(f"• F1-Score: {report['weighted avg']['f1-score']:.3f}")
    
    # Fraud Detection Model Performance
    st.subheader("🚨 Fraud Detection Model")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Model Metrics:**")
        st.write(f"• Model Type: {fraud_results['model_type']}")
        st.write(f"• Contamination Rate: {fraud_results['contamination_rate']:.1%}")
        st.write(f"• Anomalies Detected: {fraud_results['anomalies_detected']}")
    
    with col2:
        st.write("**Performance:**")
        st.write(f"• Precision: {fraud_results['precision']:.3f}")
        st.write(f"• Recall: {fraud_results['recall']:.3f}")
        st.write(f"• Score Mean: {fraud_results['anomaly_scores_mean']:.3f}")

def show_settings():
    """Settings and configuration"""
    st.header("⚙️ Settings & Configuration")
    
    st.subheader("Model Configuration")
    
    with st.expander("Contract Success Model Settings"):
        st.write("• Model: Random Forest Classifier")
        st.write("• Estimators: 100")
        st.write("• Max Depth: 10")
        st.write("• Cross-validation: 5-fold")
    
    with st.expander("Fraud Detection Model Settings"):
        st.write("• Model: Isolation Forest")
        st.write("• Contamination: 5%")
        st.write("• Algorithm: Auto")
    
    st.subheader("Data Sources")
    
    with st.expander("Current Data Integration"):
        st.write("✅ USASpending.gov API")
        st.write("✅ SAM.gov Entity Registration")
        st.write("✅ GSA CALC Labor Rates")
        st.write("✅ FPDS Contract History")
        st.write("🔄 SAM.gov Opportunities (Requires API Key)")
    
    st.subheader("System Status")
    st.success("✅ All models loaded and operational")
    st.info("ℹ️ Using synthetic data for demonstration")
    st.warning("⚠️ Replace with real data for production use")

if __name__ == "__main__":
    main()