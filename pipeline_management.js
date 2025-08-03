// Pipeline Management System for SMB Contractors
// Kanban-style pipeline with drag-and-drop functionality

const PipelineManagement = () => {
    const [opportunities, setOpportunities] = useState([]);
    const [pipelineData, setPipelineData] = useState({
        watching: [],
        analyzing: [],
        pursuing: [],
        submitted: [],
        awarded: [],
        lost: []
    });
    const [draggedItem, setDraggedItem] = useState(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedOpportunity, setSelectedOpportunity] = useState(null);

    // Pipeline stages configuration
    const pipelineStages = [
        {
            id: 'watching',
            title: 'Watching',
            subtitle: 'Monitoring for updates',
            color: 'var(--gray-500)',
            icon: 'fas fa-eye',
            description: 'Opportunities we\'re monitoring but haven\'t decided to pursue'
        },
        {
            id: 'analyzing',
            title: 'Analyzing',
            subtitle: 'Go/No-Go decision pending',
            color: 'var(--warning-orange)',
            icon: 'fas fa-brain',
            description: 'Under analysis for pursuit decision'
        },
        {
            id: 'pursuing',
            title: 'Pursuing',
            subtitle: 'Active pursuit',
            color: 'var(--primary-blue)',
            icon: 'fas fa-rocket',
            description: 'Actively developing proposals'
        },
        {
            id: 'submitted',
            title: 'Submitted',
            subtitle: 'Awaiting results',
            color: 'var(--success-green)',
            icon: 'fas fa-paper-plane',
            description: 'Proposals submitted, awaiting award decisions'
        },
        {
            id: 'awarded',
            title: 'Won',
            subtitle: 'Successful awards',
            color: 'var(--success-green)',
            icon: 'fas fa-trophy',
            description: 'Successfully awarded contracts'
        },
        {
            id: 'lost',
            title: 'Lost',
            subtitle: 'Unsuccessful bids',
            color: 'var(--danger-red)',
            icon: 'fas fa-times-circle',
            description: 'Unsuccessful proposals - lessons learned'
        }
    ];

    useEffect(() => {
        loadPipelineData();
    }, []);

    const loadPipelineData = async () => {
        try {
            // Load opportunities from API
            const oppsResponse = await fetch('/api/opportunities');
            const opps = await oppsResponse.json();
            setOpportunities(opps);

            // Load pipeline data (this would come from backend in real implementation)
            const mockPipelineData = {
                watching: opps.slice(0, 3).map(opp => ({ ...opp, stage: 'watching', notes: '', priority: 'medium' })),
                analyzing: opps.slice(3, 5).map(opp => ({ ...opp, stage: 'analyzing', notes: 'AI analysis pending', priority: 'high' })),
                pursuing: opps.slice(5, 6).map(opp => ({ ...opp, stage: 'pursuing', notes: 'Proposal in development', priority: 'high' })),
                submitted: [],
                awarded: [],
                lost: []
            };
            setPipelineData(mockPipelineData);
        } catch (error) {
            console.error('Error loading pipeline data:', error);
        }
    };

    const handleDragStart = (e, opportunity, fromStage) => {
        setDraggedItem({ opportunity, fromStage });
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    };

    const handleDrop = (e, toStage) => {
        e.preventDefault();
        if (!draggedItem) return;

        const { opportunity, fromStage } = draggedItem;
        
        // Update pipeline data
        setPipelineData(prev => {
            const newData = { ...prev };
            
            // Remove from old stage
            newData[fromStage] = newData[fromStage].filter(opp => opp.id !== opportunity.id);
            
            // Add to new stage
            const updatedOpportunity = { ...opportunity, stage: toStage };
            newData[toStage] = [...newData[toStage], updatedOpportunity];
            
            return newData;
        });

        setDraggedItem(null);
        
        // In real implementation, this would sync with backend
        console.log(`Moved ${opportunity.title} from ${fromStage} to ${toStage}`);
    };

    const getTotalValue = (stage) => {
        return pipelineData[stage].reduce((sum, opp) => sum + (opp.estimated_value || 0), 0);
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'var(--danger-red)';
            case 'medium': return 'var(--warning-orange)';
            case 'low': return 'var(--success-green)';
            default: return 'var(--gray-400)';
        }
    };

    const OpportunityCard = ({ opportunity, stage }) => {
        const daysLeft = getDaysUntil(opportunity.response_deadline);
        const isUrgent = daysLeft <= 7;

        return (
            <div
                className="pipeline-opportunity-card"
                draggable
                onDragStart={(e) => handleDragStart(e, opportunity, stage)}
                onClick={() => setSelectedOpportunity(opportunity)}
                style={{
                    border: `2px solid ${isUrgent ? 'var(--danger-red)' : 'var(--gray-200)'}`,
                    borderRadius: '8px',
                    padding: '12px',
                    marginBottom: '8px',
                    backgroundColor: 'white',
                    cursor: 'grab',
                    transition: 'all 0.2s',
                    position: 'relative'
                }}
                onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                }}
                onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                }}
            >
                {/* Priority indicator */}
                <div style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: getPriorityColor(opportunity.priority || 'medium')
                }}></div>

                <div style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '4px', paddingRight: '16px' }}>
                    {opportunity.title}
                </div>
                
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-600)', marginBottom: '8px' }}>
                    {opportunity.agency}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--gray-800)' }}>
                        {formatCurrency(opportunity.estimated_value || 0)}
                    </span>
                    <span style={{ 
                        fontSize: '0.75rem', 
                        color: isUrgent ? 'var(--danger-red)' : 'var(--gray-600)',
                        fontWeight: isUrgent ? '600' : 'normal'
                    }}>
                        {daysLeft} days left
                    </span>
                </div>

                {opportunity.notes && (
                    <div style={{ 
                        fontSize: '0.75rem', 
                        color: 'var(--gray-600)',
                        fontStyle: 'italic',
                        borderTop: '1px solid var(--gray-200)',
                        paddingTop: '6px',
                        marginTop: '6px'
                    }}>
                        {opportunity.notes}
                    </div>
                )}

                <div style={{ display: 'flex', gap: '4px', marginTop: '8px' }}>
                    <span className="badge badge-info" style={{ fontSize: '0.625rem' }}>
                        {opportunity.set_aside_type || 'Unrestricted'}
                    </span>
                    {opportunity.naics_code && (
                        <span className="badge badge-success" style={{ fontSize: '0.625rem' }}>
                            {opportunity.naics_code}
                        </span>
                    )}
                </div>
            </div>
        );
    };

    const PipelineColumn = ({ stage, stageData }) => {
        const count = pipelineData[stage.id].length;
        const totalValue = getTotalValue(stage.id);

        return (
            <div
                className="pipeline-column"
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, stage.id)}
                style={{
                    backgroundColor: 'var(--gray-50)',
                    borderRadius: '12px',
                    padding: '16px',
                    minHeight: '400px',
                    flex: '1',
                    minWidth: '280px'
                }}
            >
                {/* Column Header */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '16px',
                    paddingBottom: '12px',
                    borderBottom: `2px solid ${stage.color}`
                }}>
                    <i className={stage.icon} style={{ color: stage.color, fontSize: '1.1rem' }}></i>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: '600', color: 'var(--gray-800)', fontSize: '1rem' }}>
                            {stage.title}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--gray-600)' }}>
                            {stage.subtitle}
                        </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '1.25rem', fontWeight: '700', color: stage.color }}>
                            {count}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--gray-600)' }}>
                            {formatCurrency(totalValue)}
                        </div>
                    </div>
                </div>

                {/* Opportunities */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {pipelineData[stage.id].map(opportunity => (
                        <OpportunityCard
                            key={opportunity.id}
                            opportunity={opportunity}
                            stage={stage.id}
                        />
                    ))}
                </div>

                {/* Add Opportunity Button */}
                {(stage.id === 'watching' || stage.id === 'analyzing') && (
                    <button
                        className="btn"
                        style={{
                            width: '100%',
                            marginTop: '12px',
                            borderStyle: 'dashed',
                            borderColor: stage.color,
                            color: stage.color
                        }}
                        onClick={() => setShowAddModal(stage.id)}
                    >
                        <i className="fas fa-plus"></i>
                        Add Opportunity
                    </button>
                )}
            </div>
        );
    };

    return (
        <div>
            {/* Pipeline Header */}
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                marginBottom: '24px',
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '12px',
                border: '1px solid var(--gray-200)'
            }}>
                <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--gray-800)', margin: 0 }}>
                        Pipeline Management
                    </h2>
                    <p style={{ color: 'var(--gray-600)', margin: '4px 0 0 0', fontSize: '0.875rem' }}>
                        Drag opportunities between stages to track your pursuit pipeline
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn">
                        <i className="fas fa-filter"></i> Filter
                    </button>
                    <button className="btn">
                        <i className="fas fa-download"></i> Export
                    </button>
                    <button className="btn btn-primary">
                        <i className="fas fa-chart-line"></i> Pipeline Report
                    </button>
                </div>
            </div>

            {/* Pipeline Statistics */}
            <div className="kpi-grid" style={{ marginBottom: '24px' }}>
                <KPICard
                    title="Active Opportunities"
                    value={Object.values(pipelineData).flat().length}
                    change={8}
                    icon="fas fa-stream"
                    iconColor="var(--primary-blue)"
                />
                <KPICard
                    title="Total Pipeline Value"
                    value={formatCurrency(Object.values(pipelineData).flat().reduce((sum, opp) => sum + (opp.estimated_value || 0), 0))}
                    change={15}
                    icon="fas fa-dollar-sign"
                    iconColor="var(--success-green)"
                />
                <KPICard
                    title="Pursuing This Month"
                    value={pipelineData.pursuing.length + pipelineData.submitted.length}
                    change={12}
                    icon="fas fa-rocket"
                    iconColor="var(--warning-orange)"
                />
                <KPICard
                    title="Win Rate (YTD)"
                    value="67%"
                    change={5}
                    icon="fas fa-trophy"
                    iconColor="var(--success-green)"
                />
            </div>

            {/* Pipeline Board */}
            <div style={{
                display: 'flex',
                gap: '16px',
                overflowX: 'auto',
                paddingBottom: '16px'
            }}>
                {pipelineStages.map(stage => (
                    <PipelineColumn
                        key={stage.id}
                        stage={stage}
                        stageData={pipelineData[stage.id]}
                    />
                ))}
            </div>

            {/* Quick Actions */}
            <div style={{
                marginTop: '24px',
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '12px',
                border: '1px solid var(--gray-200)'
            }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '16px' }}>
                    Quick Actions
                </h3>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <button className="btn btn-primary">
                        <i className="fas fa-brain"></i> Analyze All Watching
                    </button>
                    <button className="btn">
                        <i className="fas fa-calendar-check"></i> Review Deadlines
                    </button>
                    <button className="btn">
                        <i className="fas fa-users"></i> Assign Team Members
                    </button>
                    <button className="btn">
                        <i className="fas fa-chart-pie"></i> Pipeline Analytics
                    </button>
                </div>
            </div>
        </div>
    );
};

// Export for use in main dashboard
window.PipelineManagement = PipelineManagement;