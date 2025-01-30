document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    
    function updateScoreboard() {
        fetch('/scoreboard')
            .then(response => response.json())
            .then(data => {
                // Update tick counter with animation
                const tickElement = document.getElementById('current-tick');
                const currentTick = parseInt(tickElement.textContent);
                const newTick = data.current_tick;
                
                if (currentTick !== newTick) {
                    tickElement.style.animation = 'none';
                    tickElement.offsetHeight; // Trigger reflow
                    tickElement.style.animation = 'fadeIn 0.5s ease-out';
                    tickElement.textContent = newTick;
                }

                const tbody = document.getElementById('scoreboard-body');
                tbody.innerHTML = '';

                data.teams.forEach((team, index) => {
                    const tr = document.createElement('tr');
                    tr.style.animation = `fadeIn 0.5s ease-out ${index * 0.1}s`;

                    // Rank column with icon
                    const rankIcon = getRankIcon(index);
                    tr.innerHTML = `
                        <td>
                            <div style="display: flex; align-items: center;">
                                ${rankIcon}
                                <span>#${index + 1}</span>
                            </div>
                        </td>
                        <td>
                            <div style="font-weight: 600;">${team.team_name}</div>
                        </td>
                        <td>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                ${Object.entries(team.services).map(([service, data]) => `
                                    <span class="service-status ${data.status.toLowerCase()}">
                                        ${getServiceIcon(data.status)}
                                        ${service}
                                    </span>
                                `).join('')}
                            </div>
                        </td>
                        <td>
                            <div class="score" style="${getScoreStyle(index)}">
                                ${team.score}
                            </div>
                        </td>
                    `;

                    tbody.appendChild(tr);
                });

                document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                document.getElementById('error-message').classList.add('hidden');
                lucide.createIcons();
            })
            .catch(error => {
                console.error('Error fetching scoreboard:', error);
                document.getElementById('error-message').classList.remove('hidden');
                document.getElementById('error-message').querySelector('span').textContent = 
                    'Could not connect to server';
            });
    }

    function getRankIcon(index) {
        switch (index) {
            case 0:
                return '<i data-lucide="trophy" style="color: #fbbf24;"></i>';
            case 1:
                return '<i data-lucide="award" style="color: #9ca3af;"></i>';
            case 2:
                return '<i data-lucide="award" style="color: #b45309;"></i>';
            default:
                return '<i data-lucide="target" style="color: #60a5fa;"></i>';
        }
    }

    function getServiceIcon(status) {
        switch (status.toLowerCase()) {
            case 'up':
                return '<i data-lucide="check-circle" style="color: #22c55e;"></i>';
            case 'down':
                return '<i data-lucide="x-circle" style="color: #ef4444;"></i>';
            default:
                return '<i data-lucide="alert-triangle" style="color: #9ca3af;"></i>';
        }
    }

    function getScoreStyle(index) {
        if (index === 0) return 'color: #fbbf24; animation: glow 2s ease-in-out infinite;';
        return '';
    }

    // Initial update
    updateScoreboard();

    // Update every 30 seconds
    setInterval(updateScoreboard, 30000);
}); 