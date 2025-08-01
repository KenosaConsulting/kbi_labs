#!/usr/bin/env python3
"""
Unified Procurement Enrichment Pipeline
Orchestrates all procurement APIs for comprehensive company enrichment
"""

import asyncio
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path

# Import our procurement integrations
from gsa_calc_integration import GSACALCProcessor
from fpds_integration import FPDSProcessor  
from sam_opportunities_integration import SAMOpportunitiesProcessor
from sam_gov_integration import CachedSAMGovAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedProcurementEnrichment:
    """
    Unified processor that combines all procurement data sources
    for comprehensive business intelligence enrichment
    """
    
    def __init__(self, sam_gov_api_key: str = None):
        self.sam_gov_api_key = sam_gov_api_key or os.environ.get('SAM_GOV_API_KEY')
        
        # Initialize processors
        self.gsa_calc = None
        self.fpds = None
        self.sam_opportunities = None
        self.sam_gov = None
        
        if self.sam_gov_api_key:
            self.sam_gov = CachedSAMGovAPI(self.sam_gov_api_key)
        else:
            logger.warning("No SAM.gov API key provided - SAM.gov integrations will be skipped")
    
    async def __aenter__(self):
        """Initialize all processors"""
        self.gsa_calc = await GSACALCProcessor().__aenter__()
        self.fpds = await FPDSProcessor().__aenter__()
        
        if self.sam_gov_api_key:
            self.sam_opportunities = await SAMOpportunitiesProcessor(self.sam_gov_api_key).__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all processors"""
        if self.gsa_calc:
            await self.gsa_calc.__aexit__(exc_type, exc_val, exc_tb)
        if self.fpds:
            await self.fpds.__aexit__(exc_type, exc_val, exc_tb)
        if self.sam_opportunities:
            await self.sam_opportunities.__aexit__(exc_type, exc_val, exc_tb)

    async def enrich_company_comprehensive(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive procurement enrichment for a single company
        Combines data from all available procurement sources
        """
        company_name = company_data.get('Organization Name', 'Unknown')
        logger.info(f"🔍 Starting comprehensive procurement enrichment for: {company_name}")
        
        enriched_data = company_data.copy()
        enrichment_summary = {
            'sources_queried': [],
            'sources_found': [],
            'total_apis_called': 0,
            'enrichment_timestamp': datetime.now().isoformat()
        }
        
        # 1. GSA CALC API (Labor Rates) - No API key required
        try:
            logger.info(f"   📊 Querying GSA CALC for pricing data...")
            enrichment_summary['sources_queried'].append('GSA_CALC')
            enrichment_summary['total_apis_called'] += 1
            
            calc_enriched = await self.gsa_calc.enrich_company_with_calc_data(enriched_data)
            if calc_enriched.get('gsa_calc_found'):
                enrichment_summary['sources_found'].append('GSA_CALC')
                logger.info(f"   ✅ GSA CALC: Found {calc_enriched.get('gsa_schedule_rates', 0)} rate records")
            
            enriched_data.update(calc_enriched)
            
        except Exception as e:
            logger.error(f"   ❌ GSA CALC error: {e}")

        # 2. FPDS (Historical Procurement Data) - No API key required
        try:
            logger.info(f"   📈 Querying FPDS for historical contracts...")
            enrichment_summary['sources_queried'].append('FPDS')
            enrichment_summary['total_apis_called'] += 1
            
            fpds_enriched = await self.fpds.enrich_company_with_fpds_data(enriched_data)
            if fpds_enriched.get('fpds_found'):
                enrichment_summary['sources_found'].append('FPDS')
                logger.info(f"   ✅ FPDS: Found {fpds_enriched.get('fpds_total_contracts', 0)} historical contracts")
            
            enriched_data.update(fpds_enriched)
            
        except Exception as e:
            logger.error(f"   ❌ FPDS error: {e}")

        # 3. SAM.gov Entity Data (requires API key)
        if self.sam_gov:
            try:
                uei = enriched_data.get('UEI (Unique Entity Identifier)')
                if uei:
                    logger.info(f"   🏛️ Querying SAM.gov for entity registration...")
                    enrichment_summary['sources_queried'].append('SAM_GOV_ENTITY')
                    enrichment_summary['total_apis_called'] += 1
                    
                    sam_data = self.sam_gov.get_entity(str(uei).strip())
                    if sam_data:
                        enrichment_summary['sources_found'].append('SAM_GOV_ENTITY')
                        logger.info(f"   ✅ SAM.gov Entity: Found registration data")
                        
                        # Map SAM.gov data to our schema
                        enriched_data.update({
                            'sam_registration_status': sam_data.get('registration_status'),
                            'sam_cage_code': sam_data.get('cage_code'),
                            'sam_registration_date': sam_data.get('registration_date'),
                            'sam_expiration_date': sam_data.get('expiration_date'),
                            'sam_business_types': sam_data.get('business_types'),
                            'sam_certifications': sam_data.get('sba_certifications'),
                            'sam_federal_ready_score': sam_data.get('federal_ready_score'),
                            'sam_entity_found': True
                        })
                
            except Exception as e:
                logger.error(f"   ❌ SAM.gov entity error: {e}")

        # 4. SAM.gov Opportunities (requires API key)
        if self.sam_opportunities:
            try:
                logger.info(f"   🎯 Querying SAM.gov for matching opportunities...")
                enrichment_summary['sources_queried'].append('SAM_GOV_OPPORTUNITIES')
                enrichment_summary['total_apis_called'] += 1
                
                opp_enriched = await self.sam_opportunities.enrich_company_with_opportunities(enriched_data)
                if opp_enriched.get('sam_opportunities_found'):
                    enrichment_summary['sources_found'].append('SAM_GOV_OPPORTUNITIES')
                    logger.info(f"   ✅ SAM.gov Opportunities: Found {opp_enriched.get('sam_total_matches', 0)} matching opportunities")
                
                enriched_data.update(opp_enriched)
                
            except Exception as e:
                logger.error(f"   ❌ SAM.gov opportunities error: {e}")

        # Calculate comprehensive procurement score
        enriched_data['procurement_intelligence_score'] = self._calculate_procurement_score(enriched_data)
        enriched_data['enrichment_summary'] = enrichment_summary
        
        logger.info(f"🎉 Enrichment complete for {company_name}: {len(enrichment_summary['sources_found'])}/{len(enrichment_summary['sources_queried'])} sources found")
        
        return enriched_data

    def _calculate_procurement_score(self, company_data: Dict[str, Any]) -> int:
        """
        Calculate comprehensive procurement readiness score (0-100)
        """
        score = 0
        
        # SAM.gov registration (25 points)
        if company_data.get('sam_entity_found'):
            if company_data.get('sam_registration_status') == 'ACTIVE':
                score += 25
            elif company_data.get('sam_registration_status'):
                score += 15
        
        # Historical performance (25 points)
        if company_data.get('fpds_found'):
            fpds_score = company_data.get('fpds_performance_score', 0)
            score += int(fpds_score * 0.25)  # Scale FPDS score to 25 points
        
        # GSA Schedule presence (20 points)
        if company_data.get('gsa_calc_found'):
            rate_count = company_data.get('gsa_schedule_rates', 0)
            if rate_count >= 10:
                score += 20
            elif rate_count >= 5:
                score += 15
            elif rate_count >= 1:
                score += 10
        
        # Opportunity matching (15 points)
        if company_data.get('sam_opportunities_found'):
            match_score = company_data.get('sam_avg_match_score', 0)
            score += int(match_score * 0.15)  # Scale to 15 points
        
        # Federal readiness factors (15 points)
        if company_data.get('sam_federal_ready_score'):
            federal_score = company_data.get('sam_federal_ready_score', 0)
            score += int(federal_score * 0.15)  # Scale to 15 points
        
        return min(score, 100)

    async def process_company_batch(self, companies_df: pd.DataFrame, 
                                  batch_size: int = 5, output_file: str = None) -> pd.DataFrame:
        """
        Process a batch of companies with comprehensive procurement enrichment
        """
        total_companies = len(companies_df)
        logger.info(f"🚀 Starting batch procurement enrichment for {total_companies} companies")
        
        enriched_companies = []
        
        # Process in smaller batches to manage API rate limits
        for i in range(0, total_companies, batch_size):
            batch = companies_df.iloc[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_companies + batch_size - 1) // batch_size
            
            logger.info(f"📦 Processing batch {batch_num}/{total_batches}: companies {i+1}-{min(i+batch_size, total_companies)}")
            
            # Process companies in parallel within batch
            batch_tasks = []
            for _, company in batch.iterrows():
                task = self.enrich_company_comprehensive(company.to_dict())
                batch_tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Error processing company {i+j+1}: {result}")
                    # Add original company data with error flag
                    error_data = batch.iloc[j].to_dict()
                    error_data['enrichment_error'] = str(result)
                    error_data['procurement_intelligence_score'] = 0
                    enriched_companies.append(error_data)
                else:
                    enriched_companies.append(result)
            
            logger.info(f"✅ Batch {batch_num} complete. Processed: {len(enriched_companies)}/{total_companies}")
            
            # Brief pause between batches
            if batch_num < total_batches:
                await asyncio.sleep(2)
        
        # Create enriched DataFrame
        enriched_df = pd.DataFrame(enriched_companies)
        
        # Save if output file specified
        if output_file:
            enriched_df.to_csv(output_file, index=False)
            logger.info(f"💾 Enriched data saved to: {output_file}")
        
        # Print summary statistics
        self._print_enrichment_summary(enriched_df)
        
        return enriched_df

    def _print_enrichment_summary(self, enriched_df: pd.DataFrame):
        """Print comprehensive enrichment summary"""
        total_companies = len(enriched_df)
        
        # Source success rates
        sources = ['GSA_CALC', 'FPDS', 'SAM_GOV_ENTITY', 'SAM_GOV_OPPORTUNITIES']
        source_stats = {}
        
        for source in sources:
            found_col = None
            if source == 'GSA_CALC':
                found_col = 'gsa_calc_found'
            elif source == 'FPDS':
                found_col = 'fpds_found'
            elif source == 'SAM_GOV_ENTITY':
                found_col = 'sam_entity_found'
            elif source == 'SAM_GOV_OPPORTUNITIES':
                found_col = 'sam_opportunities_found'
            
            if found_col and found_col in enriched_df.columns:
                found_count = enriched_df[found_col].sum()
                source_stats[source] = {
                    'found': found_count,
                    'rate': (found_count / total_companies) * 100
                }
        
        # Procurement score analysis
        scores = enriched_df['procurement_intelligence_score']
        high_scoring = len(scores[scores >= 70])
        medium_scoring = len(scores[(scores >= 40) & (scores < 70)])
        low_scoring = len(scores[scores < 40])
        
        # Print comprehensive summary
        print("\n" + "="*60)
        print("🎯 PROCUREMENT ENRICHMENT SUMMARY")
        print("="*60)
        print(f"Total companies processed: {total_companies:,}")
        print(f"Average procurement score: {scores.mean():.1f}/100")
        print(f"Median procurement score: {scores.median():.1f}/100")
        print()
        
        print("📊 SOURCE SUCCESS RATES:")
        for source, stats in source_stats.items():
            print(f"  {source:.<25} {stats['found']:>6,} ({stats['rate']:>5.1f}%)")
        print()
        
        print("🏆 PROCUREMENT READINESS DISTRIBUTION:")
        print(f"  High Ready (70-100): {high_scoring:>6,} ({(high_scoring/total_companies)*100:>5.1f}%)")
        print(f"  Medium Ready (40-69): {medium_scoring:>6,} ({(medium_scoring/total_companies)*100:>5.1f}%)")
        print(f"  Low Ready (0-39): {low_scoring:>6,} ({(low_scoring/total_companies)*100:>5.1f}%)")
        print()
        
        # Top insights
        if 'sam_total_matches' in enriched_df.columns:
            total_opportunities = enriched_df['sam_total_matches'].sum()
            print(f"💼 Total opportunities identified: {total_opportunities:,}")
        
        if 'fpds_total_value' in enriched_df.columns:
            total_contract_value = enriched_df['fpds_total_value'].sum()
            print(f"💰 Total historical contract value: ${total_contract_value:,.2f}")
        
        if 'gsa_schedule_rates' in enriched_df.columns:
            total_gsa_rates = enriched_df['gsa_schedule_rates'].sum()
            print(f"📋 Total GSA schedule rates found: {total_gsa_rates:,}")
        
        print("="*60)

    async def generate_procurement_intelligence_report(self, output_dir: str = "reports"):
        """
        Generate comprehensive procurement market intelligence reports
        """
        logger.info("📊 Generating procurement intelligence reports...")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate individual API reports
        reports = []
        
        # GSA CALC Market Report
        calc_report_file = f"{output_dir}/gsa_calc_market_report.csv"
        await self.gsa_calc.generate_procurement_intelligence_report(calc_report_file)
        reports.append(calc_report_file)
        
        # Small Business Opportunities Report
        if self.sam_opportunities:
            sb_opps = await self.sam_opportunities.search_small_business_opportunities(limit=500)
            if sb_opps:
                sb_report_file = f"{output_dir}/small_business_opportunities.json"
                with open(sb_report_file, 'w') as f:
                    json.dump(sb_opps, f, indent=2, default=str)
                reports.append(sb_report_file)
        
        logger.info(f"📋 Generated {len(reports)} intelligence reports in {output_dir}/")
        return reports

