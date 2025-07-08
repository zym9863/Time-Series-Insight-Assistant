[中文](README.md) | [English](README_EN.md)

# Time Series Insight Assistant (时间序列洞察助手)

🔍 **Intelligent Time Series Analysis Tool** - Provides automatic model identification, parameter estimation, and visualization diagnostics

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/time-series-insight-assistant)

## ✨ Features

- 🤖 **Automatic Model Identification**: Recommends the best ARIMA model based on ACF/PACF analysis
- 📊 **Smart Data Processing**: Automatic stationarity test, differencing, and data cleaning
- ⚙️ **Multiple Parameter Estimation Methods**: Supports method of moments and maximum likelihood estimation, with parameter comparison
- 🔬 **Comprehensive Model Evaluation**: Residual analysis, white noise test, and model fit evaluation
- 📈 **Rich Visualization**: ACF/PACF plots, residual diagnostics, forecast plots, and more
- 🖥️ **Dual Interface**: Command-line tool and Python library for different use cases
- 📋 **Detailed Reports**: Generates complete analysis reports and model recommendations

## 🚀 Quick Start

### Installation

Install with uv (recommended):

```bash
uv add time-series-insight-assistant
```

Or install with pip:

```bash
pip install time-series-insight-assistant
```

### Command Line Usage

```bash
# Analyze time series data in a CSV file
tsia analyze data.csv --date-col date --value-col value

# Quick data check
tsia quick-check data.csv

# Show help
tsia --help
```

### FastAPI Service Usage

```bash
# Start development server
python scripts/start_dev.py
# Or
./scripts/start.sh

# Start production server
python scripts/start_prod.py
# Or
./scripts/start.sh prod

# Access API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Python API Usage

```python
import pandas as pd
from time_series_insight import analyze_time_series

# One-click analysis
tsi = analyze_time_series('data.csv', date_column='date', value_column='value')

# View analysis summary
summary = tsi.get_summary()
print(f"Recommended model: {summary['best_model']['type']}")

# Generate forecast
forecast = tsi.predict(steps=10)
print(forecast['forecast'])

# Generate visualization charts
tsi.plot_analysis(save_dir='output/')
```

### FastAPI Service API Usage

```python
import requests

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Upload data file
with open('data.csv', 'rb') as f:
    files = {'file': f}
    data = {'date_column': 'date', 'value_column': 'value'}
    response = requests.post(f"{BASE_URL}/upload/file", files=files, data=data)
    upload_result = response.json()
    file_id = upload_result["file_id"]

# Run analysis
analysis_request = {
    "auto_diff": True,
    "max_p": 5,
    "max_q": 5,
    "n_models": 3
}
response = requests.post(f"{BASE_URL}/analysis/{file_id}", json=analysis_request)
analysis_result = response.json()
analysis_id = analysis_result["analysis_id"]

# Make prediction
prediction_request = {"steps": 10, "alpha": 0.05}
response = requests.post(f"{BASE_URL}/analysis/{analysis_id}/predict", json=prediction_request)
prediction_result = response.json()
print(f"Forecast values: {prediction_result['forecast_values']}")
```

## 📖 Core Features

### 1. Automatic Model Identification & Visualization Diagnostics

- **Stationarity Test**: ADF and KPSS tests
- **Automatic Differencing**: Determines differencing order based on test results
- **ACF/PACF Analysis**: Computes and visualizes autocorrelation and partial autocorrelation functions
- **Pattern Recognition**: Automatically identifies cutoff and tailing patterns
- **Model Recommendation**: Recommends the best ARIMA model based on statistical features

### 2. Fast Parameter Estimation & Model Evaluation

- **Method of Moments**: Quick initial parameter estimation
- **Maximum Likelihood Estimation**: More accurate parameter estimation
- **Parameter Comparison**: Compare results from different estimation methods
- **Model Evaluation**: AIC/BIC, R², residual analysis
- **White Noise Test**: Ljung-Box test for model adequacy

## 📊 Usage Examples

### Basic Analysis Flow

```python
from time_series_insight import TimeSeriesInsight
import pandas as pd

# Create analyzer
tsi = TimeSeriesInsight()

# Load data
data = pd.read_csv('your_data.csv')
tsi.load_data(data, date_column='date', value_column='value')

# Run full analysis
results = tsi.analyze()

