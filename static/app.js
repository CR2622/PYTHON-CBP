let currentCurrency = 'USD';
let exchangeRates = { USD: 1 };
let dashboardData = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initCurrencyRates();
    setupCurrencySelector();
    fetchData();
    setupForm();
    setupChat();
});

let ratesFetchedAt = null;

async function initCurrencyRates() {
    try {
        const response = await fetch('https://open.er-api.com/v6/latest/USD');
        if (response.ok) {
            const data = await response.json();
            exchangeRates = data.rates;
            ratesFetchedAt = new Date();
        }
    } catch (e) {
        console.warn('Failed to fetch live exchange rates, falling back to defaults.');
        exchangeRates = { USD: 1, EUR: 0.92, GBP: 0.79, INR: 83.5, JPY: 153.2, CAD: 1.37, AUD: 1.52 };
        ratesFetchedAt = null;
    }
    renderExchangeRates();
}

function setupCurrencySelector() {
    const selector = document.getElementById('currency-select');
    if (selector) {
        selector.addEventListener('change', (e) => {
            currentCurrency = e.target.value;
            if (dashboardData) {
                renderDashboard(dashboardData);
            }
            // Highlight the newly selected currency card
            document.querySelectorAll('.rate-card').forEach(card => {
                card.classList.toggle('active-currency', card.dataset.code === currentCurrency);
            });
        });
    }
}

const CURRENCY_META = {
    USD: { flag: '🇺🇸', name: 'US Dollar' },
    EUR: { flag: '🇪🇺', name: 'Euro' },
    GBP: { flag: '🇬🇧', name: 'British Pound' },
    INR: { flag: '🇮🇳', name: 'Indian Rupee' },
    JPY: { flag: '🇯🇵', name: 'Japanese Yen' },
    CAD: { flag: '🇨🇦', name: 'Canadian Dollar' },
    AUD: { flag: '🇦🇺', name: 'Australian Dollar' },
};

function renderExchangeRates() {
    const grid = document.getElementById('rates-grid');
    const timestamp = document.getElementById('rates-timestamp');
    if (!grid) return;

    // Update timestamp
    if (ratesFetchedAt) {
        timestamp.textContent = `Updated: ${ratesFetchedAt.toLocaleTimeString()}`;
    } else {
        timestamp.textContent = 'Using fallback rates';
    }

    grid.innerHTML = '';
    const currencies = Object.keys(CURRENCY_META);

    currencies.forEach(code => {
        const rate = exchangeRates[code] || 1;
        const meta = CURRENCY_META[code];
        const isActive = code === currentCurrency;

        const card = document.createElement('div');
        card.className = `rate-card${isActive ? ' active-currency' : ''}`;
        card.dataset.code = code;

        card.innerHTML = `
            <div class="rate-card-flag">${meta.flag}</div>
            <div class="rate-card-code">${code}</div>
            <div class="rate-card-name">${meta.name}</div>
            <div class="rate-card-value">${rate.toFixed(4)}</div>
            <div class="rate-card-base">per 1 USD</div>
        `;

        grid.appendChild(card);
    });
}

async function fetchData() {
    try {
        const response = await fetch('/api/analyze');
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        dashboardData = data;
        renderDashboard(data);
    } catch (error) {
        showError(error.message);
    }
}

