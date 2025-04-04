document.addEventListener('DOMContentLoaded', function() {
    const diagnosisForm = document.getElementById('diagnosisForm');
    const symptomsImage = document.getElementById('symptomsImage');
    const imagePreview = document.getElementById('imagePreview');
    const diagnosisResult = document.getElementById('diagnosisResult');
    const recommendations = document.getElementById('recommendations');
    const veterinarianAlert = document.getElementById('veterinarianAlert');
    const reportsTable = document.getElementById('reportsTable');
    
    loadRecentReports();
    
    symptomsImage.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.innerHTML = `<img src="${e.target.result}" alt="Symptom Preview" class="img-fluid">`;
            };
            reader.readAsDataURL(file);
        }
    });
    
    diagnosisForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('farmerId', document.getElementById('farmerId').value);
        formData.append('location', document.getElementById('location').value);
        formData.append('cropType', document.getElementById('cropType').value);
        formData.append('symptomsDesc', document.getElementById('symptomsDesc').value);
        formData.append('image', symptomsImage.files[0]);
        
        const submitBtn = diagnosisForm.querySelector('button[type="submit"]');
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Analyzing...
            `;
            
            diagnosisResult.style.display = 'none';
            recommendations.style.display = 'none';
            veterinarianAlert.style.display = 'none';
            
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            displayResults(data);
            
            await loadRecentReports();
            
        } catch (error) {
            console.error('Error:', error);
            showAlert(`Error: ${error.message}`, 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit for Diagnosis';
        }
    });
    
    function displayResults(data) {
        diagnosisResult.style.display = 'block';
        diagnosisResult.innerHTML = `
            <strong>Diagnosis:</strong> ${data.diagnosis} (${data.confidence}% confidence)
            <br><small class="text-muted">${data.timestamp}</small>
        `;
        
        recommendations.style.display = 'block';
        recommendations.innerHTML = `<strong>Recommendations:</strong> ${data.recommendations}`;
        
        if (data.requires_expert) {
            veterinarianAlert.style.display = 'block';
        }
    }
    
    async function loadRecentReports() {
        try {
            const response = await fetch('/api/reports');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.reports && data.reports.length > 0) {
                reportsTable.innerHTML = data.reports.map(report => `
                    <tr>
                        <td>${report.date}</td>
                        <td>${report.type}</td>
                        <td>${report.diagnosis}</td>
                        <td>
                            <span class="badge ${report.status === 'Expert Notified' ? 'bg-danger' : 'bg-success'}">
                                ${report.status}
                            </span>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load reports:', error);
            showAlert('Failed to load recent reports', 'warning');
        }
    }
    
    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container');
        container.prepend(alertDiv);
        
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
});