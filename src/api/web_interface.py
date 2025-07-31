#!/usr/bin/env python3
"""
KBI Labs Web Interface
Simple FastAPI interface to view enriched data
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import pandas as pd
import json

app = FastAPI(title="KBI Labs Enriched Data Viewer")

def get_db_connection():
    return sqlite3.connect('kbi_enriched_master.db')

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with summary statistics"""
    conn = get_db_connection()
    
    # Get statistics
    total = pd.read_sql_query("SELECT COUNT(*) as count FROM companies_master", conn).iloc[0]['count']
    avg_score = pd.read_sql_query("SELECT AVG(pe_investment_score) as avg FROM companies_master", conn).iloc[0]['avg']
    
    # Grade distribution
    grades = pd.read_sql_query(
        "SELECT business_health_grade, COUNT(*) as count FROM companies_master GROUP BY business_health_grade ORDER BY business_health_grade", 
        conn
    )
    
    conn.close()
    
    html = f"""
    <html>
    <head>
        <title>KBI Labs - Enriched Company Data</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .stat-box {{ background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>KBI Labs - Enriched Company Database</h1>
        
        <div class="stat-box">
            <h2>Summary Statistics</h2>
            <p><strong>Total Companies:</strong> {total:,}</p>
            <p><strong>Average PE Score:</strong> {avg_score:.1f}</p>
        </div>
        
        <h3>Business Health Grade Distribution</h3>
        <table>
            <tr><th>Grade</th><th>Count</th><th>Percentage</th></tr>
    """
    
    for _, row in grades.iterrows():
        pct = row['count'] / total * 100 if total > 0 else 0
        html += f"<tr><td>{row['business_health_grade']}</td><td>{row['count']:,}</td><td>{pct:.1f}%</td></tr>"
    
    html += """
        </table>
        
        <h3>Quick Links</h3>
        <ul>
            <li><a href="/companies/top">Top 100 Companies by PE Score</a></li>
            <li><a href="/companies/search">Search Companies</a></li>
            <li><a href="/api/stats">API: Statistics</a></li>
        </ul>
    </body>
    </html>
    """
    
    return html

@app.get("/companies/top", response_class=HTMLResponse)
async def top_companies():
    """Show top 100 companies"""
    conn = get_db_connection()
    
    companies = pd.read_sql_query("""
        SELECT organization_name, city, state, pe_investment_score, 
               business_health_grade, industry_sector, certification_count
        FROM companies_master
        ORDER BY pe_investment_score DESC
        LIMIT 100
    """, conn)
    
    conn.close()
    
    html = """
    <html>
    <head>
        <title>Top 100 Companies - KBI Labs</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Top 100 Companies by PE Investment Score</h1>
        <a href="/">← Back to Home</a>
        
        <table>
            <tr>
                <th>Rank</th>
                <th>Company</th>
                <th>Location</th>
                <th>Industry</th>
                <th>PE Score</th>
                <th>Grade</th>
                <th>Certifications</th>
            </tr>
    """
    
    for i, row in companies.iterrows():
        html += f"""
            <tr>
                <td>{i+1}</td>
                <td>{row['organization_name']}</td>
                <td>{row['city']}, {row['state']}</td>
                <td>{row['industry_sector']}</td>
                <td>{row['pe_investment_score']:.1f}</td>
                <td>{row['business_health_grade']}</td>
                <td>{row['certification_count']}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html

@app.get("/api/stats")
async def api_stats():
    """API endpoint for statistics"""
    conn = get_db_connection()
    
    stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_companies,
            AVG(pe_investment_score) as avg_pe_score,
            COUNT(CASE WHEN has_website = 1 THEN 1 END) as companies_with_websites,
            AVG(certification_count) as avg_certifications
        FROM companies_master
    """, conn).iloc[0].to_dict()
    
    conn.close()
    
    return stats

if __name__ == "__main__":
    import uvicorn
    print("Starting KBI Labs Web Interface...")
    print("Access at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8001)
