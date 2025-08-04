/**
 * KBI Labs Data Visualizer
 * 
 * Advanced visualization system for government contracting data
 * Creates compelling charts, graphs, and interactive displays
 */

class DataVisualizer {
    constructor() {
        this.charts = new Map();
        this.chartConfigs = new Map();
        this.animationQueue = [];
        this.isInitialized = false;
        
        // Chart color schemes
        this.colorSchemes = {
            primary: ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe'],
            success: ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5'],
            warning: ['#f59e0b', '#fbbf24', '#fcd34d', '#fde68a', '#fef3c7'],
            danger: ['#ef4444', '#f87171', '#fca5a5', '#fecaca', '#fee2e2'],
            purple: ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe'],
            gradient: {
                blue: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                green: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
                orange: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                purple: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
            }
        };

        this.initializeChartDefaults();
    }

    /**
     * Initialize default chart configurations
     */
    initializeChartDefaults() {
        // Plotly default config
        this.plotlyConfig = {
            displayModeBar: false,
            responsive: true
        };

        // Chart.js default config
        this.chartJSDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                x: {
                    grid: {
                        color: '#f1f5f9'
                    }
                }
            }
        };
    }

    /**
     * Create opportunity pipeline funnel chart
     */
    createOpportunityFunnel(containerId, data) {
        const stages = [
            { name: 'Total Opportunities', value: data.totalOpportunities || 0 },
            { name: 'Under Analysis', value: data.analyzeOpportunities || 0 },
            { name: 'Pursue Decision', value: data.pursueOpportunities || 0 },
            { name: 'Proposal Submitted', value: Math.floor((data.pursueOpportunities || 0) * 0.8) },
            { name: 'Award Expected', value: Math.floor((data.pursueOpportunities || 0) * 0.3) }
        ];

        const trace = {
            type: 'funnel',
            y: stages.map(s => s.name),
            x: stages.map(s => s.value),
            textinfo: 'value+percent initial',
            textposition: 'inside',
            textfont: { color: 'white', size: 14 },
            marker: {
                color: this.colorSchemes.primary,
                line: {
                    width: 2,
                    color: 'white'
                }
            },
            connector: {
                line: {
                    color: '#64748b',
                    dash: 'dot',
                    width: 2
                }
            }
        };

        const layout = {
            title: {
                text: 'Opportunity Pipeline',
                font: { size: 16, color: '#1e293b' }
            },
            margin: { l: 100, r: 50, t: 50, b: 50 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Inter, system-ui, sans-serif' }
        };

        Plotly.newPlot(containerId, [trace], layout, this.plotlyConfig);
        this.charts.set(containerId, { type: 'funnel', data: stages });
    }

    /**
     * Create agency spending distribution chart
     */
    createAgencySpendingChart(containerId, agencyData) {
        const agencies = agencyData.slice(0, 8);
        const trace = {
            type: 'bar',
            x: agencies.map(a => a.name.length > 15 ? a.name.substring(0, 15) + '...' : a.name),
            y: agencies.map(a => parseFloat(a.totalSpending.replace(/[$,MBK]/g, ''))),
            marker: {
                color: this.colorSchemes.success,
                opacity: 0.8,
                line: {
                    color: '#10b981',
                    width: 1
                }
            },
            text: agencies.map(a => a.totalSpending),
            textposition: 'outside',
            textfont: { color: '#1e293b', size: 12 }
        };

        const layout = {
            title: {
                text: 'Top Agency Spending',
                font: { size: 16, color: '#1e293b' }
            },
            margin: { l: 60, r: 50, t: 50, b: 100 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: {
                tickangle: -45,
                tickfont: { size: 10 }
            },
            yaxis: {
                title: 'Spending ($M)',
                tickfont: { size: 11 }
            },
            font: { family: 'Inter, system-ui, sans-serif' }
        };

        Plotly.newPlot(containerId, [trace], layout, this.plotlyConfig);
        this.charts.set(containerId, { type: 'agency-spending', data: agencies });
    }

    /**
     * Create regulatory impact timeline
     */
    createRegulatoryTimeline(containerId, regulationsData) {
        const regulations = regulationsData.slice(0, 10);
        
        const trace = {
            type: 'scatter',
            mode: 'markers+text',
            x: regulations.map(r => r.publicationDate),
            y: regulations.map(r => r.impactScore),
            marker: {
                size: regulations.map(r => Math.max(8, r.impactScore / 8)),
                color: regulations.map(r => {
                    if (r.impact === 'critical') return '#ef4444';
                    if (r.impact === 'high') return '#f59e0b';
                    if (r.impact === 'medium') return '#3b82f6';
                    return '#10b981';
                }),
                opacity: 0.7,
                line: {
                    width: 2,
                    color: 'white'
                }
            },
            text: regulations.map(r => r.title.length > 20 ? r.title.substring(0, 20) + '...' : r.title),
            textposition: 'top center',
            textfont: { size: 10, color: '#1e293b' },
            hovertemplate: '<b>%{text}</b><br>Impact Score: %{y}<br>Date: %{x}<extra></extra>'
        };

        const layout = {
            title: {
                text: 'Regulatory Impact Timeline',
                font: { size: 16, color: '#1e293b' }
            },
            margin: { l: 60, r: 50, t: 50, b: 60 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: {
                title: 'Publication Date',
                type: 'date'
            },
            yaxis: {
                title: 'Impact Score',
                range: [0, 100]
            },
            font: { family: 'Inter, system-ui, sans-serif' }
        };

        Plotly.newPlot(containerId, [trace], layout, this.plotlyConfig);
        this.charts.set(containerId, { type: 'regulatory-timeline', data: regulations });
    }

    /**
     * Create opportunity value distribution donut chart
     */
    createValueDistributionChart(containerId, opportunities) {
        const ranges = [
            { label: '$0-$100K', min: 0, max: 100000, color: '#dbeafe' },
            { label: '$100K-$500K', min: 100000, max: 500000, color: '#93c5fd' },
            { label: '$500K-$1M', min: 500000, max: 1000000, color: '#60a5fa' },
            { label: '$1M-$5M', min: 1000000, max: 5000000, color: '#3b82f6' },
            { label: '$5M+', min: 5000000, max: Infinity, color: '#2563eb' }
        ];

        const distribution = ranges.map(range => {
            const count = opportunities.filter(opp => {
                const value = this.parseValue(opp.value);
                return value >= range.min && value < range.max;
            }).length;
            return { ...range, count };
        });

        const trace = {
            type: 'pie',
            labels: distribution.map(d => `${d.label} (${d.count})`),
            values: distribution.map(d => d.count),
            hole: 0.4,
            marker: {
                colors: distribution.map(d => d.color),
                line: {
                    color: 'white',
                    width: 2
                }
            },
            textinfo: 'percent',
            textposition: 'outside',
            textfont: { size: 12, color: '#1e293b' },
            hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        };

        const layout = {
            title: {
                text: 'Opportunity Value Distribution',
                font: { size: 16, color: '#1e293b' }
            },
            margin: { l: 50, r: 50, t: 50, b: 50 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Inter, system-ui, sans-serif' },
            annotations: [{
                text: `${opportunities.length}<br>Total Opps`,
                x: 0.5, y: 0.5,
                font: { size: 16, color: '#1e293b' },
                showarrow: false
            }]
        };

        Plotly.newPlot(containerId, [trace], layout, this.plotlyConfig);
        this.charts.set(containerId, { type: 'value-distribution', data: distribution });
    }

    /**
     * Create AI score vs win probability scatter plot
     */
    createAIScoreAnalysis(containerId, opportunities) {
        const traces = [];
        const recommendations = ['pursue', 'analyze', 'pass'];
        const colors = ['#10b981', '#f59e0b', '#ef4444'];

        recommendations.forEach((rec, index) => {
            const filteredOpps = opportunities.filter(opp => opp.recommendation === rec);
            
            traces.push({
                type: 'scatter',
                mode: 'markers',
                name: rec.charAt(0).toUpperCase() + rec.slice(1),
                x: filteredOpps.map(opp => opp.aiScore),
                y: filteredOpps.map(opp => opp.winProbability || Math.random() * 100),
                marker: {
                    size: 12,
                    color: colors[index],
                    opacity: 0.7,
                    line: {
                        width: 2,
                        color: 'white'
                    }
                },
                text: filteredOpps.map(opp => opp.title),
                hovertemplate: '<b>%{text}</b><br>AI Score: %{x}<br>Win Probability: %{y}%<extra></extra>'
            });
        });

        const layout = {
            title: {
                text: 'AI Score vs Win Probability',
                font: { size: 16, color: '#1e293b' }
            },
            margin: { l: 60, r: 50, t: 50, b: 60 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: {
                title: 'AI Score',
                range: [0, 100]
            },
            yaxis: {
                title: 'Win Probability (%)',
                range: [0, 100]
            },
            font: { family: 'Inter, system-ui, sans-serif' }
        };

        Plotly.newPlot(containerId, traces, layout, this.plotlyConfig);
        this.charts.set(containerId, { type: 'ai-analysis', data: opportunities });
    }

    /**
     * Create compliance tracking gauge chart
     */
    createComplianceGauge(containerId, complianceData) {
        const completedCount = complianceData.filter(item => item.status === 'completed').length;
        const percentage = Math.round((completedCount / complianceData.length) * 100);

        const trace = {
            type: 'indicator',
            mode: 'gauge+number+delta',
            value: percentage,
            domain: { x: [0, 1], y: [0, 1] },
            title: { 
                text: 'Compliance Status',
                font: { size: 16, color: '#1e293b' }
            },
            delta: { 
                reference: 80,
                increasing: { color: '#10b981' },
                decreasing: { color: '#ef4444' }
            },
            gauge: {
                axis: { range: [null, 100] },
                bar: { color: percentage >= 80 ? '#10b981' : percentage >= 60 ? '#f59e0b' : '#ef4444' },
                steps: [
                    { range: [0, 50], color: '#fee2e2' },
                    { range: [50, 80], color: '#fef3c7' },
                    { range: [80, 100], color: '#d1fae5' }
                ],
                threshold: {
                    line: { color: '#ef4444', width: 4 },
                    thickness: 0.75,
                    value: 90
                }
            }
        };

        const layout = {
            margin: { l: 50, r: 50, t: 50, b: 50 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Inter, system-ui, sans-serif' }
        };

        Plotly.newPlot(containerId, [trace], layout, this.plotlyConfig);
        this.charts.set(containerId, { type: 'compliance-gauge', data: { percentage, items: complianceData }});
    }

    /**
     * Create animated KPI cards
     */
    createAnimatedKPIs(containerSelector, kpiData) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        container.innerHTML = '';

        kpiData.forEach((kpi, index) => {
            const kpiCard = document.createElement('div');
            kpiCard.className = 'kpi-card animated';
            kpiCard.style.animationDelay = `${index * 0.1}s`;
            
            kpiCard.innerHTML = `
                <div class="kpi-icon ${kpi.type}">
                    <i class="${kpi.icon}"></i>
                </div>
                <div class="kpi-content">
                    <div class="kpi-label">${kpi.label}</div>
                    <div class="kpi-value" data-value="${kpi.rawValue || kpi.value}">0</div>
                    <div class="kpi-change ${kpi.changeType}">
                        <i class="fas ${kpi.changeType === 'positive' ? 'fa-arrow-up' : 'fa-arrow-down'}"></i>
                        ${kpi.change}
                    </div>
                </div>
            `;

            container.appendChild(kpiCard);

            // Animate value counting
            setTimeout(() => {
                this.animateValue(kpiCard.querySelector('.kpi-value'), kpi.value, kpi.rawValue);
            }, index * 100);
        });
    }

    /**
     * Animate number counting
     */
    animateValue(element, displayValue, rawValue = null) {
        const targetValue = rawValue || parseInt(displayValue.replace(/[^\d]/g, '')) || 0;
        const duration = 1500;
        const increment = targetValue / (duration / 16);
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= targetValue) {
                current = targetValue;
                clearInterval(timer);
            }

            if (displayValue.includes('$')) {
                element.textContent = this.formatCurrency(current);
            } else if (displayValue.includes('%')) {
                element.textContent = Math.round(current) + '%';
            } else {
                element.textContent = Math.round(current).toLocaleString();
            }
        }, 16);
    }

    /**
     * Create interactive data table with search and filters
     */
    createInteractiveTable(containerId, data, columns, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const tableHTML = `
            <div class="data-table-container">
                <div class="table-controls">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" placeholder="Search..." id="${containerId}-search">
                    </div>
                    <div class="table-filters">
                        ${options.filters ? options.filters.map(filter => `
                            <select id="${containerId}-filter-${filter.key}">
                                <option value="">All ${filter.label}</option>
                                ${filter.options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
                            </select>
                        `).join('') : ''}
                    </div>
                </div>
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead>
                            <tr>
                                ${columns.map(col => `<th data-sort="${col.key}">${col.label} <i class="fas fa-sort"></i></th>`).join('')}
                            </tr>
                        </thead>
                        <tbody id="${containerId}-tbody">
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        container.innerHTML = tableHTML;
        this.populateTable(`${containerId}-tbody`, data, columns);
        this.attachTableEventListeners(containerId, data, columns);
    }

    /**
     * Utility functions
     */
    parseValue(valueString) {
        const cleaned = valueString.replace(/[$,]/g, '');
        let multiplier = 1;
        if (cleaned.includes('M')) multiplier = 1000000;
        if (cleaned.includes('K')) multiplier = 1000;
        return parseFloat(cleaned) * multiplier;
    }

    formatCurrency(amount) {
        if (amount >= 1e9) return `$${(amount / 1e9).toFixed(1)}B`;
        if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}M`;
        if (amount >= 1e3) return `$${(amount / 1e3).toFixed(1)}K`;
        return `$${amount.toLocaleString()}`;
    }

    /**
     * Refresh all charts with new data
     */
    refreshAllCharts(dashboardData) {
        this.charts.forEach((chart, containerId) => {
            try {
                switch (chart.type) {
                    case 'funnel':
                        this.createOpportunityFunnel(containerId, dashboardData.kpis);
                        break;
                    case 'agency-spending':
                        this.createAgencySpendingChart(containerId, dashboardData.agencies);
                        break;
                    case 'regulatory-timeline':
                        this.createRegulatoryTimeline(containerId, dashboardData.regulations);
                        break;
                    case 'value-distribution':
                        this.createValueDistributionChart(containerId, dashboardData.opportunities);
                        break;
                    case 'ai-analysis':
                        this.createAIScoreAnalysis(containerId, dashboardData.opportunities);
                        break;
                    case 'compliance-gauge':
                        this.createComplianceGauge(containerId, dashboardData.compliance);
                        break;
                }
            } catch (error) {
                console.error(`Error refreshing chart ${containerId}:`, error);
            }
        });
    }

    /**
     * Add chart animation effects
     */
    addChartAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            .kpi-card.animated {
                animation: slideInUp 0.6s ease-out;
                opacity: 0;
                animation-fill-mode: forwards;
            }
            
            @keyframes slideInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .chart-container {
                opacity: 0;
                animation: fadeIn 1s ease-in-out forwards;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Initialize visualizer
     */
    initialize() {
        this.addChartAnimations();
        this.isInitialized = true;
        console.log('📊 Data Visualizer initialized successfully');
    }
}

// Create global instance
window.dataVisualizer = new DataVisualizer();

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.dataVisualizer.initialize();
    });
} else {
    window.dataVisualizer.initialize();
}

console.log('📈 KBI Labs Data Visualizer loaded successfully');