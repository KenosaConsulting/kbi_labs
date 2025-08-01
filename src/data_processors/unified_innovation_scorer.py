#!/usr/bin/env python3
"""
Unified Innovation Scorer
Combines NSF awards and patent data for comprehensive innovation metrics
"""

import pandas as pd
import logging
from typing import Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedInnovationScorer:
    def __init__(self):
        self.nsf_processor = None
        self.patent_processor = None
        self.load_processors()
        
    def load_processors(self):
        """Load NSF and Patent processors"""
        try:
            from src.data_processors.nsf_processor_fixed import NSFProcessor
            self.nsf_processor = NSFProcessor()
            logger.info("Loading NSF data...")
            self.nsf_processor.load_awards()
            logger.info(f"Loaded {len(self.nsf_processor.awards)} NSF awards")
        except Exception as e:
            logger.error(f"Could not load NSF processor: {e}")
            
        # Patent processor will be loaded when data is available
        
    def calculate_comprehensive_score(self, organization: str) -> Dict:
        """Calculate unified innovation score combining all sources"""
        
        result = {
            "organization": organization,
            "timestamp": datetime.now().isoformat(),
            "nsf_metrics": {},
            "patent_metrics": {},
            "combined_score": 0,
            "innovation_category": "Unknown",
            "investment_rating": "Not Rated"
        }
        
        # Get NSF metrics
        if self.nsf_processor:
            nsf_data = self.nsf_processor.calculate_metrics(organization)
            result["nsf_metrics"] = {
                "awards_count": nsf_data["nsf_awards_count"],
                "total_funding": nsf_data["nsf_total_funding"],
                "recent_awards": nsf_data["recent_awards"]
            }
        
        # Calculate scores
        nsf_score = self._calculate_nsf_score(result["nsf_metrics"])
        patent_score = 0  # Will be updated when patent data is available
        
        # Combined score (0-100)
        result["combined_score"] = nsf_score + patent_score
        
        # Categorize
        score = result["combined_score"]
        if score >= 80:
            result["innovation_category"] = "Highly Innovative"
            result["investment_rating"] = "A+"
        elif score >= 60:
            result["innovation_category"] = "Innovative"
            result["investment_rating"] = "A"
        elif score >= 40:
            result["innovation_category"] = "Moderately Innovative"
            result["investment_rating"] = "B+"
        elif score >= 20:
            result["innovation_category"] = "Emerging Innovation"
            result["investment_rating"] = "B"
        else:
            result["innovation_category"] = "Traditional"
            result["investment_rating"] = "C"
            
        return result
    
    def _calculate_nsf_score(self, nsf_metrics: Dict) -> float:
        """Calculate NSF contribution to innovation score (0-50 points)"""
        score = 0
        
        # Awards count (max 20 points)
        awards = nsf_metrics.get("awards_count", 0)
        score += min(20, awards * 2)
        
        # Funding amount (max 20 points)
        funding = nsf_metrics.get("total_funding", 0)
        score += min(20, funding / 100000)  # $100k = 1 point
        
        # Recent activity (max 10 points)
        recent = nsf_metrics.get("recent_awards", 0)
        score += min(10, recent * 3)
        
        return min(50, score)
    
    def process_dsbs_batch(self, companies: list) -> pd.DataFrame:
        """Process a batch of companies"""
        results = []
        
        for i, company in enumerate(companies):
            if i % 10 == 0:
                logger.info(f"Processing {i}/{len(companies)}...")
                
            score_data = self.calculate_comprehensive_score(company)
            results.append({
                "Organization Name": company,
                "Innovation Score": score_data["combined_score"],
                "Category": score_data["innovation_category"],
                "Investment Rating": score_data["investment_rating"],
                "NSF Awards": score_data["nsf_metrics"].get("awards_count", 0),
                "NSF Funding": score_data["nsf_metrics"].get("total_funding", 0),
                "Patent Count": score_data["patent_metrics"].get("count", 0)
            })
            
        return pd.DataFrame(results)

# Test function
if __name__ == "__main__":
    scorer = UnifiedInnovationScorer()
    
    # Test with sample companies
    test_companies = [
        "Massachusetts Institute of Technology",
        "Stanford University",
        "Tech Solutions LLC",
        "Green Energy Corp"
    ]
    
    for company in test_companies:
        result = scorer.calculate_comprehensive_score(company)
        print(f"\n{company}:")
        print(f"  Innovation Score: {result['combined_score']}%")
        print(f"  Category: {result['innovation_category']}")
        print(f"  Investment Rating: {result['investment_rating']}")
        print(f"  NSF Awards: {result['nsf_metrics'].get('awards_count', 0)}")
