// ==================== Weather Dashboard Application ==================== //

class WeatherDashboard {
    constructor(config) {
        this.config = config;
        this.api = new WeatherAPI(config);
        this.currentWeatherData = null;
        this.currentForecastData = null;
        this.autoRefreshInterval = null;

        // DOM Elements
        this.elements = {
            searchInput: document.getElementById('searchInput'),
            searchBtn: document.getElementById('searchBtn'),
            errorMessage: document.getElementById('errorMessage'),
            loadingSpinner: document.getElementById('loadingSpinner'),
            currentWeather: document.getElementById('currentWeather'),
            forecastSection: document.getElementById('forecastSection'),
            forecastContainer: document.getElementById('forecastContainer'),
            lastUpdate: document.getElementById('lastUpdate'),
            quickBtns: document.querySelectorAll('.quick-btn')
        };

        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        // Check API configuration
        if (!this.api.isConfigured()) {
            this.showError('⚠️ API Key not configured! Please open js/config.js and add your OpenWeatherMap API key.');
            return;
        }

        // Event listeners
        this.elements.searchBtn.addEventListener('click', () => this.handleSearch());
        this.elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });

        // Quick city buttons
        this.elements.quickBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const city = e.target.dataset.city;
                this.fetchWeatherData(city);
            });
        });

        // Load default city
        this.fetchWeatherData(this.config.DEFAULT_CITY);

        // Setup auto-refresh if configured
        if (this.config.AUTO_REFRESH_INTERVAL > 0) {
            this.setupAutoRefresh();
        }
    }

    /**
     * Handle search button click
     */
    handleSearch() {
        const city = this.elements.searchInput.value.trim();
        if (city) {
            this.fetchWeatherData(city);
            this.elements.searchInput.value = '';
        }
    }

    /**
     * Fetch weather data for a city
     */
    async fetchWeatherData(cityName) {
        try {
            this.showLoading(true);
            this.hideError();

            const data = await this.api.getWeatherByCity(cityName);
            
            this.currentWeatherData = data.current;
            this.currentForecastData = data.forecast;

            this.displayCurrentWeather(data.current);
            this.displayForecast(data.forecast);
            this.updateLastUpdate();

            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            this.showError(error.message);
        }
    }

    /**
     * Display current weather
     */
    displayCurrentWeather(data) {
        const currentWeatherSection = this.elements.currentWeather;

        // City name and date
        document.getElementById('cityName').textContent = 
            `${data.city}, ${data.country}`;
        document.getElementById('currentDate').textContent = 
            new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

        // Temperature and icon
        document.getElementById('temperature').textContent = `${data.temperature}°`;
        document.getElementById('weatherIcon').src = this.api.getIconUrl(data.icon);
        document.getElementById('weatherDescription').textContent = data.weatherDetail;

        // Weather details
        document.getElementById('humidity').textContent = `${data.humidity}%`;
        document.getElementById('windSpeed').textContent = `${data.windSpeed.toFixed(1)} m/s`;
        document.getElementById('pressure').textContent = `${data.pressure} hPa`;
        document.getElementById('visibility').textContent = `${data.visibility} km`;

        // Additional info
        document.getElementById('feelsLike').textContent = `${data.feelsLike}°`;
        document.getElementById('maxTemp').textContent = `${data.maxTemp}°`;
        document.getElementById('minTemp').textContent = `${data.minTemp}°`;
        document.getElementById('sunrise').textContent = 
            this.api.formatTime(data.sunrise, data.timezone, this.config.UI.TIME_FORMAT);
        document.getElementById('sunset').textContent = 
            this.api.formatTime(data.sunset, data.timezone, this.config.UI.TIME_FORMAT);

        // Show weather card
        currentWeatherSection.style.display = 'block';

        // Check for weather alerts
        this.checkWeatherAlerts(data);
    }

    /**
     * Display 5-day forecast
     */
    displayForecast(forecastData) {
        const forecastSection = this.elements.forecastSection;
        const forecastContainer = this.elements.forecastContainer;

        if (!this.config.UI.SHOW_FORECAST) {
            forecastSection.style.display = 'none';
            return;
        }

        // Clear previous forecast
        forecastContainer.innerHTML = '';

        // Create forecast cards
        forecastData.forEach((day, index) => {
            const card = document.createElement('div');
            card.className = 'forecast-card';
            card.style.animationDelay = `${0.1 * index}s`;

            card.innerHTML = `
                <div class="forecast-date">${day.day}</div>
                <img src="${this.api.getIconUrl(day.icon)}" alt="Weather icon" class="forecast-icon">
                <div class="forecast-temp">
                    <span class="forecast-high">${day.tempMax}°</span>
                    <span class="forecast-low">${day.tempMin}°</span>
                </div>
                <div class="forecast-desc">${day.weatherDetail}</div>
                <div style="font-size: 0.85rem; color: #718096; margin-top: 8px;">
                    <div>💧 ${day.humidity}%</div>
                    <div>💨 ${day.windSpeed.toFixed(1)} m/s</div>
                </div>
            `;

            forecastContainer.appendChild(card);
        });

        forecastSection.style.display = 'block';
    }

    /**
     * Check for weather alerts
     */
    checkWeatherAlerts(data) {
        const alerts = [];

        if (data.temperature > this.config.ALERTS.EXTREME_HEAT) {
            alerts.push(`🔥 Extreme heat warning: ${data.temperature}°C`);
        }

        if (data.temperature < this.config.ALERTS.EXTREME_COLD) {
            alerts.push(`❄️ Extreme cold warning: ${data.temperature}°C`);
        }

        if (data.windSpeed > this.config.ALERTS.HIGH_WIND) {
            alerts.push(`💨 High wind warning: ${data.windSpeed.toFixed(1)} m/s`);
        }

        if (alerts.length > 0) {
            alerts.forEach(alert => {
                console.warn('Weather Alert:', alert);
                // You could display these in a separate alert section
            });
        }
    }

    /**
     * Show loading spinner
     */
    showLoading(show) {
        this.elements.loadingSpinner.style.display = show ? 'flex' : 'none';
    }

    /**
     * Show error message
     */
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorMessage.style.display = 'flex';
    }

    /**
     * Hide error message
     */
    hideError() {
        this.elements.errorMessage.style.display = 'none';
    }

    /**
     * Update last update time
     */
    updateLastUpdate() {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        document.getElementById('lastUpdate').textContent = time;
    }

    /**
     * Setup auto-refresh interval
     */
    setupAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            if (this.currentWeatherData) {
                const city = this.currentWeatherData.city;
                console.log(`Auto-refreshing weather for ${city}...`);
                this.fetchWeatherData(city);
            }
        }, this.config.AUTO_REFRESH_INTERVAL);
    }

    /**
     * Clear auto-refresh interval
     */
    clearAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
}

// ==================== Initialize Application ==================== //
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new WeatherDashboard(CONFIG);
});