# View recommended model
best_model = tsi.get_best_model()
print(f"Recommended model: ARIMA{best_model['order']}")
print(f"AIC: {best_model['evaluation']['fit_statistics']['aic']:.2f}")

# Generate forecast
forecast_result = tsi.predict(steps=12)
forecast = forecast_result['forecast']

# Visualize analysis
tsi.plot_analysis(save_dir='analysis_output/')
```

### Model Comparison

```python
# Analyze multiple candidate models
results = tsi.analyze(n_models=5)

# View all evaluated models
for model in results['model_evaluation']:
    order = model['order']
    aic = model['evaluation']['fit_statistics']['aic']
    r2 = model['evaluation']['fit_statistics']['r_squared']
    print(f"ARIMA{order}: AIC={aic:.2f}, R²={r2:.3f}")
```

### Export Results

```python
# Export full analysis results
tsi.export_results('analysis_results.json', format='json')
tsi.export_results('analysis_results.xlsx', format='excel')

# Get analysis summary
summary = tsi.get_summary()
```

## 🛠️ Tech Stack

- **Python 3.9+**: Modern Python features
- **pandas**: Data processing and time series operations
- **numpy**: Numerical computation
- **scipy**: Scientific computing and statistical tests
- **statsmodels**: Time series analysis and ARIMA modeling
- **matplotlib/seaborn**: Data visualization
- **typer**: Modern CLI interface
- **rich**: Beautiful terminal output

## 📁 Project Structure

```
time-series-insight-assistant/
├── time_series_insight/          # Main package
│   ├── core/                     # Core data processing
│   ├── analysis/                 # Statistical analysis
│   ├── estimation/               # Parameter estimation
│   ├── evaluation/               # Model evaluation
│   ├── visualization/            # Visualization
│   ├── cli/                      # CLI interface
│   └── api.py                    # High-level API
├── tests/                        # Test files
├── examples/                     # Usage examples
└── docs/                         # Documentation
```

## 🧪 Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run all tests
pytest

# Run a specific test
pytest tests/test_api.py

# Run tests with coverage report
pytest --cov=time_series_insight --cov-report=html
```

## 📚 Examples & Tutorials

### Generate Example Data

```bash
cd examples
python sample_data.py
```

### Run Basic Example

```bash
cd examples
python basic_usage.py
```

### CLI Examples

```bash
# Analyze ARIMA sample data
tsia analyze examples/data/arima_sample.csv

# Analyze seasonal data
tsia analyze examples/data/seasonal_sample.csv

# Analyze stock data
tsia analyze examples/data/stock_sample.csv --value-col price

# Save analysis results to a specific directory
tsia analyze data.csv --output results/ --save-plots
```

## 🔧 Development

### Environment Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/time-series-insight-assistant.git
cd time-series-insight-assistant

# Create virtual environment and install dependencies with uv
uv sync --dev

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### Code Quality

```bash
# Code formatting
black time_series_insight/
isort time_series_insight/

# Code checking
flake8 time_series_insight/
mypy time_series_insight/

# Run all quality checks
pre-commit run --all-files
```

## 📈 Performance

- **Fast Analysis**: Optimized algorithms for quick processing of medium-sized datasets (< 10,000 points)
- **Memory Efficient**: Stream processing for large datasets to avoid memory overflow
- **Parallel Computation**: Supports parallel evaluation of multiple models
- **Caching**: Smart caching of intermediate results to avoid redundant computation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines

- Follow existing code style
- Add appropriate tests
- Update relevant documentation
- Ensure all tests pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [statsmodels](https://www.statsmodels.org/) - Powerful statistical modeling
- [pandas](https://pandas.pydata.org/) - Excellent data processing library
- [matplotlib](https://matplotlib.org/) - Flexible visualization tool
- [typer](https://typer.tiangolo.com/) - Modern CLI framework

## 📞 Contact

- Project Home: [https://github.com/zym9863/time-series-insight-assistant](https://github.com/zym9863/time-series-insight-assistant)
- Issue Tracker: [Issues](https://github.com/zym9863/time-series-insight-assistant/issues)

## 🔮 Roadmap

- [ ] Support for more time series models (SARIMA, VAR, etc.)
- [ ] Add machine learning methods (LSTM, Prophet, etc.)
- [ ] Web interface support
- [ ] Real-time data stream processing
- [ ] Multivariate time series analysis
- [ ] Anomaly detection

---

**If you find this project helpful, please give it a ⭐ Star!**
