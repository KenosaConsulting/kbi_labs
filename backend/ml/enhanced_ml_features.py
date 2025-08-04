#!/usr/bin/env python3
"""
Enhanced ML Features with Multi-Source Government Data
Advanced ML models leveraging budget, regulatory, and dataset intelligence
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EnhancedMLPrediction:
    """Enhanced ML prediction with multi-source intelligence"""
    contract_success_probability: float
    budget_timing_score: float
    regulatory_impact_score: float
    strategic_alignment_score: float
    competitive_intelligence_score: float
    overall_opportunity_score: float
    confidence_level: str
    key_factors: List[str]
    recommendations: List[str]

class EnhancedMLProcessor:
    """
    Enhanced ML Processor with Multi-Source Government Data
    
    New Features:
    1. Budget Timing Predictor
    2. Regulatory Impact Scorer
    3. Strategic Alignment Model
    4. Competitive Intelligence Analyzer
    5. Multi-Source Opportunity Ranker
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = []
        
        # Enhanced feature categories
        self.traditional_features = [
            'procurement_intelligence_score', 'gsa_calc_found', 'fpds_found',
            'sam_opportunities_found', 'sam_entity_found', 'gsa_avg_rate',
            'fpds_total_value', 'fpds_total_contracts', 'sam_total_matches',
            'agency_diversity', 'contractor_network_size', 'years_in_business'
        ]
        
        self.budget_features = [
            'agency_budget_remaining', 'agency_spending_rate', 'budget_urgency_score',
            'fiscal_year_progress', 'budget_flush_proximity', 'agency_budget_authority'
        ]
        
        self.regulatory_features = [
            'recent_regulatory_changes', 'policy_impact_score', 'regulatory_uncertainty',
            'compliance_complexity', 'regulatory_opportunity_score'
        ]
        
        self.dataset_features = [
            'relevant_datasets_count', 'data_richness_score', 'intelligence_availability',
            'market_transparency_score', 'competitive_data_advantage'
        ]
        
        self.strategic_features = [
            'agency_strategic_priority_alignment', 'performance_gap_opportunity',
            'mission_criticality_score', 'innovation_priority_score'
        ]
    
    def generate_enhanced_synthetic_data(self, n_samples: int = 2000) -> pd.DataFrame:
        """Generate synthetic data with enhanced multi-source features"""
        logger.info(f"Generating {n_samples} enhanced synthetic records...")
        
        np.random.seed(42)
        
        # Traditional features (existing)
        data = {
            'procurement_intelligence_score': np.random.normal(50, 20, n_samples),
            'gsa_calc_found': np.random.choice([True, False], n_samples, p=[0.3, 0.7]),
            'fpds_found': np.random.choice([True, False], n_samples, p=[0.4, 0.6]),
            'sam_opportunities_found': np.random.choice([True, False], n_samples, p=[0.2, 0.8]),
            'sam_entity_found': np.random.choice([True, False], n_samples, p=[0.6, 0.4]),
            'gsa_avg_rate': np.random.exponential(100, n_samples),
            'fpds_total_value': np.random.exponential(50000, n_samples),
            'fpds_total_contracts': np.random.poisson(5, n_samples),
            'sam_total_matches': np.random.poisson(3, n_samples),
            'agency_diversity': np.random.poisson(2, n_samples),
            'contractor_network_size': np.random.poisson(10, n_samples),
            'years_in_business': np.random.uniform(1, 50, n_samples),
        }
        
        # NEW: Budget Intelligence Features
        data.update({
            'agency_budget_remaining': np.random.exponential(1000000, n_samples),  # Remaining budget
            'agency_spending_rate': np.random.uniform(0.1, 2.0, n_samples),  # Monthly spending rate
            'budget_urgency_score': np.random.exponential(1.0, n_samples),  # Urgency to spend
            'fiscal_year_progress': np.random.uniform(0.1, 0.95, n_samples),  # How far into fiscal year
            'budget_flush_proximity': np.random.uniform(0, 1, n_samples),  # Proximity to budget flush
            'agency_budget_authority': np.random.exponential(5000000, n_samples),  # Total budget authority
        })
        
        # NEW: Regulatory Intelligence Features  
        data.update({
            'recent_regulatory_changes': np.random.poisson(2, n_samples),  # Recent reg changes
            'policy_impact_score': np.random.uniform(0, 10, n_samples),  # Policy impact on procurement
            'regulatory_uncertainty': np.random.uniform(0, 1, n_samples),  # Regulatory uncertainty
            'compliance_complexity': np.random.uniform(1, 5, n_samples),  # Compliance complexity
            'regulatory_opportunity_score': np.random.uniform(0, 10, n_samples),  # Reg-driven opportunities
        })
        
        # NEW: Dataset Intelligence Features
        data.update({
            'relevant_datasets_count': np.random.poisson(5, n_samples),  # Relevant datasets available
            'data_richness_score': np.random.uniform(0, 10, n_samples),  # Data richness for intelligence
            'intelligence_availability': np.random.uniform(0, 1, n_samples),  # Intelligence data availability
            'market_transparency_score': np.random.uniform(0, 1, n_samples),  # Market transparency
            'competitive_data_advantage': np.random.uniform(0, 1, n_samples),  # Competitive data advantage
        })
        
        # NEW: Strategic Intelligence Features
        data.update({
            'agency_strategic_priority_alignment': np.random.uniform(0, 1, n_samples),  # Strategic alignment
            'performance_gap_opportunity': np.random.uniform(0, 1, n_samples),  # Performance gaps
            'mission_criticality_score': np.random.uniform(0, 10, n_samples),  # Mission criticality
            'innovation_priority_score': np.random.uniform(0, 10, n_samples),  # Innovation priority
        })
        
        # Additional context features
        data.update({
            'state': np.random.choice(['CA', 'TX', 'NY', 'FL', 'VA', 'MD', 'DC'], n_samples),
            'primary_naics': np.random.choice([541511, 541512, 541519, 541330, 541990], n_samples),
            'small_business': np.random.choice([True, False], n_samples, p=[0.7, 0.3]),
            'veteran_owned': np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
            'woman_owned': np.random.choice([True, False], n_samples, p=[0.15, 0.85]),
        })
        
        df = pd.DataFrame(data)
        
        # Create enhanced target variables
        
        # 1. Contract Success (enhanced formula with new features)
        success_probability = (
            (df['procurement_intelligence_score'] / 100) * 0.20 +
            (df['gsa_calc_found'].astype(int)) * 0.10 +
            (df['fpds_found'].astype(int)) * 0.10 +
            (df['budget_urgency_score'] / 5) * 0.15 +  # NEW: Budget urgency impact
            (df['regulatory_opportunity_score'] / 10) * 0.10 +  # NEW: Regulatory opportunity
            (df['agency_strategic_priority_alignment']) * 0.15 +  # NEW: Strategic alignment
            (df['data_richness_score'] / 10) * 0.10 +  # NEW: Data intelligence
            np.random.normal(0, 0.1, n_samples)  # Noise
        )
        
        success_probability = np.clip(success_probability, 0, 1)
        df['contract_success'] = (success_probability > 0.5).astype(int)
        
        # 2. Budget Timing Score (0-1, higher = better timing)
        df['optimal_budget_timing'] = np.clip(
            (df['budget_urgency_score'] / 3) * 0.4 +
            (df['budget_flush_proximity']) * 0.3 +
            (1 - df['fiscal_year_progress']) * 0.3,
            0, 1
        )
        
        # 3. Regulatory Impact Score (0-1, higher = more regulatory opportunity)
        df['regulatory_opportunity'] = np.clip(
            (df['regulatory_opportunity_score'] / 10) * 0.5 +
            (df['policy_impact_score'] / 10) * 0.3 +
            (1 - df['regulatory_uncertainty']) * 0.2,
            0, 1
        )
        
        # 4. Strategic Alignment Score (0-1, higher = better alignment)
        df['strategic_alignment'] = np.clip(
            (df['agency_strategic_priority_alignment']) * 0.4 +
            (df['performance_gap_opportunity']) * 0.3 +
            (df['mission_criticality_score'] / 10) * 0.3,
            0, 1
        )
        
        # 5. Competitive Intelligence Score (0-1, higher = better competitive position)
        df['competitive_advantage'] = np.clip(
            (df['competitive_data_advantage']) * 0.3 +
            (df['market_transparency_score']) * 0.2 +
            (df['intelligence_availability']) * 0.2 +
            (df['data_richness_score'] / 10) * 0.3,
            0, 1
        )
        
        logger.info(f"Generated enhanced data shape: {df.shape}")
        logger.info(f"Contract success rate: {df['contract_success'].mean():.2f}")
        logger.info(f"Average budget timing score: {df['optimal_budget_timing'].mean():.2f}")
        logger.info(f"Average regulatory opportunity: {df['regulatory_opportunity'].mean():.2f}")
        
        return df
    
    def prepare_enhanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare enhanced features for ML models"""
        logger.info("Preparing enhanced features for ML models...")
        
        df_features = df.copy()
        
        # All numerical features (traditional + new)
        numerical_features = (
            self.traditional_features + self.budget_features + 
            self.regulatory_features + self.dataset_features + self.strategic_features
        )
        
        # Fill missing values
        for col in numerical_features:
            if col in df_features.columns:
                df_features[col] = df_features[col].fillna(df_features[col].median())
        
        # Boolean features
        boolean_features = [
            'gsa_calc_found', 'fpds_found', 'sam_opportunities_found',
            'sam_entity_found', 'small_business', 'veteran_owned', 'woman_owned'
        ]
        
        for col in boolean_features:
            if col in df_features.columns:
                df_features[col] = df_features[col].astype(int)
        
        # Categorical features
        if 'state' in df_features.columns:
            if 'state' not in self.encoders:
                self.encoders['state'] = LabelEncoder()
                df_features['state_encoded'] = self.encoders['state'].fit_transform(df_features['state'])
            else:
                df_features['state_encoded'] = self.encoders['state'].transform(df_features['state'])
        
        if 'primary_naics' in df_features.columns:
            if 'primary_naics' not in self.encoders:
                self.encoders['primary_naics'] = LabelEncoder()
                df_features['naics_encoded'] = self.encoders['primary_naics'].fit_transform(df_features['primary_naics'])
            else:
                df_features['naics_encoded'] = self.encoders['primary_naics'].transform(df_features['primary_naics'])
        
        # Enhanced feature engineering
        
        # Budget intelligence features
        if 'agency_budget_remaining' in df_features.columns and 'agency_spending_rate' in df_features.columns:
            df_features['months_of_budget_remaining'] = df_features['agency_budget_remaining'] / (df_features['agency_spending_rate'] * 30000 + 1)
        
        # Regulatory timing features
        if 'recent_regulatory_changes' in df_features.columns and 'policy_impact_score' in df_features.columns:
            df_features['regulatory_momentum'] = df_features['recent_regulatory_changes'] * df_features['policy_impact_score'] / 10
        
        # Strategic opportunity features
        if 'agency_strategic_priority_alignment' in df_features.columns and 'performance_gap_opportunity' in df_features.columns:
            df_features['strategic_opportunity_score'] = (
                df_features['agency_strategic_priority_alignment'] * 0.6 + 
                df_features['performance_gap_opportunity'] * 0.4
            )
        
        # Competitive advantage features
        if 'data_richness_score' in df_features.columns and 'competitive_data_advantage' in df_features.columns:
            df_features['intelligence_advantage'] = (
                df_features['data_richness_score'] / 10 * 0.7 + 
                df_features['competitive_data_advantage'] * 0.3
            )
        
        # Multi-source composite features
        budget_timing_features = ['budget_urgency_score', 'fiscal_year_progress', 'budget_flush_proximity']
        available_budget_features = [f for f in budget_timing_features if f in df_features.columns]
        if available_budget_features:
            df_features['composite_budget_score'] = df_features[available_budget_features].mean(axis=1)
        
        regulatory_features_list = ['policy_impact_score', 'regulatory_opportunity_score']
        available_reg_features = [f for f in regulatory_features_list if f in df_features.columns]
        if available_reg_features:
            df_features['composite_regulatory_score'] = df_features[available_reg_features].mean(axis=1)
        
        # Select final feature columns
        base_features = [col for col in numerical_features + boolean_features if col in df_features.columns]
        engineered_features = [
            'state_encoded', 'naics_encoded', 'months_of_budget_remaining',
            'regulatory_momentum', 'strategic_opportunity_score', 'intelligence_advantage',
            'composite_budget_score', 'composite_regulatory_score'
        ]
        available_engineered = [f for f in engineered_features if f in df_features.columns]
        
        self.feature_columns = base_features + available_engineered
        
        logger.info(f"Prepared {len(self.feature_columns)} enhanced features")
        
        # Return features plus targets
        target_columns = ['contract_success', 'optimal_budget_timing', 'regulatory_opportunity', 
                         'strategic_alignment', 'competitive_advantage']
        available_targets = [t for t in target_columns if t in df_features.columns]
        
        return df_features[self.feature_columns + available_targets]
    
    def train_enhanced_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train enhanced ML models with multi-source data"""
        logger.info("Training enhanced ML models...")
        
        X = df[self.feature_columns]
        results = {}
        
        # 1. Enhanced Contract Success Model
        if 'contract_success' in df.columns:
            y_success = df['contract_success']
            X_train, X_test, y_train, y_test = train_test_split(X, y_success, test_size=0.2, random_state=42)
            
            # Scale features
            self.scalers['contract_success'] = StandardScaler()
            X_train_scaled = self.scalers['contract_success'].fit_transform(X_train)
            X_test_scaled = self.scalers['contract_success'].transform(X_test)
            
            # Train enhanced model
            self.models['contract_success'] = RandomForestClassifier(
                n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
            )
            self.models['contract_success'].fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.models['contract_success'].predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Feature importance
            feature_importance = dict(zip(self.feature_columns, self.models['contract_success'].feature_importances_))
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            results['contract_success'] = {
                'accuracy': accuracy,
                'model_type': 'Enhanced RandomForest',
                'feature_importance': feature_importance
            }
        
        # 2. Budget Timing Model
        if 'optimal_budget_timing' in df.columns:
            y_timing = df['optimal_budget_timing']
            X_train, X_test, y_train, y_test = train_test_split(X, y_timing, test_size=0.2, random_state=42)
            
            self.scalers['budget_timing'] = StandardScaler()
            X_train_scaled = self.scalers['budget_timing'].fit_transform(X_train)
            X_test_scaled = self.scalers['budget_timing'].transform(X_test)
            
            self.models['budget_timing'] = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, random_state=42
            )
            self.models['budget_timing'].fit(X_train_scaled, y_train)
            
            y_pred = self.models['budget_timing'].predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            results['budget_timing'] = {
                'mse': mse,
                'rmse': np.sqrt(mse),
                'model_type': 'GradientBoosting'
            }
        
        # 3. Regulatory Opportunity Model
        if 'regulatory_opportunity' in df.columns:
            y_regulatory = df['regulatory_opportunity']
            X_train, X_test, y_train, y_test = train_test_split(X, y_regulatory, test_size=0.2, random_state=42)
            
            self.scalers['regulatory'] = StandardScaler()
            X_train_scaled = self.scalers['regulatory'].fit_transform(X_train)
            X_test_scaled = self.scalers['regulatory'].transform(X_test)
            
            self.models['regulatory'] = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, random_state=42
            )
            self.models['regulatory'].fit(X_train_scaled, y_train)
            
            y_pred = self.models['regulatory'].predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            results['regulatory'] = {
                'mse': mse,
                'rmse': np.sqrt(mse),
                'model_type': 'GradientBoosting'
            }
        
        # 4. Strategic Alignment Model
        if 'strategic_alignment' in df.columns:
            y_strategic = df['strategic_alignment']
            X_train, X_test, y_train, y_test = train_test_split(X, y_strategic, test_size=0.2, random_state=42)
            
            self.scalers['strategic'] = StandardScaler()
            X_train_scaled = self.scalers['strategic'].fit_transform(X_train)
            X_test_scaled = self.scalers['strategic'].transform(X_test)
            
            self.models['strategic'] = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, random_state=42
            )
            self.models['strategic'].fit(X_train_scaled, y_train)
            
            y_pred = self.models['strategic'].predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            results['strategic'] = {
                'mse': mse,
                'rmse': np.sqrt(mse),
                'model_type': 'GradientBoosting'
            }
        
        logger.info(f"Trained {len(results)} enhanced ML models")
        return results
    
    def predict_enhanced_intelligence(self, company_data: Dict[str, Any]) -> EnhancedMLPrediction:
        """Generate enhanced ML predictions with multi-source intelligence"""
        
        # Convert to DataFrame and prepare features
        df = pd.DataFrame([company_data])
        
        # Prepare features (simplified for single prediction)
        features = []
        for col in self.feature_columns:
            if col in df.columns:
                features.append(df[col].iloc[0])
            else:
                # Use reasonable defaults for missing features
                if 'budget' in col:
                    features.append(0.5)  # Medium budget score
                elif 'regulatory' in col:
                    features.append(0.3)  # Low regulatory impact
                elif 'strategic' in col:
                    features.append(0.4)  # Medium strategic alignment
                else:
                    features.append(0)  # Default to 0
        
        # Make predictions
        predictions = {}
        
        # Contract success prediction
        if 'contract_success' in self.models and 'contract_success' in self.scalers:
            features_scaled = self.scalers['contract_success'].transform([features])
            prob = self.models['contract_success'].predict_proba(features_scaled)[0][1]
            predictions['contract_success'] = prob
        else:
            predictions['contract_success'] = 0.5
        
        # Budget timing prediction
        if 'budget_timing' in self.models and 'budget_timing' in self.scalers:
            features_scaled = self.scalers['budget_timing'].transform([features])
            score = self.models['budget_timing'].predict(features_scaled)[0]
            predictions['budget_timing'] = max(0, min(1, score))
        else:
            predictions['budget_timing'] = 0.5
        
        # Regulatory opportunity prediction
        if 'regulatory' in self.models and 'regulatory' in self.scalers:
            features_scaled = self.scalers['regulatory'].transform([features])
            score = self.models['regulatory'].predict(features_scaled)[0]
            predictions['regulatory'] = max(0, min(1, score))
        else:
            predictions['regulatory'] = 0.3
        
        # Strategic alignment prediction
        if 'strategic' in self.models and 'strategic' in self.scalers:
            features_scaled = self.scalers['strategic'].transform([features])
            score = self.models['strategic'].predict(features_scaled)[0]
            predictions['strategic'] = max(0, min(1, score))
        else:
            predictions['strategic'] = 0.4
        
        # Competitive intelligence (composite score)
        competitive_score = (
            predictions['contract_success'] * 0.3 +
            predictions['budget_timing'] * 0.25 +
            predictions['regulatory'] * 0.25 +
            predictions['strategic'] * 0.2
        )
        
        # Overall opportunity score
        overall_score = (
            predictions['contract_success'] * 0.35 +
            predictions['budget_timing'] * 0.20 +
            predictions['regulatory'] * 0.15 +
            predictions['strategic'] * 0.20 +
            competitive_score * 0.10
        )
        
        # Determine confidence level
        scores = list(predictions.values())
        score_variance = np.var(scores)
        
        if overall_score > 0.8 and score_variance < 0.05:
            confidence = "Very High"
        elif overall_score > 0.6 and score_variance < 0.1:
            confidence = "High"
        elif overall_score > 0.4 and score_variance < 0.2:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Generate key factors and recommendations
        key_factors = []
        recommendations = []
        
        if predictions['budget_timing'] > 0.7:
            key_factors.append("Excellent budget timing")
            recommendations.append("Accelerate proposal preparation - optimal budget window")
        elif predictions['budget_timing'] < 0.3:
            key_factors.append("Poor budget timing")
            recommendations.append("Consider delaying until next fiscal period")
        
        if predictions['regulatory'] > 0.6:
            key_factors.append("Strong regulatory tailwinds")
            recommendations.append("Emphasize regulatory compliance and innovation")
        
        if predictions['strategic'] > 0.7:
            key_factors.append("High strategic alignment")
            recommendations.append("Highlight mission alignment in proposals")
        
        if overall_score > 0.7:
            recommendations.append("HIGH PRIORITY: Pursue aggressively with full resources")
        elif overall_score > 0.5:
            recommendations.append("MEDIUM PRIORITY: Solid opportunity worth pursuing")
        else:
            recommendations.append("LOW PRIORITY: Monitor for improved conditions")
        
        return EnhancedMLPrediction(
            contract_success_probability=predictions['contract_success'],
            budget_timing_score=predictions['budget_timing'],
            regulatory_impact_score=predictions['regulatory'],
            strategic_alignment_score=predictions['strategic'],
            competitive_intelligence_score=competitive_score,
            overall_opportunity_score=overall_score,
            confidence_level=confidence,
            key_factors=key_factors,
            recommendations=recommendations
        )

