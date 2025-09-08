/**
 * Dashboard JavaScript for CopadoCon 2025 Hackathon
 * Handles real-time updates, charts, and user interactions
 */

class ObservabilityDashboard {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.incidents = [];
        this.metrics = {};
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
        this.setupCharts();
        
        // Refresh data every 30 seconds
        setInterval(() => this.refreshData(), 30000);
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateRealTimeData(data);
        };
        
        this.ws.onclose = () => {
            // Reconnect after 5 seconds
            setTimeout(() => this.setupWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Filter dropdowns
        document.getElementById('severity-filter').addEventListener('change', () => {
            this.filterIncidents();
        });
        
        document.getElementById('status-filter').addEventListener('change', () => {
            this.filterIncidents();
        });
        
        // Modal close
        document.getElementById('close-modal').addEventListener('click', () => {
            this.closeModal();
        });
        
        // Close modal on outside click
        document.getElementById('incident-modal').addEventListener('click', (e) => {
            if (e.target.id === 'incident-modal') {
                this.closeModal();
            }
        });
    }
    
    async loadInitialData() {
        try {
            // Load incidents with error handling
            try {
                await this.loadIncidents();
            } catch (incidentError) {
                console.error('Error loading incidents:', incidentError);
                this.incidents = [];
            }
            
            // Load metrics with error handling
            try {
                await this.loadMetrics();
            } catch (metricsError) {
                console.error('Error loading metrics:', metricsError);
                this.metrics = {};
            }
            
            this.updateDashboard();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    async loadIncidents() {
        const response = await fetch('/api/incidents');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        this.incidents = data.incidents || [];
    }
    
    async loadMetrics() {
        const response = await fetch('/api/metrics');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        this.metrics = await response.json();
    }
    
    async refreshData() {
        try {
            await this.loadInitialData();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }
    
    updateRealTimeData(data) {
        if (data.incidents) {
            this.incidents = data.incidents;
            this.updateIncidentsTable();
            this.updateStatsCards();
        }
    }
    
    updateDashboard() {
        this.updateStatsCards();
        this.updateIncidentsTable();
        this.updateCharts();
    }
    
    updateStatsCards() {
        const activeIncidents = this.incidents.filter(inc => inc.status !== 'resolved').length;
        const resolvedToday = this.incidents.filter(inc => {
            if (inc.status !== 'resolved' || !inc.resolved_at) return false;
            const resolvedDate = new Date(inc.resolved_at);
            const today = new Date();
            return resolvedDate.toDateString() === today.toDateString();
        }).length;
        
        const avgResolution = this.metrics.average_resolution_time_seconds || 0;
        const avgResolutionMinutes = Math.round(avgResolution / 60);
        
        const avgConfidence = this.incidents.length > 0 
            ? this.incidents.reduce((sum, inc) => sum + (inc.confidence || 0), 0) / this.incidents.length
            : 0;
        
        document.getElementById('active-incidents').textContent = activeIncidents;
        document.getElementById('resolved-today').textContent = resolvedToday;
        document.getElementById('avg-resolution').textContent = `${avgResolutionMinutes}m`;
        document.getElementById('ai-confidence').textContent = `${Math.round(avgConfidence * 100)}%`;
    }
    
    updateIncidentsTable() {
        const tbody = document.getElementById('incidents-table');
        tbody.innerHTML = '';
        
        const filteredIncidents = this.getFilteredIncidents();
        
        if (filteredIncidents.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-4 text-center text-gray-500">
                        No incidents found
                    </td>
                </tr>
            `;
            return;
        }
        
        filteredIncidents.forEach(incident => {
            const row = this.createIncidentRow(incident);
            tbody.appendChild(row);
        });
    }
    
    createIncidentRow(incident) {
        const row = document.createElement('tr');
        row.onclick = () => this.showIncidentDetails(incident.id);
        
        const createdAt = new Date(incident.created_at).toLocaleString();
        const confidence = Math.round((incident.confidence || 0) * 100);
        
        row.innerHTML = `
            <td>
                <div style="font-weight: 600; color: #1f2937; font-size: 0.875em; margin-bottom: 2px;">${incident.id}</div>
                <div style="color: #6b7280; font-size: 0.8em;">${incident.title}</div>
            </td>
            <td>
                <span class="severity-badge severity-${incident.severity}">
                    ${incident.severity}
                </span>
            </td>
            <td>
                <span class="status-badge status-${incident.status}">
                    ${incident.status}
                </span>
            </td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                    <span style="font-size: 0.75em; color: #6b7280; font-weight: 500;">${confidence}%</span>
                </div>
            </td>
            <td style="color: #6b7280; font-size: 0.8em;">
                ${createdAt}
            </td>
            <td>
                <button class="view-details-btn" onclick="event.stopPropagation(); dashboard.showIncidentDetails('${incident.id}')">
                    <i class="fas fa-eye" style="margin-right: 4px;"></i>View
                </button>
            </td>
        `;
        
        return row;
    }
    
    getFilteredIncidents() {
        const severityFilter = document.getElementById('severity-filter').value;
        const statusFilter = document.getElementById('status-filter').value;
        
        return this.incidents.filter(incident => {
            if (severityFilter && incident.severity !== severityFilter) return false;
            if (statusFilter && incident.status !== statusFilter) return false;
            return true;
        });
    }
    
    filterIncidents() {
        this.updateIncidentsTable();
    }
    
    async showIncidentDetails(incidentId) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}`);
            const incident = await response.json();
            
            this.renderIncidentModal(incident);
            const modal = document.getElementById('incident-modal');
            modal.style.display = 'flex';
        } catch (error) {
            console.error('Error loading incident details:', error);
            this.showError('Failed to load incident details');
        }
    }
    
    renderIncidentModal(incident) {
        document.getElementById('modal-title').textContent = `Incident ${incident.id}`;
        
        const modalContent = document.getElementById('modal-content');
        modalContent.innerHTML = `
            <!-- Basic Information Section -->
            <div class="modal-section">
                <h4 class="modal-section-title">
                    <i class="fas fa-info-circle" style="color: #3b82f6;"></i>
                    Basic Information
                </h4>
                <div class="modal-grid">
                    <div class="modal-field">
                        <span class="modal-label">Title</span>
                        <div class="modal-value">${incident.title}</div>
                    </div>
                    <div class="modal-field">
                        <span class="modal-label">Severity</span>
                        <div class="modal-value">
                            <span class="severity-badge severity-${incident.severity.toLowerCase()}">${incident.severity.toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="modal-field">
                        <span class="modal-label">Status</span>
                        <div class="modal-value">
                            <span class="status-badge status-${incident.status.toLowerCase()}">${incident.status.toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="modal-field">
                        <span class="modal-label">Created</span>
                        <div class="modal-value">${new Date(incident.created_at).toLocaleString()}</div>
                    </div>
                </div>
                <div class="modal-field">
                    <span class="modal-label">Description</span>
                    <div class="modal-value">${incident.description}</div>
                </div>
            </div>
                
            ${incident.analysis ? `
            <!-- AI Analysis Section -->
            <div class="modal-section">
                <h4 class="modal-section-title">
                    <i class="fas fa-brain" style="color: #8b5cf6;"></i>
                    AI Analysis
                </h4>
                <div class="analysis-card">
                    <div class="modal-grid">
                        <div class="modal-field">
                            <span class="modal-label">Confidence</span>
                            <div class="confidence-display">
                                <i class="fas fa-chart-line" style="color: #059669;"></i>
                                ${Math.round((incident.analysis.confidence || 0) * 100)}%
                            </div>
                        </div>
                        <div class="modal-field">
                            <span class="modal-label">Analysis Time</span>
                            <div class="modal-value">${incident.analysis.analysis_timestamp ? new Date(incident.analysis.analysis_timestamp).toLocaleString() : 'N/A'}</div>
                        </div>
                    </div>
                    <div class="modal-field">
                        <span class="modal-label">Root Cause</span>
                        <div class="modal-value">${incident.analysis.root_cause || 'Analysis pending...'}</div>
                    </div>
                    ${incident.analysis.impact_assessment ? `
                    <div class="modal-field">
                        <span class="modal-label">Impact Assessment</span>
                        <div class="modal-value">${incident.analysis.impact_assessment}</div>
                    </div>
                    ` : ''}
                    ${incident.analysis.suggested_actions && incident.analysis.suggested_actions.length > 0 ? `
                    <div class="modal-field">
                        <span class="modal-label">Suggested Actions</span>
                        <ul class="action-list">
                            ${incident.analysis.suggested_actions.map(action => `<li class="action-item">${action}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}
                </div>
            </div>
            ` : ''}
                
            <!-- Detected Signals Section -->
            <div class="modal-section">
                <h4 class="modal-section-title">
                    <i class="fas fa-satellite-dish" style="color: #f59e0b;"></i>
                    Detected Signals (${incident.signals ? incident.signals.length : 0})
                </h4>
                ${incident.signals && incident.signals.length > 0 ? `
                    ${incident.signals.map(signal => `
                    <div class="signal-card">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                            <span class="signal-type">${signal.type.toUpperCase()}</span>
                            <span class="signal-timestamp">${new Date(signal.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="modal-value" style="margin-bottom: 8px;">${signal.description}</div>
                        <div style="font-size: 0.75em; color: #6b7280;">
                            <i class="fas fa-server" style="margin-right: 4px;"></i>Source: ${signal.source} | 
                            <i class="fas fa-cube" style="margin-right: 4px;"></i>Component: ${signal.component}
                        </div>
                    </div>
                    `).join('')}
                ` : `
                    <div style="text-align: center; padding: 40px; color: #6b7280;">
                        <i class="fas fa-search" style="font-size: 2em; margin-bottom: 16px; opacity: 0.5;"></i>
                        <p>No signals detected yet</p>
                    </div>
                `}
            </div>
        `;
    }
    
    async resolveIncident(incidentId) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}/resolve`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.closeModal();
                this.refreshData();
                this.showSuccess('Incident resolved successfully');
            } else {
                throw new Error('Failed to resolve incident');
            }
        } catch (error) {
            console.error('Error resolving incident:', error);
            this.showError('Failed to resolve incident');
        }
    }
    
    closeModal() {
        document.getElementById('incident-modal').style.display = 'none';
    }
    
    setupCharts() {
        this.setupSeverityChart();
        this.setupTrendChart();
    }
    
    setupSeverityChart() {
        const ctx = document.getElementById('severity-chart').getContext('2d');
        this.charts.severity = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#DC2626', '#EA580C', '#D97706', '#059669']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    setupTrendChart() {
        const ctx = document.getElementById('trend-chart').getContext('2d');
        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Incidents Created',
                    data: [],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Incidents Resolved',
                    data: [],
                    borderColor: '#059669',
                    backgroundColor: 'rgba(5, 150, 105, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    updateCharts() {
        this.updateSeverityChart();
        this.updateTrendChart();
    }
    
    updateSeverityChart() {
        const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
        
        this.incidents.forEach(incident => {
            if (incident.status !== 'resolved') {
                severityCounts[incident.severity]++;
            }
        });
        
        this.charts.severity.data.datasets[0].data = [
            severityCounts.critical,
            severityCounts.high,
            severityCounts.medium,
            severityCounts.low
        ];
        
        this.charts.severity.update();
    }
    
    updateTrendChart() {
        // Generate last 24 hours data
        const hours = [];
        const createdData = [];
        const resolvedData = [];
        
        for (let i = 23; i >= 0; i--) {
            const hour = new Date();
            hour.setHours(hour.getHours() - i);
            hours.push(hour.getHours() + ':00');
            
            const hourStart = new Date(hour);
            hourStart.setMinutes(0, 0, 0);
            const hourEnd = new Date(hourStart);
            hourEnd.setHours(hourEnd.getHours() + 1);
            
            const created = this.incidents.filter(inc => {
                const createdAt = new Date(inc.created_at);
                return createdAt >= hourStart && createdAt < hourEnd;
            }).length;
            
            const resolved = this.incidents.filter(inc => {
                if (!inc.resolved_at) return false;
                const resolvedAt = new Date(inc.resolved_at);
                return resolvedAt >= hourStart && resolvedAt < hourEnd;
            }).length;
            
            createdData.push(created);
            resolvedData.push(resolved);
        }
        
        this.charts.trend.data.labels = hours;
        this.charts.trend.data.datasets[0].data = createdData;
        this.charts.trend.data.datasets[1].data = resolvedData;
        this.charts.trend.update();
    }
    
    showError(message) {
        // Simple error notification - could be enhanced with a proper notification system
        alert(`Error: ${message}`);
    }
    
    showSuccess(message) {
        // Simple success notification - could be enhanced with a proper notification system
        alert(`Success: ${message}`);
    }
}

// Initialize dashboard when page loads
const dashboard = new ObservabilityDashboard();
window.dashboard = dashboard; // Make it globally accessible
