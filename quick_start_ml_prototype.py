#!/usr/bin/env python3
"""
KBI Labs ML Prototype - Quick Start
First ML implementation using existing data and simple models
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KBIProcurementMLPrototype:
    """
    Quick start ML prototype for KBI Labs procurement intelligence
    Uses existing data patterns to create immediate value
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = []
        
    def prepare_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Create synthetic data based on your existing KBI Labs data structure
        Replace this with your actual data loading
        """
        logger.info(f"Generating {n_samples} synthetic procurement records...")
        
        np.random.seed(42)  # For reproducibility
        
        # Simulate data based on your existing schema
        data = {
            # Existing KBI Labs features
            'procurement_intelligence_score': np.random.normal(50, 20, n_samples),
            'gsa_calc_found': np.random.choice([True, False], n_samples, p=[0.3, 0.7]),
            'fpds_found': np.random.choice([True, False], n_samples, p=[0.4, 0.6]),
            'sam_opportunities_found': np.random.choice([True, False], n_samples, p=[0.2, 0.8]),
            'sam_entity_found': np.random.choice([True, False], n_samples, p=[0.6, 0.4]),
            
            # Financial features
            'gsa_avg_rate': np.random.exponential(100, n_samples),
            'fpds_total_value': np.random.exponential(50000, n_samples),
            'fpds_total_contracts': np.random.poisson(5, n_samples),
            'sam_total_matches': np.random.poisson(3, n_samples),
            
            # Network features (simulated)
            'agency_diversity': np.random.poisson(2, n_samples),
            'contractor_network_size': np.random.poisson(10, n_samples),
            
            # Geographic features
            'state': np.random.choice(['CA', 'TX', 'NY', 'FL', 'VA', 'MD', 'DC'], n_samples),
            
            # Industry features
            'primary_naics': np.random.choice([541511, 541512, 541519, 541330, 541990], n_samples),
            
            # Business characteristics
            'years_in_business': np.random.uniform(1, 50, n_samples),
            'small_business': np.random.choice([True, False], n_samples, p=[0.7, 0.3]),
            'veteran_owned': np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
            'woman_owned': np.random.choice([True, False], n_samples, p=[0.15, 0.85]),
        }
        
        df = pd.DataFrame(data)
        
        # Create target variable: Contract Success (based on logical rules)
        # Companies with higher scores, more matches, and presence in systems are more likely to succeed
        success_probability = (
            (df['procurement_intelligence_score'] / 100) * 0.4 +
            (df['gsa_calc_found'].astype(int)) * 0.2 +
            (df['fpds_found'].astype(int)) * 0.2 +
            (df['sam_opportunities_found'].astype(int)) * 0.1 +
            (df['sam_entity_found'].astype(int)) * 0.1 +
            np.random.normal(0, 0.1, n_samples)  # Add some noise
        )
        
        # Clip to [0, 1] and convert to binary
        success_probability = np.clip(success_probability, 0, 1)
        df['contract_success'] = (success_probability > 0.5).astype(int)
        
        # Create fraud labels (rare events, 5% fraud rate)
        fraud_indicators = (
            (df['fpds_total_value'] > df['fpds_total_value'].quantile(0.95)) |
            (df['contractor_network_size'] > df['contractor_network_size'].quantile(0.95)) |
            (df['procurement_intelligence_score'] < 10)
        )
        df['potential_fraud'] = fraud_indicators.astype(int)
        
        logger.info(f"Generated data shape: {df.shape}")
        logger.info(f"Contract success rate: {df['contract_success'].mean():.2f}")
        logger.info(f"Potential fraud rate: {df['potential_fraud'].mean():.2f}")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ML models
        """
        logger.info("Preparing features for ML models...")
        
        # Create feature engineering
        df_features = df.copy()
        
        # Numerical features
        numerical_features = [
            'procurement_intelligence_score', 'gsa_avg_rate', 'fpds_total_value',
            'fpds_total_contracts', 'sam_total_matches', 'agency_diversity',
            'contractor_network_size', 'years_in_business'
        ]
        
        # Fill missing values
        for col in numerical_features:
            df_features[col] = df_features[col].fillna(df_features[col].median())
        
        # Boolean features (convert to int)
        boolean_features = [
            'gsa_calc_found', 'fpds_found', 'sam_opportunities_found',
            'sam_entity_found', 'small_business', 'veteran_owned', 'woman_owned'
        ]
        
        for col in boolean_features:
            df_features[col] = df_features[col].astype(int)
        
        # Categorical features (encode)
        if 'state' not in self.encoders:
            self.encoders['state'] = LabelEncoder()
            df_features['state_encoded'] = self.encoders['state'].fit_transform(df_features['state'])
        else:
            df_features['state_encoded'] = self.encoders['state'].transform(df_features['state'])
        
        if 'primary_naics' not in self.encoders:
            self.encoders['primary_naics'] = LabelEncoder()
            df_features['naics_encoded'] = self.encoders['primary_naics'].fit_transform(df_features['primary_naics'])
        else:
            df_features['naics_encoded'] = self.encoders['primary_naics'].transform(df_features['primary_naics'])
        
        # Feature engineering: Create composite features
        df_features['value_per_contract'] = df_features['fpds_total_value'] / (df_features['fpds_total_contracts'] + 1)
        df_features['matches_per_agency'] = df_features['sam_total_matches'] / (df_features['agency_diversity'] + 1)
        df_features['experience_score'] = df_features['years_in_business'] * df_features['fpds_total_contracts']
        
        # Diversity score
        df_features['diversity_score'] = (
            df_features['small_business'] +
            df_features['veteran_owned'] +
            df_features['woman_owned']
        )
        
        # Select final feature columns
        self.feature_columns = (
            numerical_features + boolean_features +
            ['state_encoded', 'naics_encoded', 'value_per_contract',
             'matches_per_agency', 'experience_score', 'diversity_score']
        )
        
        logger.info(f"Prepared {len(self.feature_columns)} features: {self.feature_columns}")
        
        return df_features[self.feature_columns + ['contract_success', 'potential_fraud']]
    
    def train_contract_success_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train contract success prediction model
        """
        logger.info("Training contract success prediction model...")
        
        X = df[self.feature_columns]
        y = df['contract_success']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scalers['contract_success'] = StandardScaler()
        X_train_scaled = self.scalers['contract_success'].fit_transform(X_train)
        X_test_scaled = self.scalers['contract_success'].transform(X_test)
        
        # Train model
        self.models['contract_success'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.models['contract_success'].fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.models['contract_success'].predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Get feature importance
        feature_importance = dict(zip(
            self.feature_columns,
            self.models['contract_success'].feature_importances_
        ))
        
        # Sort by importance
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        results = {
            'model_type': 'RandomForestClassifier',
            'accuracy': accuracy,
            'feature_importance': feature_importance,
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
        logger.info(f"Contract success model accuracy: {accuracy:.3f}")
        logger.info(f"Top 5 important features: {list(feature_importance.keys())[:5]}")
        
        return results
    
    def train_fraud_detection_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train fraud/anomaly detection model
        """
        logger.info("Training fraud detection model...")
        
        X = df[self.feature_columns]
        
        # Scale features
        self.scalers['fraud_detection'] = StandardScaler()
        X_scaled = self.scalers['fraud_detection'].fit_transform(X)
        
        # Train Isolation Forest for anomaly detection
        self.models['fraud_detection'] = IsolationForest(
            contamination=0.05,  # 5% anomalies
            random_state=42,
            n_jobs=-1
        )
        
        self.models['fraud_detection'].fit(X_scaled)
        
        # Get anomaly scores
        anomaly_scores = self.models['fraud_detection'].decision_function(X_scaled)
        is_anomaly = self.models['fraud_detection'].predict(X_scaled) == -1
        
        # Evaluate against synthetic fraud labels
        y_true = df['potential_fraud'].values
        
        # Calculate precision, recall for anomaly detection
        true_anomalies = np.sum(y_true)
        detected_anomalies = np.sum(is_anomaly)
        true_positives = np.sum(y_true & is_anomaly)
        
        precision = true_positives / detected_anomalies if detected_anomalies > 0 else 0
        recall = true_positives / true_anomalies if true_anomalies > 0 else 0
        
        results = {
            'model_type': 'IsolationForest',
            'contamination_rate': 0.05,
            'anomalies_detected': int(detected_anomalies),
            'precision': precision,
            'recall': recall,
            'anomaly_scores_mean': float(np.mean(anomaly_scores)),
            'anomaly_scores_std': float(np.std(anomaly_scores))
        }
        
        logger.info(f"Fraud detection - Anomalies detected: {detected_anomalies}, Precision: {precision:.3f}, Recall: {recall:.3f}")
        
        return results
    
    def predict_contract_success(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict contract success for a single company
        """
        if 'contract_success' not in self.models:
            raise ValueError("Contract success model not trained yet")
        
        # Convert to DataFrame
        df = pd.DataFrame([company_data])
        
        # Prepare features (this should match training preparation)
        features = []
        for col in self.feature_columns:
            if col in df.columns:
                features.append(df[col].iloc[0])
            else:
                # Use median/mode for missing features
                features.append(0)  # Simple fallback
        
        # Scale features
        features_scaled = self.scalers['contract_success'].transform([features])
        
        # Predict
        probability = self.models['contract_success'].predict_proba(features_scaled)[0][1]
        prediction = self.models['contract_success'].predict(features_scaled)[0]
        
        return {
            'success_probability': float(probability),
            'predicted_success': bool(prediction),
            'confidence': 'High' if abs(probability - 0.5) > 0.3 else 'Medium' if abs(probability - 0.5) > 0.15 else 'Low'
        }
    
    def detect_anomalies(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomalies for a single company
        """
        if 'fraud_detection' not in self.models:
            raise ValueError("Fraud detection model not trained yet")
        
        # Similar to predict_contract_success but for anomaly detection
        df = pd.DataFrame([company_data])
        
        features = []
        for col in self.feature_columns:
            if col in df.columns:
                features.append(df[col].iloc[0])
            else:
                features.append(0)
        
        # Scale features
        features_scaled = self.scalers['fraud_detection'].transform([features])
        
        # Detect anomaly
        anomaly_score = self.models['fraud_detection'].decision_function(features_scaled)[0]
        is_anomaly = self.models['fraud_detection'].predict(features_scaled)[0] == -1
        
        return {
            'anomaly_score': float(anomaly_score),
            'is_anomaly': bool(is_anomaly),
            'risk_level': 'High' if is_anomaly else 'Medium' if anomaly_score < -0.1 else 'Low'
        }
    
    def save_models(self, directory: str = 'models'):
        """
        Save trained models and preprocessors
        """
        import os
        os.makedirs(directory, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            joblib.dump(model, f'{directory}/{name}_model.pkl')
        
        # Save scalers
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f'{directory}/{name}_scaler.pkl')
        
        # Save encoders
        for name, encoder in self.encoders.items():
            joblib.dump(encoder, f'{directory}/{name}_encoder.pkl')
        
        # Save feature columns
        with open(f'{directory}/feature_columns.json', 'w') as f:
            json.dump(self.feature_columns, f)
        
        logger.info(f"Models saved to {directory}/")
    
    def load_models(self, directory: str = 'models'):
        """
        Load trained models and preprocessors
        """
        import os
        
        # Load models
        model_files = ['contract_success_model.pkl', 'fraud_detection_model.pkl']
        for model_file in model_files:
            if os.path.exists(f'{directory}/{model_file}'):
                name = model_file.replace('_model.pkl', '')
                self.models[name] = joblib.load(f'{directory}/{model_file}')
        
        # Load scalers
        scaler_files = ['contract_success_scaler.pkl', 'fraud_detection_scaler.pkl']
        for scaler_file in scaler_files:
            if os.path.exists(f'{directory}/{scaler_file}'):
                name = scaler_file.replace('_scaler.pkl', '')
                self.scalers[name] = joblib.load(f'{directory}/{scaler_file}')
        
        # Load encoders
        encoder_files = ['state_encoder.pkl', 'primary_naics_encoder.pkl']
        for encoder_file in encoder_files:
            if os.path.exists(f'{directory}/{encoder_file}'):
                name = encoder_file.replace('_encoder.pkl', '')
                self.encoders[name] = joblib.load(f'{directory}/{encoder_file}')
        
        # Load feature columns
        if os.path.exists(f'{directory}/feature_columns.json'):
            with open(f'{directory}/feature_columns.json', 'r') as f:
                self.feature_columns = json.load(f)
        
        logger.info(f"Models loaded from {directory}/")

def main():
    """
    Run the ML prototype training
    """
    print("🚀 KBI Labs ML Prototype - Quick Start")
    print("=" * 50)
    
    # Initialize prototype
    ml_prototype = KBIProcurementMLPrototype()
    
    # Generate synthetic data (replace with your real data)
    print("📊 Generating synthetic procurement data...")
    data = ml_prototype.prepare_synthetic_data(n_samples=2000)
    
    # Prepare features
    print("⚙️ Preparing features...")
    features_df = ml_prototype.prepare_features(data)
    
    # Train contract success model
    print("🎯 Training contract success prediction model...")
    success_results = ml_prototype.train_contract_success_model(features_df)
    
    # Train fraud detection model
    print("🚨 Training fraud detection model...")
    fraud_results = ml_prototype.train_fraud_detection_model(features_df)
    
    # Save models
    print("💾 Saving models...")
    ml_prototype.save_models()
    
    # Print results
    print("\n🎉 Training Complete!")
    print(f"Contract Success Model Accuracy: {success_results['accuracy']:.3f}")
    print(f"Top 3 Important Features: {list(success_results['feature_importance'].keys())[:3]}")
    print(f"Fraud Detection Precision: {fraud_results['precision']:.3f}")
    print(f"Anomalies Detected: {fraud_results['anomalies_detected']}")
    
    # Test predictions
    print("\n🧪 Testing Predictions...")
    test_company = {
        'procurement_intelligence_score': 75,
        'gsa_calc_found': True,
        'fpds_found': True,
        'sam_opportunities_found': True,
        'sam_entity_found': True,
        'gsa_avg_rate': 120,
        'fpds_total_value': 250000,
        'fpds_total_contracts': 8,
        'sam_total_matches': 5,
        'agency_diversity': 3,
        'contractor_network_size': 15,
        'years_in_business': 10,
        'small_business': True,
        'veteran_owned': False,
        'woman_owned': True,
        'state': 'VA',
        'primary_naics': 541511
    }
    
    success_pred = ml_prototype.predict_contract_success(test_company)
    anomaly_pred = ml_prototype.detect_anomalies(test_company)
    
    print(f"Test Company Contract Success Probability: {success_pred['success_probability']:.3f}")
    print(f"Test Company Anomaly Risk: {anomaly_pred['risk_level']}")
    
    print("\n✅ ML Prototype Ready!")
    print("Next steps:")
    print("1. Run: streamlit run streamlit_ml_dashboard.py")
    print("2. Replace synthetic data with your real KBI Labs data")
    print("3. Integrate with your existing FastAPI endpoints")

if __name__ == "__main__":
    main()