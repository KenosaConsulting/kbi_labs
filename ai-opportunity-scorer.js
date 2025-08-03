/**
 * KBI Labs AI Opportunity Scorer
 * Client-side JavaScript implementation for real-time opportunity evaluation
 */

class AIOpportunityScorer {
    constructor() {
        this.version = "2.0.0";
        this.modelWeights = {
            // Scoring weights for different factors
            valueAlignment: 0.25,      // How well the opportunity aligns with company capabilities
            competitiveAnalysis: 0.20, // Competition level assessment
            agencyRelationship: 0.15,  // Historical success with agency
            technicalMatch: 0.15,      // Technical requirements fit
            financialViability: 0.10,  // Financial aspects (size, payment terms)
            timeConstraints: 0.10,     // Deadline and timeline factors
            riskAssessment: 0.05       // Overall risk evaluation
        };

        this.companyProfile = {
            // Mock company profile - would be user-configurable
            primaryNAICS: ['541511', '541512', '541513'], // IT services
            capabilities: ['cloud', 'cybersecurity', 'software development', 'it consulting'],
            securityClearance: true,
            smallBusiness: true,
            preferredAgencies: ['DoD', 'DHS', 'VA'],
            teamSize: 25,
            maxContractValue: 5000000
        };
    }

    /**
     * Main scoring function - evaluates an opportunity and returns comprehensive analysis
     * @param {Object} opportunity - Raw opportunity data from government APIs
     * @returns {Object} Detailed scoring analysis with recommendations
     */
    async scoreOpportunity(opportunity) {
        const startTime = performance.now();
        
        try {
            // Extract and normalize opportunity data
            const normalizedOpp = this.normalizeOpportunityData(opportunity);
            
            // Calculate individual factor scores
            const factorScores = {
                valueAlignment: this.calculateValueAlignment(normalizedOpp),
                competitiveAnalysis: this.calculateCompetitiveAnalysis(normalizedOpp),
                agencyRelationship: this.calculateAgencyRelationship(normalizedOpp),
                technicalMatch: this.calculateTechnicalMatch(normalizedOpp),
                financialViability: this.calculateFinancialViability(normalizedOpp),
                timeConstraints: this.calculateTimeConstraints(normalizedOpp),
                riskAssessment: this.calculateRiskAssessment(normalizedOpp)
            };

            // Calculate weighted overall score
            const overallScore = this.calculateWeightedScore(factorScores);
            
            // Generate recommendation based on score and factors
            const recommendation = this.generateRecommendation(overallScore, factorScores);
            
            // Calculate confidence level
            const confidence = this.calculateConfidence(factorScores, normalizedOpp);
            
            // Generate win probability
            const winProbability = this.calculateWinProbability(overallScore, factorScores);
            
            // Create detailed analysis
            const analysis = this.generateDetailedAnalysis(normalizedOpp, factorScores, overallScore);
            
            const processingTime = performance.now() - startTime;
            
            return {
                opportunity_id: normalizedOpp.id,
                overall_score: Math.round(overallScore * 10) / 10,
                recommendation: recommendation.action,
                confidence: Math.round(confidence * 100),
                win_probability: Math.round(winProbability),
                
                factor_scores: factorScores,
                
                analysis: {
                    strengths: analysis.strengths,
                    concerns: analysis.concerns,
                    recommendations: analysis.recommendations,
                    reasoning: analysis.reasoning
                },
                
                metadata: {
                    scorer_version: this.version,
                    processing_time_ms: Math.round(processingTime),
                    timestamp: new Date().toISOString()
                }
            };
            
        } catch (error) {
            console.error('AI Scoring Error:', error);
            return this.generateFallbackScore(opportunity);
        }
    }

    /**
     * Normalize opportunity data from various government API formats
     */
    normalizeOpportunityData(opportunity) {
        return {
            id: opportunity.id || opportunity.notice_id || Math.random().toString(36),
            title: opportunity.title || opportunity.solicitation_number || 'Unknown Opportunity',
            description: opportunity.description || opportunity.synopsis || '',
            agency: opportunity.agency || opportunity.department || 'Unknown Agency',
            naics_codes: opportunity.naics_codes || opportunity.naics || [],
            set_aside: opportunity.set_aside_code || opportunity.set_aside || null,
            value: this.parseContractValue(opportunity.award_amount || opportunity.estimated_value),
            deadline: opportunity.response_date || opportunity.due_date || null,
            posted_date: opportunity.posted_date || opportunity.created_date || null,
            location: opportunity.place_of_performance || opportunity.location || null,
            classification: opportunity.classification_code || null,
            raw: opportunity
        };
    }

