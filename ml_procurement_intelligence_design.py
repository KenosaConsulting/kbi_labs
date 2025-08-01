#!/usr/bin/env python3
"""
ML-Enhanced Procurement Intelligence System Architecture
Combines KBI Labs' existing infrastructure with cutting-edge ML techniques
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from enum import Enum

# Framework imports (to be added to requirements)
try:
    from tpot import TPOTClassifier, TPOTRegressor
    import networkx as nx
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import torch
    import torch.nn as nn
    import torch_geometric
    from torch_geometric.nn import GCNConv, GATConv
    ADVANCED_ML_AVAILABLE = True
except ImportError:
    ADVANCED_ML_AVAILABLE = False
    logging.warning("Advanced ML libraries not installed. Run: pip install tpot networkx scikit-learn torch torch-geometric")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcurementMLTypes(Enum):
    """Types of ML models for procurement intelligence"""
    CONTRACT_SUCCESS_PREDICTION = "contract_success"
    FRAUD_DETECTION = "fraud_detection"
    OPPORTUNITY_MATCHING = "opportunity_matching"
    PRICING_OPTIMIZATION = "pricing_optimization"
    RISK_ASSESSMENT = "risk_assessment"
    SUPPLIER_NETWORK_ANALYSIS = "supplier_network"
    MARKET_FORECASTING = "market_forecasting"

@dataclass
class MLModelConfig:
    """Configuration for ML models"""
    model_type: ProcurementMLTypes
    features: List[str]
    target: str
    model_params: Dict[str, Any]
    training_data_sources: List[str]
    update_frequency: str  # 'daily', 'weekly', 'monthly'
    
class ProcurementGraphBuilder:
    """
    Builds heterogeneous graphs from procurement data for GNN analysis
    Novel insight: Multi-layer graph with companies, contracts, agencies, and opportunities
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_types = {
            'company': [],
            'contract': [],
            'agency': [],
            'opportunity': [],
            'naics': [],
            'location': []
        }
        
    def build_procurement_graph(self, 
                              companies_data: List[Dict],
                              contracts_data: List[Dict],
                              opportunities_data: List[Dict]) -> nx.MultiDiGraph:
        """
        Build comprehensive procurement ecosystem graph
        Novel: Combines historical performance with future opportunities
        """
        logger.info("Building procurement ecosystem graph...")
        
        # Add company nodes with rich features
        for company in companies_data:
            company_id = f"company_{company.get('UEI', company.get('Organization Name', ''))}"
            
            self.graph.add_node(company_id, 
                              node_type='company',
                              # Existing KBI Labs features
                              gsa_calc_found=company.get('gsa_calc_found', False),
                              fpds_found=company.get('fpds_found', False),
                              sam_opportunities_found=company.get('sam_opportunities_found', False),
                              procurement_intelligence_score=company.get('procurement_intelligence_score', 0),
                              
                              # Enhanced ML features
                              annual_contract_volume=company.get('fpds_total_value', 0),
                              avg_contract_size=company.get('fpds_avg_contract_value', 0),
                              agency_diversity=len(company.get('fpds_primary_agencies', [])),
                              opportunity_match_quality=company.get('sam_avg_match_score', 0),
                              
                              # Temporal features
                              years_active=self._calculate_years_active(company),
                              recent_activity_score=self._calculate_recent_activity(company),
                              
                              # Network features (to be calculated)
                              centrality_score=0,
                              clustering_coefficient=0)
            
            self.node_types['company'].append(company_id)
        
        # Add contract nodes and relationships
        self._add_contract_relationships(contracts_data)
        
        # Add opportunity nodes and predictions
        self._add_opportunity_relationships(opportunities_data)
        
        # Add NAICS and geographic clustering
        self._add_categorical_relationships(companies_data)
        
        # Calculate network metrics
        self._calculate_network_features()
        
        logger.info(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        return self.graph
    
    def _add_contract_relationships(self, contracts_data: List[Dict]):
        """Add contract nodes and company-contract-agency relationships"""
        for contract in contracts_data:
            contract_id = f"contract_{contract.get('piid', contract.get('Award ID', ''))}"
            
            # Contract node with features
            self.graph.add_node(contract_id,
                              node_type='contract',
                              value=contract.get('dollars_obligated', 0),
                              duration_days=self._calculate_contract_duration(contract),
                              competition_type=contract.get('competition_type', 'unknown'),
                              small_business=contract.get('small_business', 'N') == 'Y')
            
            # Company-Contract relationship
            company_id = f"company_{contract.get('vendor_name', '')}"
            if self.graph.has_node(company_id):
                self.graph.add_edge(company_id, contract_id, 
                                  relationship='awarded',
                                  award_date=contract.get('signed_date'),
                                  performance_score=self._calculate_performance_score(contract))
            
            # Agency-Contract relationship
            agency_id = f"agency_{contract.get('agency_name', '')}"
            if not self.graph.has_node(agency_id):
                self.graph.add_node(agency_id, node_type='agency')
                self.node_types['agency'].append(agency_id)
            
            self.graph.add_edge(agency_id, contract_id,
                              relationship='contracted',
                              naics_code=contract.get('naics_code'))
    
    def _add_opportunity_relationships(self, opportunities_data: List[Dict]):
        """Add future opportunity nodes and prediction relationships"""
        for opp in opportunities_data:
            opp_id = f"opportunity_{opp.get('noticeId', '')}"
            
            # Opportunity node
            self.graph.add_node(opp_id,
                              node_type='opportunity',
                              estimated_value=self._parse_value(opp.get('awardValue', 0)),
                              days_until_deadline=self._days_until_deadline(opp.get('responseDeadLine')),
                              competition_level=self._assess_competition_level(opp),
                              set_aside_type=opp.get('typeOfSetAsideDescription', 'None'))
            
            # Predict company-opportunity relationships
            predicted_matches = opp.get('potential_matches', [])
            for match in predicted_matches:
                company_id = f"company_{match.get('company_uei', '')}"
                if self.graph.has_node(company_id):
                    self.graph.add_edge(company_id, opp_id,
                                      relationship='potential_match',
                                      match_score=match.get('match_score', 0),
                                      bid_probability=match.get('bid_probability', 0))
    
    def _calculate_network_features(self):
        """Calculate advanced network features for each node"""
        logger.info("Calculating network centrality measures...")
        
        # Calculate various centrality measures
        centrality_measures = {
            'degree': nx.degree_centrality(self.graph),
            'betweenness': nx.betweenness_centrality(self.graph),
            'eigenvector': nx.eigenvector_centrality(self.graph, max_iter=1000),
            'pagerank': nx.pagerank(self.graph)
        }
        
        # Add centrality features to nodes
        for node in self.graph.nodes():
            self.graph.nodes[node].update({
                f'{measure}_centrality': centrality_measures[measure].get(node, 0)
                for measure in centrality_measures
            })
    
    def detect_procurement_communities(self) -> Dict[str, List[str]]:
        """
        Detect communities in procurement network
        Novel insight: Identify hidden supplier ecosystems and agency preferences
        """
        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()
        
        # Use multiple community detection algorithms
        communities = {}
        
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(undirected)
            
            # Group nodes by community
            for node, comm_id in partition.items():
                if comm_id not in communities:
                    communities[comm_id] = []
                communities[comm_id].append(node)
                
        except ImportError:
            logger.warning("python-louvain not installed for community detection")
            # Fallback to simple connected components
            communities = {i: list(comp) for i, comp in enumerate(nx.connected_components(undirected))}
        
        return communities

class AutomatedFeatureEngineering:
    """
    TPOT-inspired automated feature engineering for procurement data
    Novel: Specialized for government contracting domain
    """
    
    def __init__(self):
        self.feature_transformers = []
        self.generated_features = []
        
    def generate_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate sophisticated temporal features from procurement data"""
        logger.info("Generating temporal features...")
        
        # Contract timing features
        if 'signed_date' in df.columns:
            df['signed_date'] = pd.to_datetime(df['signed_date'])
            df['days_since_last_contract'] = (datetime.now() - df['signed_date']).dt.days
            df['contract_frequency'] = df.groupby('vendor_name')['signed_date'].transform(
                lambda x: len(x) / ((x.max() - x.min()).days / 365.25) if len(x) > 1 else 0
            )
            df['seasonal_quarter'] = df['signed_date'].dt.quarter
            df['fiscal_year'] = df['signed_date'].apply(lambda x: x.year if x.month >= 10 else x.year - 1)
        
        # Opportunity timing features  
        if 'responseDeadLine' in df.columns:
            df['responseDeadLine'] = pd.to_datetime(df['responseDeadLine'])
            df['response_urgency'] = (df['responseDeadLine'] - datetime.now()).dt.days
            df['weekend_deadline'] = df['responseDeadLine'].dt.weekday >= 5  # Weekend deadlines are suspicious
        
        return df
    
    def generate_network_features(self, df: pd.DataFrame, graph: nx.Graph) -> pd.DataFrame:
        """Generate network-based features from procurement graph"""
        logger.info("Generating network features...")
        
        # Map dataframe entities to graph nodes
        entity_to_node = {}
        for _, row in df.iterrows():
            if 'UEI' in row:
                entity_to_node[row.name] = f"company_{row['UEI']}"
            elif 'Organization Name' in row:
                entity_to_node[row.name] = f"company_{row['Organization Name']}"
        
        # Extract network features
        network_features = []
        for idx, node_id in entity_to_node.items():
            if graph.has_node(node_id):
                node_data = graph.nodes[node_id]
                network_features.append({
                    'index': idx,
                    'degree_centrality': node_data.get('degree_centrality', 0),
                    'betweenness_centrality': node_data.get('betweenness_centrality', 0),
                    'pagerank_score': node_data.get('pagerank_centrality', 0),
                    'clustering_coefficient': nx.clustering(graph, node_id) if graph.degree(node_id) > 1 else 0
                })
        
        # Merge network features back to dataframe
        network_df = pd.DataFrame(network_features).set_index('index')
        return df.join(network_df, how='left').fillna(0)
    
    def generate_competitive_intelligence_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate competitive landscape features"""
        logger.info("Generating competitive intelligence features...")
        
        # Market concentration features
        if 'naics_code' in df.columns:
            naics_stats = df.groupby('naics_code').agg({
                'dollars_obligated': ['count', 'sum', 'mean', 'std'],
                'vendor_name': 'nunique'
            }).fillna(0)
            
            # Flatten column names
            naics_stats.columns = ['_'.join(col).strip() for col in naics_stats.columns]
            
            # Market concentration ratio (HHI)
            def calculate_hhi(group):
                if len(group) == 0:
                    return 0
                total = group.sum()
                if total == 0:
                    return 0
                shares = (group / total) ** 2
                return shares.sum()
            
            naics_hhi = df.groupby('naics_code')['dollars_obligated'].apply(calculate_hhi)
            
            # Add market features to dataframe
            df = df.merge(naics_stats, left_on='naics_code', right_index=True, how='left')
            df = df.merge(naics_hhi.rename('market_concentration_hhi'), 
                         left_on='naics_code', right_index=True, how='left')
        
        # Competitor analysis features
        if 'vendor_name' in df.columns and 'agency_name' in df.columns:
            # Agency specialization score
            agency_vendor_counts = df.groupby(['agency_name', 'vendor_name']).size().unstack(fill_value=0)
            vendor_specialization = (agency_vendor_counts > 0).sum(axis=0) / len(agency_vendor_counts)
            
            df = df.merge(vendor_specialization.rename('agency_specialization_score'),
                         left_on='vendor_name', right_index=True, how='left')
        
        return df
    
    def automated_feature_discovery(self, X: pd.DataFrame, y: pd.Series, 
                                  problem_type: str = 'classification') -> Tuple[pd.DataFrame, Any]:
        """
        Use TPOT-inspired automated feature engineering and model selection
        Novel: Specialized for procurement prediction tasks
        """
        if not ADVANCED_ML_AVAILABLE:
            logger.error("TPOT not available. Install with: pip install tpot")
            return X, None
        
        logger.info(f"Starting automated ML pipeline optimization for {problem_type}...")
        
        # Configure TPOT for procurement domain
        tpot_config = {
            'sklearn.preprocessing.StandardScaler': {},
            'sklearn.preprocessing.RobustScaler': {},
            'sklearn.feature_selection.SelectKBest': {'k': range(1, min(100, X.shape[1] + 1))},
            'sklearn.ensemble.RandomForestClassifier': {'n_estimators': [10, 100], 'max_depth': [3, 5, None]},
            'sklearn.ensemble.GradientBoostingClassifier': {'n_estimators': [10, 100], 'learning_rate': [0.1, 0.01]},
            'sklearn.linear_model.LogisticRegression': {'C': [0.1, 1.0, 10.0]},
            'xgboost.XGBClassifier': {'n_estimators': [10, 100], 'max_depth': [3, 6]}
        }
        
        if problem_type == 'classification':
            tpot = TPOTClassifier(generations=5, population_size=20, cv=3,
                                random_state=42, verbosity=2, n_jobs=-1,
                                config_dict=tpot_config)
        else:
            tpot = TPOTRegressor(generations=5, population_size=20, cv=3,
                               random_state=42, verbosity=2, n_jobs=-1)
        
        # Fit TPOT
        tpot.fit(X, y)
        
        # Get optimized features
        optimized_X = tpot.transform(X)
        
        logger.info(f"TPOT optimization complete. Best CV score: {tpot.score(X, y):.4f}")
        logger.info(f"Best pipeline: {tpot.fitted_pipeline_}")
        
        return pd.DataFrame(optimized_X), tpot

class ProcurementAnomalyDetector:
    """
    Novel anomaly detection for procurement fraud and unusual patterns
    Combines multiple techniques for comprehensive analysis
    """
    
    def __init__(self):
        self.models = {}
        self.feature_scalers = {}
        
    def fit_anomaly_models(self, df: pd.DataFrame, features: List[str]):
        """Fit multiple anomaly detection models"""
        if not ADVANCED_ML_AVAILABLE:
            logger.error("Scikit-learn not available for anomaly detection")
            return
        
        logger.info("Training anomaly detection models...")
        
        X = df[features].fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.feature_scalers['isolation_forest'] = scaler
        
        # Isolation Forest for general anomalies
        iso_forest = IsolationForest(contamination=0.1, random_state=42, n_jobs=-1)
        iso_forest.fit(X_scaled)
        self.models['isolation_forest'] = iso_forest
        
        logger.info("Anomaly detection models trained")
    
    def detect_procurement_anomalies(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """Detect various types of procurement anomalies"""
        results = df.copy()
        
        if 'isolation_forest' in self.models:
            X = df[features].fillna(0)
            X_scaled = self.feature_scalers['isolation_forest'].transform(X)
            
            # Anomaly scores
            anomaly_scores = self.models['isolation_forest'].decision_function(X_scaled)
            is_anomaly = self.models['isolation_forest'].predict(X_scaled) == -1
            
            results['anomaly_score'] = anomaly_scores
            results['is_anomaly'] = is_anomaly
            
            # Specific anomaly types
            results['price_anomaly'] = self._detect_pricing_anomalies(df)
            results['timeline_anomaly'] = self._detect_timeline_anomalies(df)
            results['network_anomaly'] = self._detect_network_anomalies(df)
        
        return results
    
    def _detect_pricing_anomalies(self, df: pd.DataFrame) -> pd.Series:
        """Detect unusual pricing patterns"""
        if 'dollars_obligated' not in df.columns:
            return pd.Series([False] * len(df))
        
        # Z-score based pricing anomaly detection
        prices = df['dollars_obligated'].fillna(0)
        z_scores = np.abs((prices - prices.mean()) / prices.std())
        return z_scores > 3  # Values more than 3 standard deviations
    
    def _detect_timeline_anomalies(self, df: pd.DataFrame) -> pd.Series:
        """Detect unusual timeline patterns in contracts"""
        anomalies = [False] * len(df)
        
        if 'responseDeadLine' in df.columns:
            df['responseDeadLine'] = pd.to_datetime(df['responseDeadLine'])
            
            # Weekend deadlines (unusual)
            weekend_deadlines = df['responseDeadLine'].dt.weekday >= 5
            
            # Extremely short response times (< 7 days)
            short_response = (df['responseDeadLine'] - datetime.now()).dt.days < 7
            
            anomalies = weekend_deadlines | short_response
        
        return pd.Series(anomalies)
    
    def _detect_network_anomalies(self, df: pd.DataFrame) -> pd.Series:
        """Detect unusual network patterns (requires graph analysis)"""
        # Placeholder for network anomaly detection
        # Would require integration with graph analysis
        return pd.Series([False] * len(df))

class ProcurementIntelligenceOrchestrator:
    """
    Main orchestrator that combines all ML techniques for comprehensive insights
    Novel: Unified system leveraging existing KBI Labs infrastructure
    """
    
    def __init__(self, existing_enrichers: Dict[str, Any]):
        self.existing_enrichers = existing_enrichers
        self.graph_builder = ProcurementGraphBuilder()
        self.feature_engineer = AutomatedFeatureEngineering()
        self.anomaly_detector = ProcurementAnomalyDetector()
        self.models = {}
        
    async def comprehensive_intelligence_analysis(self, 
                                                companies_data: List[Dict],
                                                contracts_data: List[Dict],
                                                opportunities_data: List[Dict]) -> Dict[str, Any]:
        """
        Run comprehensive ML-enhanced procurement intelligence analysis
        """
        logger.info("🧠 Starting comprehensive ML-enhanced procurement intelligence...")
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'companies_analyzed': len(companies_data),
            'contracts_analyzed': len(contracts_data),
            'opportunities_analyzed': len(opportunities_data),
            'insights': {}
        }
        
        # Step 1: Build comprehensive procurement graph
        logger.info("📊 Building procurement ecosystem graph...")
        graph = self.graph_builder.build_procurement_graph(
            companies_data, contracts_data, opportunities_data
        )
        
        # Step 2: Detect procurement communities and networks
        logger.info("🌐 Analyzing procurement networks...")
        communities = self.graph_builder.detect_procurement_communities()
        results['insights']['procurement_communities'] = {
            f'community_{i}': {
                'size': len(members),
                'dominant_node_types': self._analyze_community_composition(members, graph)
            }
            for i, members in communities.items()
        }
        
        # Step 3: Advanced feature engineering
        logger.info("⚙️ Performing automated feature engineering...")
        companies_df = pd.DataFrame(companies_data)
        
        # Generate temporal features
        if not companies_df.empty:
            companies_df = self.feature_engineer.generate_temporal_features(companies_df)
            companies_df = self.feature_engineer.generate_network_features(companies_df, graph)
            companies_df = self.feature_engineer.generate_competitive_intelligence_features(companies_df)
        
        # Step 4: Contract success prediction
        logger.info("🎯 Training contract success prediction models...")
        if len(companies_df) > 10:  # Minimum data requirement
            success_insights = await self._predict_contract_success(companies_df)
            results['insights']['contract_success_predictions'] = success_insights
        
        # Step 5: Anomaly detection
        logger.info("🚨 Detecting procurement anomalies...")
        if len(companies_df) > 10:
            anomaly_insights = self._detect_comprehensive_anomalies(companies_df, contracts_data)
            results['insights']['anomaly_detection'] = anomaly_insights
        
        # Step 6: Market intelligence forecasting
        logger.info("📈 Generating market intelligence forecasts...")
        market_insights = self._generate_market_forecasts(companies_df, opportunities_data)
        results['insights']['market_forecasts'] = market_insights
        
        # Step 7: Novel procurement insights
        logger.info("💡 Generating novel procurement insights...")
        novel_insights = self._generate_novel_insights(graph, companies_df, contracts_data)
        results['insights']['novel_discoveries'] = novel_insights
        
        logger.info("🎉 Comprehensive ML analysis complete!")
        return results
    
    async def _predict_contract_success(self, companies_df: pd.DataFrame) -> Dict[str, Any]:
        """Predict contract success probability using automated ML"""
        
        # Create success target (companies with recent contracts)
        companies_df['contract_success'] = (
            (companies_df.get('fpds_found', False)) & 
            (companies_df.get('sam_opportunities_found', False))
        ).astype(int)
        
        # Select features for prediction
        feature_columns = [
            'procurement_intelligence_score', 'gsa_avg_rate', 'fpds_performance_score',
            'sam_avg_match_score', 'agency_diversity', 'recent_activity_score'
        ]
        
        # Filter available features
        available_features = [col for col in feature_columns if col in companies_df.columns]
        
        if len(available_features) < 3:
            return {'error': 'Insufficient features for contract success prediction'}
        
        X = companies_df[available_features].fillna(0)
        y = companies_df['contract_success']
        
        if y.sum() < 5:  # Need minimum positive examples
            return {'error': 'Insufficient positive examples for training'}
        
        # Use automated feature engineering if available
        if ADVANCED_ML_AVAILABLE:
            X_optimized, tpot_model = self.feature_engineer.automated_feature_discovery(X, y, 'classification')
            if tpot_model:
                self.models['contract_success'] = tpot_model
                
                return {
                    'model_score': tpot_model.score(X, y),
                    'best_pipeline': str(tpot_model.fitted_pipeline_),
                    'feature_importance': self._get_feature_importance(tpot_model, available_features),
                    'predictions': tpot_model.predict_proba(X)[:, 1].tolist()
                }
        
        # Fallback to simple analysis
        return {
            'correlation_analysis': X.corrwith(y).to_dict(),
            'success_rate_by_feature': self._analyze_success_by_features(X, y)
        }
    
    def _detect_comprehensive_anomalies(self, companies_df: pd.DataFrame, 
                                      contracts_data: List[Dict]) -> Dict[str, Any]:
        """Comprehensive anomaly detection across multiple dimensions"""
        
        # Prepare features for anomaly detection
        anomaly_features = [
            'procurement_intelligence_score', 'fpds_total_value', 'sam_total_matches'
        ]
        available_features = [col for col in anomaly_features if col in companies_df.columns]
        
        if len(available_features) < 2:
            return {'error': 'Insufficient features for anomaly detection'}
        
        # Fit and detect anomalies
        self.anomaly_detector.fit_anomaly_models(companies_df, available_features)
        anomalies_df = self.anomaly_detector.detect_procurement_anomalies(companies_df, available_features)
        
        # Analyze contract-level anomalies
        contracts_df = pd.DataFrame(contracts_data)
        contract_anomalies = self._detect_contract_anomalies(contracts_df)
        
        return {
            'company_anomalies': {
                'total_anomalies': anomalies_df['is_anomaly'].sum(),
                'anomaly_rate': anomalies_df['is_anomaly'].mean(),
                'top_anomalies': anomalies_df.nlargest(5, 'anomaly_score')[['Organization Name', 'anomaly_score']].to_dict('records')
            },
            'contract_anomalies': contract_anomalies,
            'anomaly_patterns': self._analyze_anomaly_patterns(anomalies_df)
        }
    
    def _generate_market_forecasts(self, companies_df: pd.DataFrame, 
                                 opportunities_data: List[Dict]) -> Dict[str, Any]:
        """Generate market intelligence and forecasting insights"""
        
        forecasts = {}
        
        # Opportunity trend analysis
        if opportunities_data:
            opps_df = pd.DataFrame(opportunities_data)
            
            # Analyze opportunity distribution by NAICS
            if 'naicsCode' in opps_df.columns:
                naics_trends = opps_df.groupby('naicsCode').agg({
                    'awardValue': ['count', 'sum', 'mean'],
                    'responseDeadLine': lambda x: pd.to_datetime(x).dt.days_until_deadline.mean()
                }).fillna(0)
                
                forecasts['naics_opportunity_trends'] = naics_trends.to_dict()
            
            # Set-aside analysis
            if 'typeOfSetAsideDescription' in opps_df.columns:
                setaside_analysis = opps_df['typeOfSetAsideDescription'].value_counts().to_dict()
                forecasts['setaside_distribution'] = setaside_analysis
        
        # Company competitiveness trends
        if not companies_df.empty and 'procurement_intelligence_score' in companies_df.columns:
            score_distribution = companies_df['procurement_intelligence_score'].describe().to_dict()
            forecasts['competitiveness_distribution'] = score_distribution
        
        return forecasts
    
    def _generate_novel_insights(self, graph: nx.Graph, companies_df: pd.DataFrame, 
                               contracts_data: List[Dict]) -> Dict[str, Any]:
        """Generate novel insights unique to procurement intelligence"""
        
        insights = {}
        
        # Network-based insights
        if graph.number_of_nodes() > 0:
            # Identify key broker companies (high betweenness centrality)
            company_nodes = [n for n in graph.nodes() if graph.nodes[n].get('node_type') == 'company']
            if company_nodes:
                brokers = sorted(
                    [(n, graph.nodes[n].get('betweenness_centrality', 0)) for n in company_nodes],
                    key=lambda x: x[1], reverse=True
                )[:5]
                
                insights['key_brokers'] = [
                    {'company': broker[0], 'broker_score': broker[1]} 
                    for broker in brokers
                ]
        
        # Competitive landscape insights
        if not companies_df.empty:
            # Identify companies with unusual competitive positions
            if 'gsa_competitive_position' in companies_df.columns:
                position_analysis = companies_df['gsa_competitive_position'].value_counts().to_dict()
                insights['competitive_landscape'] = position_analysis
        
        # Temporal pattern insights
        if contracts_data:
            contracts_df = pd.DataFrame(contracts_data)
            if 'signed_date' in contracts_df.columns:
                contracts_df['signed_date'] = pd.to_datetime(contracts_df['signed_date'])
                
                # Seasonal patterns
                seasonal_patterns = contracts_df.groupby(
                    contracts_df['signed_date'].dt.quarter
                )['dollars_obligated'].sum().to_dict()
                
                insights['seasonal_contracting_patterns'] = seasonal_patterns
        
        return insights
    
    def _analyze_community_composition(self, members: List[str], graph: nx.Graph) -> Dict[str, int]:
        """Analyze the composition of a procurement community"""
        composition = {}
        for member in members:
            if graph.has_node(member):
                node_type = graph.nodes[member].get('node_type', 'unknown')
                composition[node_type] = composition.get(node_type, 0) + 1
        return composition
    
    def _get_feature_importance(self, model: Any, feature_names: List[str]) -> Dict[str, float]:
        """Extract feature importance from trained model"""
        try:
            if hasattr(model.fitted_pipeline_, 'feature_importances_'):
                importance = model.fitted_pipeline_.feature_importances_
                return dict(zip(feature_names[:len(importance)], importance))
        except:
            pass
        return {}
    
    def _analyze_success_by_features(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Analyze success rates by feature quartiles"""
        analysis = {}
        for col in X.columns:
            quartiles = pd.qcut(X[col], q=4, duplicates='drop')
            success_by_quartile = y.groupby(quartiles).mean().to_dict()
            analysis[col] = success_by_quartile
        return analysis
    
    def _detect_contract_anomalies(self, contracts_df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies specifically in contract data"""
        if contracts_df.empty:
            return {'error': 'No contract data available'}
        
        anomalies = {}
        
        # Price anomalies
        if 'dollars_obligated' in contracts_df.columns:
            prices = contracts_df['dollars_obligated'].fillna(0)
            price_z_scores = np.abs((prices - prices.mean()) / prices.std())
            anomalies['price_anomalies'] = {
                'count': (price_z_scores > 3).sum(),
                'top_anomalies': contracts_df[price_z_scores > 3].nlargest(3, 'dollars_obligated')[
                    ['vendor_name', 'dollars_obligated']
                ].to_dict('records')
            }
        
        return anomalies
    
    def _analyze_anomaly_patterns(self, anomalies_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in detected anomalies"""
        patterns = {}
        
        if 'is_anomaly' in anomalies_df.columns:
            anomaly_subset = anomalies_df[anomalies_df['is_anomaly']]
            
            # Geographic patterns
            if 'Physical Address State' in anomaly_subset.columns:
                state_patterns = anomaly_subset['Physical Address State'].value_counts().to_dict()
                patterns['geographic_anomaly_concentration'] = state_patterns
            
            # Industry patterns
            if 'Primary NAICS Code' in anomaly_subset.columns:
                naics_patterns = anomaly_subset['Primary NAICS Code'].value_counts().to_dict()
                patterns['industry_anomaly_concentration'] = naics_patterns
        
        return patterns

# Usage example and integration points
async def integrate_with_kbi_labs(unified_enricher, companies_data: List[Dict]) -> Dict[str, Any]:
    """
    Integration function showing how to combine existing KBI Labs enrichment
    with new ML-enhanced procurement intelligence
    """
    
    # Step 1: Run existing KBI Labs enrichment
    enriched_companies = []
    for company in companies_data:
        enriched = await unified_enricher.enrich_company_comprehensive(company)
        enriched_companies.append(enriched)
    
    # Step 2: Generate synthetic contract and opportunity data for ML analysis
    # (In production, this would come from your APIs)
    contracts_data = generate_synthetic_contracts(enriched_companies)
    opportunities_data = generate_synthetic_opportunities(enriched_companies)
    
    # Step 3: Run ML-enhanced analysis
    ml_orchestrator = ProcurementIntelligenceOrchestrator(
        existing_enrichers={'unified_enricher': unified_enricher}
    )
    
    ml_insights = await ml_orchestrator.comprehensive_intelligence_analysis(
        enriched_companies, contracts_data, opportunities_data
    )
    
    return {
        'enriched_companies': enriched_companies,
        'ml_insights': ml_insights,
        'integration_timestamp': datetime.now().isoformat()
    }

def generate_synthetic_contracts(companies: List[Dict]) -> List[Dict]:
    """Generate synthetic contract data for ML training (replace with real data)"""
    # Placeholder - in production, use your FPDS/USASpending data
    return []

def generate_synthetic_opportunities(companies: List[Dict]) -> List[Dict]:
    """Generate synthetic opportunity data for ML training (replace with real data)"""  
    # Placeholder - in production, use your SAM.gov opportunities data
    return []

if __name__ == "__main__":
    logger.info("🚀 ML-Enhanced Procurement Intelligence System initialized")
    logger.info(f"Advanced ML libraries available: {ADVANCED_ML_AVAILABLE}")
    
    if not ADVANCED_ML_AVAILABLE:
        print("\n📦 To enable full ML capabilities, install:")
        print("pip install tpot networkx scikit-learn torch torch-geometric python-louvain xgboost")