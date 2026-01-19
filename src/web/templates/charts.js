// charts.js - Chart.js implementations for PURPLE team dashboards

// Global chart instances
let asymmetryChart = null;
let detailChart = null;

// ===== PATIENT DASHBOARD CHARTS =====

// Initialize Patient Asymmetry Chart
function initializePatientCharts() {
    const ctx = document.getElementById('asymmetryChart');
    if (!ctx) return;

    // Sample data for last 7 days
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Today'];
    const asymmetryData = [18, 15, 22, 19, 14, 16, 12];

    // Determine colors based on values (following 20% rule)
    const pointColors = asymmetryData.map(value =>
        value > 20 ? '#DC3545' : value > 15 ? '#FFC107' : '#28A745'
    );

    // Clear existing chart if any
    if (asymmetryChart) {
        asymmetryChart.destroy();
    }

    asymmetryChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Asymmetry %',
                data: asymmetryData,
                borderColor: '#2E5AAC',
                backgroundColor: 'rgba(46, 90, 172, 0.1)',
                pointBackgroundColor: pointColors,
                pointBorderColor: pointColors,
                pointRadius: 6,
                pointHoverRadius: 8,
                borderWidth: 3,
                fill: true,
                tension: 0.3
            },
                {
                    label: 'Critical Threshold (20%)',
                    data: Array(days.length).fill(20),
                    borderColor: '#DC3545',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Warning Threshold (15%)',
                    data: Array(days.length).fill(15),
                    borderColor: '#FFC107',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    fill: false,
                    pointRadius: 0
                }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 30,
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '%';

                                // Add status indicator in tooltip
                                if (context.datasetIndex === 0) {
                                    const value = context.parsed.y;
                                    if (value > 20) {
                                        label += ' ⚠️ (Critical)';
                                    } else if (value > 15) {
                                        label += ' ⚠️ (Borderline)';
                                    } else {
                                        label += ' ✓ (Normal)';
                                    }
                                }
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Update patient chart with new data point
function updatePatientChart(newAsymmetryValue) {
    if (!asymmetryChart) return;

    // Add current time as label
    const now = new Date();
    const timeLabel = now.getHours().toString().padStart(2, '0') + ':' +
        now.getMinutes().toString().padStart(2, '0');

    // Add new data point and remove oldest
    asymmetryChart.data.labels.push(timeLabel);
    if (asymmetryChart.data.labels.length > 10) {
        asymmetryChart.data.labels.shift();
    }

    asymmetryChart.data.datasets[0].data.push(newAsymmetryValue);
    if (asymmetryChart.data.datasets[0].data.length > 10) {
        asymmetryChart.data.datasets[0].data.shift();
    }

    // Update point colors based on new values
    const newColors = asymmetryChart.data.datasets[0].data.map(value =>
        value > 20 ? '#DC3545' : value > 15 ? '#FFC107' : '#28A745'
    );

    asymmetryChart.data.datasets[0].pointBackgroundColor = newColors;
    asymmetryChart.data.datasets[0].pointBorderColor = newColors;

    // Update threshold lines
    asymmetryChart.data.datasets[1].data = Array(asymmetryChart.data.labels.length).fill(20);
    asymmetryChart.data.datasets[2].data = Array(asymmetryChart.data.labels.length).fill(15);

    asymmetryChart.update();
}

// ===== DOCTOR DASHBOARD CHARTS =====