    /**
     * Calculate value alignment score based on NAICS, keywords, and requirements
     */
    calculateValueAlignment(opportunity) {
        let score = 50; // Base score

        // NAICS code matching
        const naicsMatch = this.calculateNAICSMatch(opportunity.naics_codes);
        score += naicsMatch * 20;

        // Keyword matching in title and description
        const keywordMatch = this.calculateKeywordMatch(opportunity.title, opportunity.description);
        score += keywordMatch * 15;

        // Set-aside matching
        if (opportunity.set_aside && this.companyProfile.smallBusiness) {
            if (opportunity.set_aside.includes('SB') || opportunity.set_aside.includes('SMALL')) {
                score += 10;
            }
        }

        // Agency preference
        const agencyMatch = this.calculateAgencyPreference(opportunity.agency);
        score += agencyMatch * 5;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate competitive analysis score
     */
    calculateCompetitiveAnalysis(opportunity) {
        let score = 60; // Base competitive score

        // Contract size analysis
        const valueRange = this.getValueRange(opportunity.value);
        switch(valueRange) {
            case 'small': score += 15; break;      // Less competition on smaller contracts
            case 'medium': score += 5; break;      // Moderate competition
            case 'large': score -= 10; break;      // High competition
            case 'mega': score -= 20; break;       // Very high competition
        }

        // Set-aside advantages
        if (opportunity.set_aside) {
            score += 15; // Set-asides have reduced competition
        }

        // Specialized requirements (less competition)
        if (this.hasSpecializedRequirements(opportunity)) {
            score += 10;
        }

        // Timeline pressure (may reduce competition)
        const daysLeft = this.calculateDaysLeft(opportunity.deadline);
        if (daysLeft < 7) {
            score += 5; // Rush jobs have less competition
        }

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate agency relationship score
     */
    calculateAgencyRelationship(opportunity) {
        let score = 40; // Base score

        // Preferred agency bonus
        const agencyScore = this.calculateAgencyPreference(opportunity.agency);
        score += agencyScore * 30;

        // Historical performance (simulated - would use real data)
        const historicalScore = this.getHistoricalPerformance(opportunity.agency);
        score += historicalScore * 20;

        // Agency spending patterns (simulated)
        const spendingPattern = this.analyzeAgencySpending(opportunity.agency);
        score += spendingPattern * 10;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate technical match score
     */
    calculateTechnicalMatch(opportunity) {
        let score = 50; // Base score

        // Capability matching
        const capabilityMatch = this.calculateCapabilityMatch(opportunity.title, opportunity.description);
        score += capabilityMatch * 25;

        // Security clearance requirements
        if (this.requiresSecurityClearance(opportunity) && this.companyProfile.securityClearance) {
            score += 15;
        } else if (this.requiresSecurityClearance(opportunity) && !this.companyProfile.securityClearance) {
            score -= 20;
        }

        // Technical complexity assessment
        const complexityScore = this.assessTechnicalComplexity(opportunity);
        score += complexityScore * 10;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate financial viability score
     */
    calculateFinancialViability(opportunity) {
        let score = 70; // Base score

        // Contract size vs company capacity
        if (opportunity.value > this.companyProfile.maxContractValue) {
            score -= 30; // Too large for company
        } else if (opportunity.value > this.companyProfile.maxContractValue * 0.8) {
            score -= 10; // Stretch but manageable
        } else if (opportunity.value < this.companyProfile.maxContractValue * 0.1) {
            score -= 5; // May be too small to be worthwhile
        }

        // Payment terms assessment (simulated)
        const paymentScore = this.assessPaymentTerms(opportunity);
        score += paymentScore * 10;

        // ROI potential
        const roiScore = this.calculateROIPotential(opportunity);
        score += roiScore * 15;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate time constraints score
     */
    calculateTimeConstraints(opportunity) {
        let score = 70; // Base score

        const daysLeft = this.calculateDaysLeft(opportunity.deadline);
        
        if (daysLeft <= 0) {
            score = 0; // Expired
        } else if (daysLeft <= 3) {
            score = 20; // Very tight
        } else if (daysLeft <= 7) {
            score = 40; // Tight but doable
        } else if (daysLeft <= 14) {
            score = 70; // Reasonable timeline
        } else if (daysLeft <= 30) {
            score = 90; // Good timeline
        } else {
            score = 85; // Very generous timeline
        }

        // Adjust based on proposal complexity
        const complexity = this.assessProposalComplexity(opportunity);
        score -= complexity * 20;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate risk assessment score
     */
    calculateRiskAssessment(opportunity) {
        let score = 80; // Base low-risk score

        // New agency risk
        if (!this.hasWorkedWithAgency(opportunity.agency)) {
            score -= 10;
        }

        // Large contract risk
        if (opportunity.value > this.companyProfile.maxContractValue * 0.5) {
            score -= 10;
        }

        // Tight timeline risk
        const daysLeft = this.calculateDaysLeft(opportunity.deadline);
        if (daysLeft <= 7) {
            score -= 15;
        }

        // Complex requirements risk
        if (this.hasComplexRequirements(opportunity)) {
            score -= 10;
        }

        // Competition risk
        if (!opportunity.set_aside && opportunity.value > 1000000) {
            score -= 10; // High competition risk
        }

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate weighted overall score
     */
    calculateWeightedScore(factorScores) {
        let weightedSum = 0;
        let totalWeight = 0;

        for (const [factor, score] of Object.entries(factorScores)) {
            const weight = this.modelWeights[factor] || 0;
            weightedSum += score * weight;
            totalWeight += weight;
        }

        return totalWeight > 0 ? weightedSum / totalWeight : 50;
    }

    /**
     * Generate recommendation based on overall score and factors
     */
    generateRecommendation(overallScore, factorScores) {
        if (overallScore >= 80) {
            return { action: 'pursue', priority: 'high', reason: 'Excellent opportunity match' };
        } else if (overallScore >= 65) {
            return { action: 'pursue', priority: 'medium', reason: 'Good opportunity with solid potential' };
        } else if (overallScore >= 50) {
            return { action: 'analyze', priority: 'medium', reason: 'Mixed signals - requires detailed analysis' };
        } else if (overallScore >= 35) {
            return { action: 'analyze', priority: 'low', reason: 'Significant concerns but may have potential' };
        } else {
            return { action: 'pass', priority: 'low', reason: 'Poor fit or high risk' };
        }
    }

    /**
     * Calculate confidence in the scoring
     */
    calculateConfidence(factorScores, opportunity) {
        let confidence = 0.7; // Base confidence

        // More data = higher confidence
        const dataQuality = this.assessDataQuality(opportunity);
        confidence += dataQuality * 0.2;

        // Consistent factor scores = higher confidence
        const scoreVariance = this.calculateScoreVariance(factorScores);
        confidence += (1 - scoreVariance) * 0.1;

        return Math.max(0.3, Math.min(1.0, confidence));
    }

    /**
     * Calculate win probability
     */
    calculateWinProbability(overallScore, factorScores) {
        let baseProbability = (overallScore - 30) * 1.2; // Scale from score

        // Adjust based on specific factors
        baseProbability += (factorScores.agencyRelationship - 50) * 0.3;
        baseProbability += (factorScores.technicalMatch - 50) * 0.2;
        baseProbability -= (100 - factorScores.competitiveAnalysis) * 0.1;

        return Math.max(10, Math.min(90, baseProbability));
    }

    /**
     * Generate detailed analysis with strengths, concerns, and recommendations
     */
    generateDetailedAnalysis(opportunity, factorScores, overallScore) {
        const strengths = [];
        const concerns = [];
        const recommendations = [];

        // Analyze each factor
        if (factorScores.valueAlignment > 70) {
            strengths.push('Strong alignment with company capabilities and NAICS codes');
        } else if (factorScores.valueAlignment < 40) {
            concerns.push('Poor fit with current capabilities - may need teaming');
        }

        if (factorScores.competitiveAnalysis > 70) {
            strengths.push('Favorable competitive landscape');
        } else if (factorScores.competitiveAnalysis < 40) {
            concerns.push('High competition expected');
        }

        if (factorScores.timeConstraints < 40) {
            concerns.push('Very tight timeline for proposal preparation');
            recommendations.push('Consider early no-bid decision if timeline is unworkable');
        }

        if (factorScores.financialViability > 80) {
            strengths.push('Excellent financial opportunity');
        } else if (factorScores.financialViability < 40) {
            concerns.push('Financial terms may not be favorable');
        }

        // Generate reasoning
        const reasoning = this.generateScoreReasoning(overallScore, factorScores);

        return { strengths, concerns, recommendations, reasoning };
    }

    /**
     * Generate human-readable reasoning for the score
     */
    generateScoreReasoning(overallScore, factorScores) {
        const topFactors = Object.entries(factorScores)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3)
            .map(([factor, score]) => ({ factor, score }));

        let reasoning = `Overall score of ${overallScore.toFixed(1)} based on `;
        reasoning += topFactors.map(f => `${f.factor} (${f.score.toFixed(0)})`).join(', ');
        reasoning += '. ';

        if (overallScore > 80) {
            reasoning += 'This is a high-value opportunity with strong alignment to company strengths.';
        } else if (overallScore > 60) {
            reasoning += 'This opportunity shows good potential but requires careful evaluation.';
        } else {
            reasoning += 'This opportunity has significant challenges that need to be addressed.';
        }

        return reasoning;
    }

    // Helper methods for calculations
    calculateNAICSMatch(naicsCodes) {
        if (!naicsCodes || naicsCodes.length === 0) return 0.3;
        
        const matches = naicsCodes.filter(code => 
            this.companyProfile.primaryNAICS.some(primary => 
                code.startsWith(primary.substring(0, 4))
            )
        );
        
        return matches.length / naicsCodes.length;
    }

    calculateKeywordMatch(title, description) {
        const text = (title + ' ' + description).toLowerCase();
        const matches = this.companyProfile.capabilities.filter(cap => 
            text.includes(cap.toLowerCase())
        );
        return matches.length / this.companyProfile.capabilities.length;
    }

    calculateAgencyPreference(agency) {
        if (!agency) return 0.3;
        return this.companyProfile.preferredAgencies.some(pref => 
            agency.toLowerCase().includes(pref.toLowerCase())
        ) ? 1.0 : 0.3;
    }

    parseContractValue(value) {
        if (typeof value === 'number') return value;
        if (typeof value === 'string') {
            const cleaned = value.replace(/[,$]/g, '');
            const num = parseFloat(cleaned);
            if (value.toLowerCase().includes('m')) return num * 1000000;
            if (value.toLowerCase().includes('k')) return num * 1000;
            return num || 0;
        }
        return 0;
    }

    calculateDaysLeft(deadline) {
        if (!deadline) return 30; // Default assumption
        const deadlineDate = new Date(deadline);
        const today = new Date();
        const diffTime = deadlineDate - today;
        return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
    }

    getValueRange(value) {
        if (value < 250000) return 'small';
        if (value < 1000000) return 'medium';
        if (value < 10000000) return 'large';
        return 'mega';
    }

    // Simplified implementations for demo purposes
    hasSpecializedRequirements(opportunity) {
        const text = (opportunity.title + ' ' + opportunity.description).toLowerCase();
        return text.includes('clearance') || text.includes('specialized') || text.includes('custom');
    }

    getHistoricalPerformance(agency) { return Math.random() * 0.5 + 0.3; }
    analyzeAgencySpending(agency) { return Math.random() * 0.3 + 0.2; }
    calculateCapabilityMatch(title, description) { return Math.random() * 0.4 + 0.3; }
    requiresSecurityClearance(opportunity) { 
        return (opportunity.title + opportunity.description).toLowerCase().includes('clearance'); 
    }
    assessTechnicalComplexity(opportunity) { return Math.random() * 0.2; }
    assessPaymentTerms(opportunity) { return Math.random() * 0.3 + 0.4; }
    calculateROIPotential(opportunity) { return Math.random() * 0.3 + 0.5; }
    assessProposalComplexity(opportunity) { return Math.random() * 0.3; }
    hasWorkedWithAgency(agency) { return Math.random() > 0.6; }
    hasComplexRequirements(opportunity) { return Math.random() > 0.7; }
    assessDataQuality(opportunity) { return Math.random() * 0.3 + 0.6; }
    calculateScoreVariance(scores) { 
        const values = Object.values(scores);
        const mean = values.reduce((a, b) => a + b) / values.length;
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
        return Math.min(1, variance / 1000); // Normalize
    }

    /**
     * Fallback scoring when main algorithm fails
     */
    generateFallbackScore(opportunity) {
        return {
            opportunity_id: opportunity.id || 'unknown',
            overall_score: 60.0,
            recommendation: 'analyze',
            confidence: 50,
            win_probability: 55,
            factor_scores: {
                valueAlignment: 60,
                competitiveAnalysis: 60,
                agencyRelationship: 50,
                technicalMatch: 60,
                financialViability: 70,
                timeConstraints: 60,
                riskAssessment: 70
            },
            analysis: {
                strengths: ['Opportunity identified'],
                concerns: ['Limited data for analysis'],
                recommendations: ['Gather more information before bidding'],
                reasoning: 'Fallback scoring due to insufficient data'
            },
            metadata: {
                scorer_version: this.version,
                processing_time_ms: 1,
                timestamp: new Date().toISOString(),
                fallback: true
            }
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIOpportunityScorer;
} else {
    window.AIOpportunityScorer = AIOpportunityScorer;
}

console.log('🧠 KBI Labs AI Opportunity Scorer loaded successfully');