from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('../kbi_complete_enriched.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main dashboard view"""
    conn = get_db_connection()
    
    # Get summary stats
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_companies,
            AVG(pe_investment_score) as avg_score,
            COUNT(CASE WHEN business_health_grade = 'A' THEN 1 END) as grade_a,
            COUNT(CASE WHEN patent_count > 0 THEN 1 END) as has_patents
        FROM enriched_companies_full
    ''').fetchone()
    
    # Get top companies
    top_companies = conn.execute('''
        SELECT * FROM enriched_companies_full 
        ORDER BY pe_investment_score DESC 
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', stats=stats, top_companies=top_companies)

@app.route('/api/companies')
def api_companies():
    """API endpoint for company data"""
    conn = get_db_connection()
    
    # Get query parameters
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    
    companies = conn.execute('''
        SELECT * FROM enriched_companies_full 
        WHERE pe_investment_score >= ?
        ORDER BY pe_investment_score DESC 
        LIMIT ? OFFSET ?
    ''', (min_score, limit, offset)).fetchall()
    
    conn.close()
    
    return jsonify([dict(row) for row in companies])

@app.route('/company/<uei>')
def company_detail(uei):
    """Individual company detail page"""
    conn = get_db_connection()
    company = conn.execute('SELECT * FROM enriched_companies_full WHERE uei = ?', (uei,)).fetchone()
    conn.close()
    
    if company:
        return render_template('company_detail.html', company=company)
    else:
        return "Company not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