// Initialize Doctor Detail Chart for a specific patient
function initializeDetailChart(patientData) {
    const ctx = document.getElementById('detailChart');
    if (!ctx) return;

    // Clear existing chart if any
    if (detailChart) {
        detailChart.destroy();
    }

    // Default data if none provided
    const labels = patientData?.labels || ['9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM'];
    const data = patientData?.data || [18, 19, 22, 23, 21, 20, 19];

    // Determine point colors based on 20% rule
    const pointColors = data.map(value =>
        value > 20 ? '#DC3545' : value > 15 ? '#FFC107' : '#28A745'
    );

    detailChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Asymmetry %',
                data: data,
                borderColor: '#2E5AAC',
                backgroundColor: 'rgba(46, 90, 172, 0.1)',
                pointBackgroundColor: pointColors,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 10,
                borderWidth: 3,
                fill: true,
                tension: 0.3
            },
                {
                    label: 'Critical Threshold (20%)',
                    data: Array(labels.length).fill(20),
                    borderColor: '#DC3545',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Warning Threshold (15%)',
                    data: Array(labels.length).fill(15),
                    borderColor: '#FFC107',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    fill: false,
                    pointRadius: 0
                }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: Math.max(30, Math.max(...data) + 5),
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '%';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Create comparison chart for multiple patients
function createComparisonChart(patientList) {
    // This function creates a bar chart comparing patients' average asymmetry
    const patientNames = patientList.map(p => p.name);
    const avgAsymmetry = patientList.map(p => p.averageAsymmetry);

    // Determine bar colors based on 20% rule
    const barColors = avgAsymmetry.map(value =>
        value > 20 ? '#DC3545' : value > 15 ? '#FFC107' : '#28A745'
    );

    return {
        type: 'bar',
        data: {
            labels: patientNames,
            datasets: [{
                label: 'Average Asymmetry %',
                data: avgAsymmetry,
                backgroundColor: barColors,
                borderColor: barColors.map(color => color.replace('0.8', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 30,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            let status = '';
                            if (value > 20) {
                                status = ' (Critical)';
                            } else if (value > 15) {
                                status = ' (Borderline)';
                            } else {
                                status = ' (Normal)';
                            }
                            return `Asymmetry: ${value}%${status}`;
                        }
                    }
                }
            }
        }
    };
}

// Create daily pattern chart
function createDailyPatternChart(readingsByHour) {
    // This shows asymmetry pattern throughout the day
    const hours = ['6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM'];
    const avgAsymmetry = readingsByHour || [12, 14, 18, 22, 19, 15];

    // Determine point colors
    const pointColors = avgAsymmetry.map(value =>
        value > 20 ? '#DC3545' : value > 15 ? '#FFC107' : '#28A745'
    );

    return {
        type: 'line',
        data: {
            labels: hours,
            datasets: [{
                label: 'Average Asymmetry by Time',
                data: avgAsymmetry,
                borderColor: '#2E5AAC',
                backgroundColor: 'rgba(46, 90, 172, 0.1)',
                pointBackgroundColor: pointColors,
                pointBorderColor: pointColors,
                pointRadius: 6,
                borderWidth: 3,
                fill: true,
                tension: 0.3
            },
                {
                    label: 'Critical Threshold',
                    data: Array(hours.length).fill(20),
                    borderColor: '#DC3545',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 30,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    };
}

// ===== HELPER FUNCTIONS =====

// Generate random asymmetry data for demo purposes
function generateDemoAsymmetryData(days = 7, includeSpike = false) {
    const data = [];
    for (let i = 0; i < days; i++) {
        // Base asymmetry between 8-18%
        let value = Math.floor(Math.random() * 11) + 8;

        // Occasionally add a spike for demo
        if (includeSpike && i === Math.floor(days / 2) && Math.random() > 0.7) {
            value = Math.floor(Math.random() * 11) + 20; // 20-30%
        }

        data.push(value);
    }
    return data;
}

// Format date for chart labels
function getChartLabels(days = 7) {
    const labels = [];
    const today = new Date();

    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);

        if (i === 0) {
            labels.push('Today');
        } else {
            const month = date.toLocaleString('default', { month: 'short' });
            const day = date.getDate();
            labels.push(`${month} ${day}`);
        }
    }

    return labels;
}

// Get time labels for today
function getTodayTimeLabels() {
    const labels = [];
    const now = new Date();
    const currentHour = now.getHours();

    for (let i = 6; i <= currentHour; i += 3) {
        if (i < 12) {
            labels.push(`${i} AM`);
        } else if (i === 12) {
            labels.push('12 PM');
        } else {
            labels.push(`${i - 12} PM`);
        }
    }

    return labels;
}

// Export charts as image
function exportChartAsImage(chartId, filename = 'chart.png') {
    const chartCanvas = document.getElementById(chartId);
    if (!chartCanvas) return;

    const link = document.createElement('a');
    link.download = filename;
    link.href = chartCanvas.toDataURL('image/png');
    link.click();
}

// ===== GLOBAL EXPORTS =====
// Make functions available globally
window.initializePatientCharts = initializePatientCharts;
window.updatePatientChart = updatePatientChart;
window.initializeDetailChart = initializeDetailChart;
window.createComparisonChart = createComparisonChart;
window.createDailyPatternChart = createDailyPatternChart;
window.exportChartAsImage = exportChartAsImage;