function renderDashboard(data) {
    // Hide loader, show dashboard
    document.getElementById('loader').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    
    // Update summary cards
    document.getElementById('monthly-total').textContent = formatCurrency(data.overall_total);
    document.getElementById('annual-forecast').textContent = formatCurrency(data.annual_forecast);
    
    // Update volatility warnings
    const warningsContainer = document.getElementById('warnings-container');
    const warningsSection = document.getElementById('volatility-warnings');
    
    warningsContainer.innerHTML = '';
    warningsSection.classList.add('hidden');
    
    if (data.high_volatility && data.high_volatility.length > 0) {
        warningsSection.classList.remove('hidden');
        data.high_volatility.forEach(category => {
            const stats = data.stats[category];
            const card = document.createElement('div');
            card.className = 'warning-card';
            
            const pct = Math.round((stats.std / stats.mean) * 100) || 0;
            
            card.innerHTML = `
                <h4>${category}</h4>
                <p>Std Dev is ${pct}% of Mean (${formatCurrency(stats.std)} vs ${formatCurrency(stats.mean)}).</p>
                <p>Spending in this category is unpredictable.</p>
            `;
            warningsContainer.appendChild(card);
        });
    }
    
    // Populate data table
    const tableBody = document.getElementById('expense-table-body');
    tableBody.innerHTML = '';
    
    // Sort categories alphabetically
    const categories = Object.keys(data.stats).sort();
    
    categories.forEach(category => {
        const stats = data.stats[category];
        const tr = document.createElement('tr');
        
        const statusBadge = stats.volatile 
            ? '<span class="badge badge-warning">High Volatility</span>'
            : '<span class="badge badge-normal">Stable</span>';
            
        tr.innerHTML = `
            <td>${category}</td>
            <td class="amount-cell">${formatCurrency(stats.total)}</td>
            <td class="amount-cell">${formatCurrency(stats.mean)}</td>
            <td class="amount-cell">${formatCurrency(stats.std)}</td>
            <td>${statusBadge}</td>
        `;
        
        tableBody.appendChild(tr);
    });
}

function setupForm() {
    const form = document.getElementById('add-transaction-form');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const date = document.getElementById('txn-date').value;
        const category = document.getElementById('txn-category').value;
        const amount = document.getElementById('txn-amount').value;
        const submitBtn = document.getElementById('submit-btn');
        const msgDiv = document.getElementById('form-message');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Adding...';
        msgDiv.className = 'form-message hidden';
        
        try {
            const response = await fetch('/api/transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ date, category, amount })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Server returned ${response.status}`);
            }
            
            // Success
            form.reset();
            msgDiv.textContent = 'Transaction added successfully!';
            msgDiv.className = 'form-message success';
            
            // Refresh dashboard data
            fetchData();
            
            setTimeout(() => {
                msgDiv.className = 'form-message hidden';
            }, 3000);
            
        } catch (error) {
            msgDiv.textContent = error.message;
            msgDiv.className = 'form-message error';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Add Expense';
        }
    });
}

function formatCurrency(amount) {
    const rate = exchangeRates[currentCurrency] || 1;
    const convertedAmount = amount * rate;
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currentCurrency,
        currencyDisplay: 'narrowSymbol'
    }).format(convertedAmount);
}

function showError(message) {
    document.getElementById('loader').classList.add('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    
    const errorSection = document.getElementById('error-message');
    errorSection.classList.remove('hidden');
    document.getElementById('error-text').textContent = message;
}

// Chatbot Logic
function setupChat() {
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (!chatToggleBtn) return;

    chatToggleBtn.addEventListener('click', () => {
        chatWindow.classList.toggle('hidden');
        if (!chatWindow.classList.contains('hidden')) {
            chatInput.focus();
        }
    });

    closeChatBtn.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to UI
        addChatMessage(message, 'user-message');
        chatInput.value = '';
        
        // Show typing indicator
        const typingId = showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            removeTypingIndicator(typingId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                addChatMessage(errorData.error || `Server error: ${response.status}`, 'bot-message');
                return;
            }
            
            const data = await response.json();
            
            if (data.error) {
                addChatMessage(`Error: ${data.error}`, 'bot-message');
            } else {
                // Use marked.js if available
                let htmlContent = data.reply;
                if (typeof marked !== 'undefined') {
                    htmlContent = marked.parse(data.reply);
                }
                addChatMessage(htmlContent, 'bot-message', true);
            }
            
        } catch (error) {
            removeTypingIndicator(typingId);
            addChatMessage(`Connection error: ${error.message}`, 'bot-message');
        }
    });

    function addChatMessage(text, className, isHtml = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${className}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHtml) {
            contentDiv.innerHTML = text;
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            contentDiv.appendChild(p);
        }
        
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot-message';
        msgDiv.id = id;
        
        msgDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) {
            el.remove();
        }
    }
}
