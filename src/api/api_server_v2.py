def get_user_context(
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None, description="API key for authentication")
) -> str:
    """Get user context from auth token or API key"""
    
    # First try API key from query parameter (easier for Swagger)
    if api_key:
        user_type = VALID_TOKENS.get(api_key)
        if user_type:
            return user_type
    
    # Then try Authorization header
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            token = authorization
        
        user_type = VALID_TOKENS.get(token)
        if user_type:
            return user_type
    
    raise HTTPException(status_code=401, detail="Invalid authentication")

# Copy all the other endpoints from your original api_server.py
# ... (rest of the code remains the same)
}

def get_user_context(authorization: str = Header(None)) -> str:
    """Get user context from auth token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    token = authorization.replace("Bearer ", "")
    user_type = VALID_TOKENS.get(token)
    
    if not user_type:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_type

@app.get("/api/v2/companies/{uei}/intelligence")
async def get_company_intelligence(uei: str, user_type: str = Depends(get_user_context)):
    """Get intelligent, context-aware company analysis"""
    
    # Find company
    company_data = company_index.get(uei)
    if not company_data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Build base intelligence
    base_info = {
        "uei": uei,
        "company_name": company_data["name"],
        "location": {
            "city": company_data.get("city", "Unknown"),
            "state": company_data.get("state", "Unknown"),
            "address": company_data.get("address", "Not provided")
        },
        "contact": {
            "email": company_data.get("email"),
            "phone": str(company_data.get("phone")) if company_data.get("phone") else None,
            "website": company_data.get("website"),
            "contact_name": f"{company_data.get('first_name', '')} {company_data.get('last_name', '')}".strip()
        },
        "business_info": {
            "naics_code": company_data.get("naics"),
            "legal_structure": company_data.get("legal_structure", "Unknown"),
            "certifications": company_data.get("certifications", "").split(",") if company_data.get("certifications") else []
        }
    }
    
    # Context-aware analysis based on user type
    if user_type == "pe_firm":
        # PE firm analysis - focus on acquisition potential
        risk_score = 0
        risk_factors = []
        opportunities = []
        
        if not company_data.get("website"):
            risk_score += 30
            risk_factors.append("No digital presence")
            opportunities.append("Digital transformation potential")
        
        if "Sole" in str(company_data.get("legal_structure", "")):
            risk_score += 25
            risk_factors.append("Sole proprietorship - succession risk")
            opportunities.append("Succession planning opportunity")
        
        if not company_data.get("email"):
            risk_score += 15
            risk_factors.append("Limited contact information")
        
        base_info.update({
            "risk_assessment": {
                "score": risk_score,
                "level": "High" if risk_score > 50 else "Medium" if risk_score > 25 else "Low",
                "factors": risk_factors
            },
            "opportunities": opportunities,
            "recommendations": [
                {
                    "priority": "High",
                    "action": "Conduct detailed due diligence",
                    "reason": "Assess operational dependencies and growth potential"
                },
                {
                    "priority": "Medium",
                    "action": "Evaluate digital transformation ROI",
                    "reason": "Significant value creation opportunity"
                }
            ],
            "estimated_value": {
                "range_low": "$500K",
                "range_high": "$2M",
                "factors": ["Industry", "Location", "Digital presence", "Structure"]
            }
        })
    else:  # smb_owner
        # SMB owner analysis - focus on growth opportunities
        opportunities = []
        recommendations = []
        
        if not company_data.get("website"):
            opportunities.append("Establish online presence")
            recommendations.append({
                "priority": "High",
                "action": "Create professional website",
                "reason": "80% of customers research online before purchasing"
            })
        
        if not company_data.get("capabilities_narrative"):
            opportunities.append("Document your capabilities")
            recommendations.append({
                "priority": "High",
                "action": "Create capability statement",
                "reason": "Required for government contracts"
            })
        
        if "Sole" in str(company_data.get("legal_structure", "")):
            opportunities.append("Consider business structure upgrade")
            recommendations.append({
                "priority": "Medium",
                "action": "Explore LLC or Corporation structure",
                "reason": "Better liability protection and growth potential"
            })
        
        base_info.update({
            "growth_opportunities": opportunities,
            "recommendations": recommendations,
            "resources": {
                "funding": ["SBA loans", "SBIR grants", "Local development programs"],
                "training": ["SCORE mentorship", "SBA learning center", "Industry associations"],
                "certifications": ["8(a)", "HUBZone", "WOSB/EDWOSB", "VOSB/SDVOSB"]
            },
            "next_steps": {
                "immediate": "Address highest priority recommendations",
                "short_term": "Pursue relevant certifications",
                "long_term": "Build strategic partnerships"
            }
        })
    
    return base_info

@app.get("/api/v2/search")
async def search_companies(
    q: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20,
    user_type: str = Depends(get_user_context)
):
    """Search companies with filters"""
    results = []
    
    for uei, data in company_index.items():
        # Apply filters
        if state and str(data.get("state", "")).lower() != state.lower():
            continue
        
        if q and q.lower() not in str(data.get("name", "")).lower():
            continue
        
        # Handle float values for state
        if isinstance(data.get("state"), float):
            continue
            
        results.append({
            "uei": uei,
            "name": data["name"],
            "location": f"{data.get('city', 'Unknown')}, {data.get('state', 'Unknown')}",
            "website": data.get("website"),
            "certifications": data.get("certifications", "").split(",") if data.get("certifications") else []
        })
        
        if len(results) >= limit:
            break
    
    return {
        "count": len(results),
        "results": results,
        "user_context": user_type
    }

@app.get("/api/v2/market-insights")
async def get_market_insights(user_type: str = Depends(get_user_context)):
    """Get market-wide insights"""
    
    if user_type == "pe_firm":
        return {
            "total_opportunities": market_insights.get("pe_targets", {}).get("total", 0),
            "top_states": dict(list(market_insights.get("states", {}).items())[:5]),
            "digital_transformation_targets": market_insights.get("digital_presence", {}).get("without_website", 0),
            "recommended_focus_areas": [
                "Companies without websites",
                "Sole proprietorships needing succession",
                "High-growth industries (Tech, Healthcare, Professional Services)"
            ]
        }
    else:
        return {
            "total_market_size": market_insights.get("total_companies", 0),
            "competitive_landscape": {
                "your_state_competitors": "Use search endpoint with your state",
                "digital_adoption": f"{market_insights.get('digital_presence', {}).get('with_website', 0):,} have websites"
            },
            "growth_resources": {
                "government": ["SAM.gov", "SBA.gov", "SBIR.gov"],
                "funding": ["SBA loans", "Angel investors", "Crowdfunding"],
                "training": ["SCORE", "SBDC", "Industry associations"]
            }
        }

@app.get("/api/v2/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "companies_loaded": len(company_index),
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
