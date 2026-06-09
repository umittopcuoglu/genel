// AI Control Panel - Frontend Logic

let currentAPI = null;

// Show configuration modal
function showConfigModal(apiName) {
    currentAPI = apiName;
    document.getElementById('configModal').style.display = 'block';
    document.getElementById('apiKey').value = '';
    document.getElementById('apiKey').focus();
}

// Close configuration modal
function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
    currentAPI = null;
}

// Save API configuration
async function saveConfig(event) {
    event.preventDefault();

    const apiKey = document.getElementById('apiKey').value.trim();

    if (!apiKey) {
        alert('Please enter an API key');
        return;
    }

    try {
        const response = await fetch(`/api/config/${currentAPI}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            document.getElementById(`status-${currentAPI}`).textContent = 'configured';
            document.getElementById(`status-${currentAPI}`).classList.add('configured');
            closeConfigModal();
        } else {
            alert(`❌ Error: ${data.error || 'Failed to configure API'}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error configuring API');
    }
}

// Test API connection
async function testAPI(apiName) {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Testing...';

    try {
        const response = await fetch(`/api/config/${apiName}`);
        const data = await response.json();

        if (data.api_key) {
            alert(`✅ ${apiName} is configured and ready to use!`);
        } else {
            alert(`⚠️ ${apiName} needs to be configured first.`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error testing API');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Test';
    }
}

// Open application directory
function openApp(path) {
    // This will require backend support to open file explorer
    alert(`Opening: ${path}\n\nYou can manually open this directory in your file explorer.`);
}

// Sync single application
async function syncApp(appName) {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Syncing...';

    try {
        const response = await fetch('/api/apps/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ app: appName })
        });

        const data = await response.json();

        if (response.ok) {
            const result = data.results[0];
            alert(`✅ ${appName} synced!\n${result.message}`);
        } else {
            alert(`❌ Error syncing ${appName}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error syncing application');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sync';
    }
}

// Sync all applications
async function syncAllApps() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Syncing all...';

    try {
        const response = await fetch('/api/apps/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            let message = '✅ All applications synced!\n\n';
            data.results.forEach(result => {
                const status = result.status === 'success' ? '✓' : '✗';
                message += `${status} ${result.app}: ${result.status}\n`;
            });
            alert(message);
        } else {
            alert('❌ Error syncing applications');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error syncing applications');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sync All Applications';
    }
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('configModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', function () {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// Load dashboard data
async function loadDashboardData() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        // Update status badges
        Object.entries(data.apis).forEach(([key, api]) => {
            const badge = document.getElementById(`status-${key}`);
            if (badge) {
                badge.textContent = api.status;
                badge.className = `badge ${api.status}`;
            }
        });
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}