def test_enhanced_ml_features():
    """Test enhanced ML features"""
    print("🤖 Testing Enhanced ML Features...")
    
    # Initialize processor
    ml_processor = EnhancedMLProcessor()
    
    # Generate enhanced synthetic data
    print("📊 Generating enhanced synthetic data...")
    data = ml_processor.generate_enhanced_synthetic_data(n_samples=1000)
    print(f"✅ Generated data with {data.shape[1]} features")
    
    # Prepare features
    print("⚙️ Preparing enhanced features...")
    features_df = ml_processor.prepare_enhanced_features(data)
    print(f"✅ Prepared {len(ml_processor.feature_columns)} features for ML")
    
    # Train enhanced models
    print("🎯 Training enhanced ML models...")
    results = ml_processor.train_enhanced_models(features_df)
    print(f"✅ Trained {len(results)} enhanced models")
    
    # Display results
    for model_name, result in results.items():
        print(f"\n{model_name.replace('_', ' ').title()} Model:")
        if 'accuracy' in result:
            print(f"  Accuracy: {result['accuracy']:.3f}")
        if 'rmse' in result:
            print(f"  RMSE: {result['rmse']:.3f}")
        print(f"  Model Type: {result['model_type']}")
    
    # Test enhanced prediction
    print("\n🔮 Testing enhanced prediction...")
    test_company = {
        'procurement_intelligence_score': 75,
        'gsa_calc_found': True,
        'fpds_found': True,
        'sam_opportunities_found': True,
        'sam_entity_found': True,
        'agency_budget_remaining': 2000000,  # NEW: Budget intelligence
        'budget_urgency_score': 2.5,
        'policy_impact_score': 7.0,  # NEW: Regulatory intelligence
        'regulatory_opportunity_score': 8.0,
        'agency_strategic_priority_alignment': 0.8,  # NEW: Strategic intelligence
        'data_richness_score': 9.0,  # NEW: Dataset intelligence
        'competitive_data_advantage': 0.7
    }
    
    prediction = ml_processor.predict_enhanced_intelligence(test_company)
    
    print(f"Enhanced ML Prediction Results:")
    print(f"  Contract Success Probability: {prediction.contract_success_probability:.3f}")
    print(f"  Budget Timing Score: {prediction.budget_timing_score:.3f}")
    print(f"  Regulatory Impact Score: {prediction.regulatory_impact_score:.3f}")
    print(f"  Strategic Alignment Score: {prediction.strategic_alignment_score:.3f}")
    print(f"  Overall Opportunity Score: {prediction.overall_opportunity_score:.3f}")
    print(f"  Confidence Level: {prediction.confidence_level}")
    
    print(f"\n📋 Key Factors ({len(prediction.key_factors)}):")
    for factor in prediction.key_factors:
        print(f"  • {factor}")
    
    print(f"\n💡 Recommendations ({len(prediction.recommendations)}):")
    for rec in prediction.recommendations:
        print(f"  • {rec}")
    
    print("\n✅ Enhanced ML features testing complete!")
    return True

if __name__ == "__main__":
    test_enhanced_ml_features()