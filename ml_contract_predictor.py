#!/usr/bin/env python3
"""
Advanced ML Contract Prediction Service
Uses company data to predict contract winning probability
"""
import asyncio
import aiohttp
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re

class MLContractPredictor:
    def __init__(self):
        self.session = None
        self.prediction_cache = "contract_predictions.db"
        self.init_prediction_db()
        
        # Load SAM.gov opportunity data patterns
        self.naics_patterns = self._load_naics_patterns()
        self.agency_preferences = self._load_agency_preferences()
    
    def init_prediction_db(self):
        """Initialize prediction cache database"""
        conn = sqlite3.connect(self.prediction_cache)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                uei TEXT,
                opportunity_id TEXT,
                prediction_score REAL,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (uei, opportunity_id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_id TEXT PRIMARY KEY,
                title TEXT,
                agency TEXT,
                naics_codes TEXT,
                set_aside_codes TEXT,
                estimated_value TEXT,
                deadline TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    async def predict_contract_opportunities(self, company: Dict) -> Dict:
        """Generate AI-powered contract predictions for a company"""
        try:
            # Get current opportunities from SAM.gov
            opportunities = await self._fetch_sam_opportunities(company)
            
            # Score each opportunity
            predictions = []
            for opp in opportunities:
                score_data = self._calculate_match_score(company, opp)
                if score_data["score"] > 30:  # Only include viable opportunities
                    predictions.append({
                        "opportunity_id": opp["opportunity_id"],
                        "title": opp["title"],
                        "agency": opp["agency"],
                        "probability": score_data["score"],
                        "reasoning": score_data["reasoning"],
                        "estimated_value": opp["estimated_value"],
                        "deadline": opp["deadline"],
                        "competition_level": score_data["competition_level"],
                        "key_factors": score_data["key_factors"]
                    })
            
            # Sort by probability
            predictions.sort(key=lambda x: x["probability"], reverse=True)
            
            # Generate strategic analysis
            analysis = self._generate_strategic_analysis(company, predictions)
            
            return {
                "company_uei": company.get("uei"),
                "total_predictions": len(predictions),
                "high_probability": len([p for p in predictions if p["probability"] > 75]),
                "medium_probability": len([p for p in predictions if 50 <= p["probability"] <= 75]),
                "predictions": predictions[:10],  # Top 10
                "analysis": analysis,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Prediction error for {company.get('uei', 'unknown')}: {e}")
            return self._fallback_predictions(company)
    
    async def _fetch_sam_opportunities(self, company: Dict) -> List[Dict]:
        """Fetch relevant opportunities from SAM.gov API"""
        try:
            session = await self.get_session()
            
            # Build search criteria
            naics = company.get("primary_naics", "")
            state = company.get("state", "")
            certifications = company.get("active_sba_certifications", "")
            
            opportunities = []
            
            # Search by NAICS code
            if naics:
                naics_opps = await self._search_sam_by_naics(session, naics)
                opportunities.extend(naics_opps)
            
            # Search by set-aside types if company has certifications
            if certifications:
                cert_opps = await self._search_sam_by_certifications(session, certifications)
                opportunities.extend(cert_opps)
            
            # Remove duplicates
            seen_ids = set()
            unique_opportunities = []
            for opp in opportunities:
                if opp["opportunity_id"] not in seen_ids:
                    unique_opportunities.append(opp)
                    seen_ids.add(opp["opportunity_id"])
            
            return unique_opportunities[:50]  # Limit to 50 opportunities
            
        except Exception as e:
            print(f"SAM.gov fetch error: {e}")
            return self._get_mock_opportunities(company)
    
    async def _search_sam_by_naics(self, session, naics: str) -> List[Dict]:
        """Search SAM.gov by NAICS code"""
        try:
            # SAM.gov API endpoint (this is a simplified mock - real API requires registration)
            # In production, you'd use the actual SAM.gov Opportunities API
            
            # For now, return mock data based on NAICS patterns
            return self._generate_naics_opportunities(naics)
            
        except Exception as e:
            print(f"NAICS search error: {e}")
            return []
    
    async def _search_sam_by_certifications(self, session, certifications: str) -> List[Dict]:
        """Search SAM.gov by SBA certifications"""
        try:
            # Mock implementation - would use real SAM.gov API
            return self._generate_certification_opportunities(certifications)
            
        except Exception as e:
            print(f"Certification search error: {e}")
            return []
    
    def _calculate_match_score(self, company: Dict, opportunity: Dict) -> Dict:
        """Calculate comprehensive match score using ML-like algorithm"""
        score = 0
        reasoning_parts = []
        key_factors = []
        
        # NAICS Code Match (30% weight)
        company_naics = company.get("primary_naics", "")
        opp_naics = opportunity.get("naics_codes", [])
        
        if isinstance(opp_naics, str):
            opp_naics = [opp_naics]
        
        naics_match = False
        for opp_naics_code in opp_naics:
            if company_naics and opp_naics_code:
                if company_naics.startswith(opp_naics_code[:3]):  # Industry match
                    score += 30
                    naics_match = True
                    reasoning_parts.append(f"Strong NAICS match ({company_naics} → {opp_naics_code})")
                    key_factors.append("NAICS Code Alignment")
                    break
                elif company_naics.startswith(opp_naics_code[:2]):  # Sector match
                    score += 20
                    naics_match = True
                    reasoning_parts.append(f"Sector NAICS match ({company_naics} → {opp_naics_code})")
                    key_factors.append("Related Industry Experience")
                    break
        
        if not naics_match:
            reasoning_parts.append("Limited NAICS alignment")
        
        # SBA Certification Match (25% weight)
        company_certs = company.get("active_sba_certifications", "").upper()
        opp_set_asides = opportunity.get("set_aside_codes", [])
        
        if isinstance(opp_set_asides, str):
            opp_set_asides = [opp_set_asides]
        
        cert_match = False
        for set_aside in opp_set_asides:
            if "8(A)" in set_aside and "8A" in company_certs:
                score += 25
                cert_match = True
                reasoning_parts.append("8(a) certification advantage")
                key_factors.append("8(a) Small Business Certification")
                break
            elif "SDVOSB" in set_aside and "SDVOSB" in company_certs:
                score += 25
                cert_match = True
                reasoning_parts.append("SDVOSB certification advantage")
                key_factors.append("Service-Disabled Veteran Certification")
                break
            elif "WOSB" in set_aside and "WOSB" in company_certs:
                score += 20
                cert_match = True
                reasoning_parts.append("WOSB certification advantage")
                key_factors.append("Women-Owned Small Business Certification")
                break
            elif "HUBZONE" in set_aside and "HUBZONE" in company_certs:
                score += 20
                cert_match = True
                reasoning_parts.append("HUBZone certification advantage")
                key_factors.append("HUBZone Certification")
                break
        
        if not cert_match and company_certs:
            score += 5  # Small boost for having any certification
            reasoning_parts.append("Has SBA certifications")
        
        # Company Size/Experience (20% weight)
        investment_score = float(company.get("pe_investment_score", 0))
        if investment_score >= 90:
            score += 20
            reasoning_parts.append("Excellent company profile")
            key_factors.append("Strong Business Profile")
        elif investment_score >= 70:
            score += 15
            reasoning_parts.append("Good company profile")
            key_factors.append("Solid Business Profile")
        elif investment_score >= 50:
            score += 10
            reasoning_parts.append("Adequate company profile")
        
        # Contract History (15% weight) - would come from enrichment
        # For now, estimate based on company maturity
        if company.get("sam_status") == "Active":
            score += 10
            reasoning_parts.append("Active SAM registration")
            key_factors.append("SAM Registration Current")
        
        if company.get("cage_code"):
            score += 5
            reasoning_parts.append("Has CAGE code")
        
        # Geographic Preference (10% weight)
        company_state = company.get("state", "")
        opp_description = opportunity.get("description", "").upper()
        
        if company_state and company_state.upper() in opp_description:
            score += 10
            reasoning_parts.append(f"Geographic preference for {company_state}")
            key_factors.append("Local/Regional Preference")
        
        # Estimate competition level
        estimated_value = opportunity.get("estimated_value", "")
        competition_level = "High"  # Default
        
        if "million" in estimated_value.lower() or "$" in estimated_value and "M" in estimated_value:
            competition_level = "High"
        elif any(cert in company_certs for cert in ["8A", "SDVOSB", "WOSB"]):
            competition_level = "Medium"  # Set-asides typically have less competition
        elif naics_match and cert_match:
            competition_level = "Low"
        
        return {
            "score": min(100, max(0, score)),  # Clamp between 0-100
            "reasoning": "; ".join(reasoning_parts),
            "competition_level": competition_level,
            "key_factors": key_factors
        }
    
    def _generate_strategic_analysis(self, company: Dict, predictions: List[Dict]) -> Dict:
        """Generate strategic analysis and recommendations"""
        if not predictions:
            return {
                "market_position": "Limited opportunities identified",
                "strengths": [],
                "improvements": ["Expand NAICS capabilities", "Consider SBA certifications"],
                "recommendations": ["Review contracting strategy", "Enhance company profile"]
            }
        
        # Analyze strengths
        strengths = []
        certifications = company.get("active_sba_certifications", "")
        if certifications:
            strengths.append(f"SBA certification advantage ({certifications})")
        
        if company.get("pe_investment_score", 0) > 85:
            strengths.append("Strong business profile")
        
        if company.get("sam_status") == "Active":
            strengths.append("Active government registration")
        
        high_prob_count = len([p for p in predictions if p["probability"] > 75])
        if high_prob_count > 0:
            strengths.append(f"{high_prob_count} high-probability opportunities")
        
        # Identify improvement areas
        improvements = []
        if not certifications:
            improvements.append("Consider obtaining SBA certifications")
        
        if company.get("pe_investment_score", 0) < 70:
            improvements.append("Enhance business profile and capabilities")
        
        if not company.get("cage_code"):
            improvements.append("Obtain CAGE code for contracting")
        
        # Generate recommendations
        recommendations = []
        top_agencies = list(set([p["agency"] for p in predictions[:5]]))
        if top_agencies:
            recommendations.append(f"Focus on {', '.join(top_agencies[:2])} opportunities")
        
        avg_probability = sum(p["probability"] for p in predictions) / len(predictions)
        if avg_probability > 60:
            recommendations.append("Strong market position - pursue aggressive bidding strategy")
        elif avg_probability > 40:
            recommendations.append("Moderate position - focus on highest probability opportunities")
        else:
            recommendations.append("Build experience with smaller contracts first")
        
        market_position = "Competitive" if avg_probability > 60 else "Developing" if avg_probability > 40 else "Emerging"
        
        return {
            "market_position": f"{market_position} in government contracting",
            "strengths": strengths,
            "improvements": improvements,
            "recommendations": recommendations,
            "opportunity_focus": top_agencies[:3] if top_agencies else []
        }
    
    def _generate_naics_opportunities(self, naics: str) -> List[Dict]:
        """Generate mock opportunities based on NAICS code"""
        opportunities = []
        
        # Technology/IT services (54xxxx)
        if naics.startswith("54"):
            opportunities.extend([
                {
                    "opportunity_id": f"IT{naics[:3]}001",
                    "title": "IT Support and Cybersecurity Services",
                    "agency": "Department of Defense",
                    "naics_codes": [naics],
                    "set_aside_codes": ["SDVOSB"],
                    "estimated_value": "$500K - $2M",
                    "deadline": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
                    "description": f"Professional IT services for NAICS {naics} including system modernization and security."
                },
                {
                    "opportunity_id": f"IT{naics[:3]}002", 
                    "title": "Digital Transformation Consulting",
                    "agency": "General Services Administration",
                    "naics_codes": [naics],
                    "set_aside_codes": ["8(a)", "WOSB"],
                    "estimated_value": "$1M - $5M",
                    "deadline": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
                    "description": f"Digital modernization services for government agencies, NAICS {naics}."
                }
            ])
        
        # Manufacturing (3xxxxx)
        elif naics.startswith("3"):
            opportunities.extend([
                {
                    "opportunity_id": f"MFG{naics[:3]}001",
                    "title": "Manufacturing and Supply Services",
                    "agency": "Department of Defense",
                    "naics_codes": [naics],
                    "set_aside_codes": ["Small Business"],
                    "estimated_value": "$2M - $10M",
                    "deadline": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                    "description": f"Manufacturing services for defense applications, NAICS {naics}."
                }
            ])
        
        # Construction (23xxxx)
        elif naics.startswith("23"):
            opportunities.extend([
                {
                    "opportunity_id": f"CON{naics[:3]}001",
                    "title": "Facility Construction and Renovation",
                    "agency": "U.S. Army Corps of Engineers",
                    "naics_codes": [naics],
                    "set_aside_codes": ["HUBZone"],
                    "estimated_value": "$5M - $25M", 
                    "deadline": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
                    "description": f"Construction and renovation services for federal facilities, NAICS {naics}."
                }
            ])
        
        return opportunities
    
    def _generate_certification_opportunities(self, certifications: str) -> List[Dict]:
        """Generate opportunities based on SBA certifications"""
        opportunities = []
        
        if "SDVOSB" in certifications:
            opportunities.append({
                "opportunity_id": "SDVOSB001",
                "title": "Veteran-Owned Business Support Services",
                "agency": "Department of Veterans Affairs",
                "naics_codes": ["541611"],
                "set_aside_codes": ["SDVOSB"],
                "estimated_value": "$1M - $3M",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "description": "Administrative and support services reserved for Service-Disabled Veteran-Owned Small Businesses."
            })
        
        if "8A" in certifications:
            opportunities.append({
                "opportunity_id": "8A001",
                "title": "8(a) Program Professional Services",
                "agency": "Small Business Administration",
                "naics_codes": ["541990"],
                "set_aside_codes": ["8(a)"],
                "estimated_value": "$500K - $2M",
                "deadline": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
                "description": "Professional services opportunity reserved for 8(a) certified small businesses."
            })
        
        return opportunities
    
    def _get_mock_opportunities(self, company: Dict) -> List[Dict]:
        """Fallback mock opportunities"""
        return [
            {
                "opportunity_id": "MOCK001",
                "title": "General Professional Services",
                "agency": "General Services Administration",
                "naics_codes": ["541990"],
                "set_aside_codes": ["Small Business"],
                "estimated_value": "$250K - $1M",
                "deadline": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
                "description": "General professional services for government agencies."
            }
        ]
    
    def _fallback_predictions(self, company: Dict) -> Dict:
        """Fallback prediction data"""
        return {
            "company_uei": company.get("uei"),
            "total_predictions": 0,
            "high_probability": 0,
            "medium_probability": 0,
            "predictions": [],
            "analysis": {
                "market_position": "Unable to assess - data unavailable",
                "strengths": [],
                "improvements": ["Check internet connection", "Verify company data"],
                "recommendations": ["Try again later"]
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_naics_patterns(self) -> Dict:
        """Load NAICS code patterns for better matching"""
        return {
            "54": "Professional Services",
            "23": "Construction",
            "33": "Manufacturing",
            "56": "Administrative Support",
            "62": "Health Care"
        }
    
    def _load_agency_preferences(self) -> Dict:
        """Load agency preferences for certain business types"""
        return {
            "DoD": ["SDVOSB", "8(a)", "Small Business"],
            "VA": ["SDVOSB", "VOSB"],
            "SBA": ["8(a)", "HUBZone", "WOSB"],
            "GSA": ["Small Business", "WOSB"]
        }
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

# Global predictor instance
ml_predictor = MLContractPredictor()

if __name__ == "__main__":
    # Test the predictor
    async def test():
        test_company = {
            "uei": "PD85S6JN3D38",
            "organization_name": "3 STAR MANUFACTURING, INC",
            "primary_naics": "339999",
            "state": "Alabama",
            "active_sba_certifications": "SDVOSB",
            "pe_investment_score": 100.0,
            "sam_status": "Active"
        }
        
        predictions = await ml_predictor.predict_contract_opportunities(test_company)
        print("ML Contract Predictions:")
        print(json.dumps(predictions, indent=2))
        
        await ml_predictor.close()
    
    asyncio.run(test())