# CLI Interface
async def main():
    """
    Main CLI interface for unified procurement enrichment
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Procurement Enrichment Pipeline')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file with company data')
    parser.add_argument('--output', '-o', help='Output CSV file for enriched data')
    parser.add_argument('--sam-api-key', help='SAM.gov API key (or set SAM_GOV_API_KEY env var)')
    parser.add_argument('--batch-size', '-b', type=int, default=5, help='Batch size for processing')
    parser.add_argument('--reports', action='store_true', help='Generate intelligence reports')
    parser.add_argument('--reports-dir', default='reports', help='Directory for reports')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        return
    
    # Set default output filename
    if not args.output:
        input_stem = Path(args.input).stem
        args.output = f"{input_stem}_procurement_enriched.csv"
    
    # Load company data
    logger.info(f"📁 Loading company data from: {args.input}")
    companies_df = pd.read_csv(args.input)
    logger.info(f"📊 Loaded {len(companies_df)} companies for enrichment")
    
    # Initialize and run enrichment
    sam_api_key = args.sam_api_key or os.environ.get('SAM_GOV_API_KEY')
    
    async with UnifiedProcurementEnrichment(sam_api_key) as enricher:
        # Process companies
        enriched_df = await enricher.process_company_batch(
            companies_df, 
            batch_size=args.batch_size,
            output_file=args.output
        )
        
        # Generate reports if requested
        if args.reports:
            await enricher.generate_procurement_intelligence_report(args.reports_dir)
    
    logger.info("🎉 Unified procurement enrichment complete!")

if __name__ == "__main__":
    asyncio.run(main())