document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const toggleButtons = document.querySelectorAll('.toggle-password');
    if (toggleButtons) {
        toggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const target = document.querySelector(targetId);
                
                if (target.type === 'password') {
                    target.type = 'text';
                    this.querySelector('i').classList.remove('fa-eye');
                    this.querySelector('i').classList.add('fa-eye-slash');
                } else {
                    target.type = 'password';
                    this.querySelector('i').classList.remove('fa-eye-slash');
                    this.querySelector('i').classList.add('fa-eye');
                }
            });
        });
    }
    
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tabs button');
    if (tabButtons) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                
                // Remove active class from all buttons and panels
                document.querySelectorAll('.tabs button').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.querySelectorAll('.tab-panel').forEach(panel => {
                    panel.classList.remove('active');
                });
                
                // Add active class to clicked button and its target panel
                this.classList.add('active');
                document.querySelector(targetId).classList.add('active');
            });
        });
    }
    
    // Form submission with confirmation
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    if (confirmForms) {
        confirmForms.forEach(form => {
            form.addEventListener('submit', function(event) {
                const message = this.getAttribute('data-confirm');
                if (!confirm(message)) {
                    event.preventDefault();
                }
            });
        });
    }
    
    // Add timestamp to logs URL to avoid caching
    const refreshLogButton = document.getElementById('refresh-logs');
    if (refreshLogButton) {
        refreshLogButton.addEventListener('click', function() {
            const timestamp = new Date().getTime();
            window.location.href = '/logs?t=' + timestamp;
        });
    }
    
    // Sidebar toggle functionality
    const sidebarToggleBtn = document.querySelector('.sidebar-toggle');
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            const mainContent = document.querySelector('.main-content');
            
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        });
    }
    
    // Mobile menu toggle
    const menuToggleBtn = document.querySelector('.menu-toggle');
    if (menuToggleBtn) {
        menuToggleBtn.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('expanded');
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const sidebar = document.querySelector('.sidebar');
        const menuToggle = document.querySelector('.menu-toggle');
        
        if (sidebar && sidebar.classList.contains('expanded')) {
            // Check if click is outside the sidebar and not on the menu toggle
            if (!sidebar.contains(event.target) && event.target !== menuToggle && !menuToggle.contains(event.target)) {
                sidebar.classList.remove('expanded');
            }
        }
    });
    
    // Handle window resize
    let windowWidth = window.innerWidth;
    
    window.addEventListener('resize', function() {
        const newWidth = window.innerWidth;
        const sidebar = document.querySelector('.sidebar');
        
        // If transitioning from mobile to desktop
        if (windowWidth <= 768 && newWidth > 768) {
            if (sidebar) {
                sidebar.classList.remove('expanded');
                if (sidebar.classList.contains('collapsed')) {
                    sidebar.style.width = 'var(--sidebar-collapsed-width)';
                } else {
                    sidebar.style.width = 'var(--sidebar-width)';
                }
            }
        }
        
        // If transitioning from desktop to mobile
        if (windowWidth > 768 && newWidth <= 768) {
            if (sidebar) {
                sidebar.style.width = '0';
                sidebar.classList.remove('collapsed');
            }
        }
        
        windowWidth = newWidth;
    });
    
    // Initialize sidebar state on load
    function initializeSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (sidebar && mainContent) {
            if (window.innerWidth <= 768) {
                sidebar.style.width = '0';
                mainContent.style.marginLeft = '0';
            } else {
                // Check for stored preference
                const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
                if (sidebarCollapsed) {
                    sidebar.classList.add('collapsed');
                    mainContent.classList.add('expanded');
                }
            }
        }
    }
    
    // Save sidebar state preference
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }
    
    // Initialize sidebar
    initializeSidebar();
    
    // Statistics charts initialization (if chart.js is included)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Form validation
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// Function to initialize charts
function initializeCharts() {
    // Traffic chart
    const trafficCtx = document.getElementById('traffic-chart');
    if (trafficCtx) {
        new Chart(trafficCtx, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: 'Incoming',
                    data: [10, 25, 55, 70, 45, 30],
                    borderColor: '#4a6ee0',
                    backgroundColor: 'rgba(74, 110, 224, 0.1)',
                    tension: 0.3,
                    fill: true
                }, {
                    label: 'Outgoing',
                    data: [5, 20, 35, 60, 40, 25],
                    borderColor: '#2ecc71',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Traffic (MB/s)'
                        }
                    }
                }
            }
        });
    }
    
    // Blocked connections chart
    const blockedCtx = document.getElementById('blocked-chart');
    if (blockedCtx) {
        new Chart(blockedCtx, {
            type: 'doughnut',
            data: {
                labels: ['Malware', 'Policy', 'Geoblocking', 'Rate limiting'],
                datasets: [{
                    data: [35, 25, 20, 20],
                    backgroundColor: [
                        '#e74c3c',
                        '#f1c40f',
                        '#3498db',
                        '#9b59b6'
                    ]
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
}

// Function to send an AJAX request
function ajaxRequest(url, method, data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            callback(null, JSON.parse(xhr.responseText));
        } else {
            callback(xhr.statusText, null);
        }
    };
    
    xhr.onerror = function() {
        callback('Network error', null);
    };
    
    xhr.send(JSON.stringify(data));
}

// Function to show a notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="close-notification">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Fade in
    setTimeout(() => {
        notification.classList.add('active');
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('active');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
    
    // Close button
    notification.querySelector('.close-notification').addEventListener('click', function() {
        notification.classList.remove('active');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
} 