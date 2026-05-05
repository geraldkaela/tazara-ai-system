"""Exploratory seasonal and trend analysis for cargo demand.

Generates a short textual summary and saves optional plots to
`forecasting/outputs/`.

Usage:
    python forecasting/historical_analysis.py
"""
from __future__ import annotations

import logging
from pathlib import Path
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


PROC_PATH = Path("data/simulated/cargo_demand.csv")
OUTPUT_DIR = Path("forecasting/outputs")


def ensure_sample_data(path: Path) -> None:
    # Treat missing files OR files with only headers as empty and create sample data
    try:
        if path.exists():
            # try reading a single row to check for data presence
            import pandas as _pd

            small = _pd.read_csv(path, nrows=1)
            if not small.empty:
                return
    except Exception:
        # any read error treat as missing and continue to create sample
        pass
    logger.info("No processed demand data found or file is empty — creating sample data")
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=180, freq="D")
    # create synthetic seasonality: weekly + monthly + noise
    weekly = 50 * np.sin(2 * np.pi * rng.dayofweek / 7)
    monthly = 30 * np.sin(2 * np.pi * rng.day / 30.5)
    trend = np.linspace(100, 150, len(rng))
    noise = np.random.normal(scale=10, size=len(rng))
    cargo = np.maximum(0, trend + weekly + monthly + noise)
    df = pd.DataFrame({"date": rng, "cargo_tons": cargo.round(2)})
    df.to_csv(path, index=False)
    logger.info(f"Wrote sample processed data to {path}")


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"]) if path.exists() else pd.DataFrame()
    if df.empty:
        raise FileNotFoundError(f"Processed demand file not found or empty: {path}")
    df = df.set_index("date").asfreq("D").fillna(0)
    return df


def seasonality_metrics(series: pd.Series) -> dict:
    res = {}
    res["start"] = str(series.index.min().date())
    res["end"] = str(series.index.max().date())
    res["n"] = int(len(series))
    res["mean"] = float(series.mean())
    res["std"] = float(series.std())
    # autocorrelation at weekly and monthly lags
    res["acf_7"] = float(series.autocorr(lag=7))
    res["acf_30"] = float(series.autocorr(lag=30))

    # FFT-based dominant period detection (days)
    y = series.values - np.mean(series.values)
    fft = np.fft.rfft(y)
    freq = np.fft.rfftfreq(len(y), d=1.0)
    power = np.abs(fft)
    # ignore zero frequency
    power[0] = 0
    peak = np.argmax(power)
    if freq[peak] > 0:
        dominant_period = 1.0 / freq[peak]
        res["dominant_period_days"] = float(np.round(dominant_period, 2))
    else:
        res["dominant_period_days"] = None

    return res


def save_plots(series: pd.Series, out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt

        out_dir.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(10, 4))
        series.plot(title="Daily cargo demand")
        plt.ylabel("cargo_tons")
        plt.tight_layout()
        p1 = out_dir / "demand_timeseries.png"
        plt.savefig(p1)
        plt.close()

        plt.figure(figsize=(10, 4))
        series.rolling(7).mean().plot(title="7-day rolling mean")
        plt.ylabel("cargo_tons")
        plt.tight_layout()
        p2 = out_dir / "demand_rolling7.png"
        plt.savefig(p2)
        plt.close()
        logger.info(f"Saved plots to {out_dir}")
    except Exception as e:
        logger.warning(f"Skipping plots: {e}")


def run(out: Path = PROC_PATH) -> dict:
    ensure_sample_data(out)
    df = load_data(out)
    series = df["cargo_tons"].astype(float)
    metrics = seasonality_metrics(series)
    logger.info("Seasonality summary:")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v}")
    save_plots(series, OUTPUT_DIR)
    return metrics


if __name__ == "__main__":
    run()
"""
Phase 2 Week 4: Historical Data Analysis for Demand Forecasting
Seasonal pattern detection, route-specific demand modeling
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalDemandAnalyzer:
    """Analyze historical cargo demand data for forecasting"""
    
    def __init__(self, data_path: str = "data/simulated/cargo_demand.csv"):
        """Initialize analyzer with historical data"""
        self.data_path = data_path
        self.df = None
        self.routes = None
        self.analysis_results = {}
        self._load_data()
    
    def _load_data(self):
        """Load and prepare historical data"""
        try:
            self.df = pd.read_csv(self.data_path)
            
            # Ensure date column is datetime
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df = self.df.sort_values('date')
            
            # Identify routes (stations or route identifiers)
            if 'station' in self.df.columns:
                self.routes = self.df['station'].unique()
            elif 'route' in self.df.columns:
                self.routes = self.df['route'].unique()
            else:
                self.routes = ['combined']
            
            logger.info(f"Loaded {len(self.df)} records with {len(self.routes)} routes")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def detect_seasonal_patterns(self) -> Dict:
        """Detect seasonal patterns in demand data"""
        logger.info("🔍 Detecting seasonal patterns...")
        
        patterns = {}
        
        try:
            # Prepare time series data
            if 'date' in self.df.columns and 'cargo_tons' in self.df.columns:
                ts_data = self.df.set_index('date')['cargo_tons']
                
                # Ensure we have enough data for decomposition (need at least 2 periods)
                if len(ts_data) >= 24:  # At least 24 periods for monthly seasonality
                    # Seasonal decomposition
                    decomposition = seasonal_decompose(
                        ts_data, 
                        model='additive', 
                        period=12  # Monthly seasonality
                    )
                    
                    patterns['trend'] = decomposition.trend.mean()
                    patterns['seasonal'] = decomposition.seasonal.std()
                    patterns['residual_std'] = decomposition.resid.std()
                    patterns['trend_component'] = decomposition.trend.tolist()
                    patterns['seasonal_component'] = decomposition.seasonal.tolist()
                    
                    # Calculate seasonal indices
                    seasonal_indices = decomposition.seasonal.groupby(
                        decomposition.seasonal.index.month
                    ).mean()
                    patterns['monthly_seasonal_indices'] = seasonal_indices.to_dict()
                    
                    logger.info("✅ Seasonal decomposition completed")
                else:
                    logger.warning("Insufficient data for seasonal decomposition")
                    patterns = {"status": "insufficient_data"}
        
        except Exception as e:
            logger.error(f"Error in seasonal pattern detection: {e}")
            patterns = {"error": str(e)}
        
        self.analysis_results['seasonal_patterns'] = patterns
        return patterns
    
    def analyze_route_demand(self) -> Dict:
        """Analyze demand patterns by route"""
        logger.info("🛣️ Analyzing route-specific demand...")
        
        route_analysis = {}
        
        try:
            # Group by route if available
            if 'station' in self.df.columns:
                grouped = self.df.groupby('station')['cargo_tons'].agg([
                    'mean', 'std', 'min', 'max', 'count'
                ])
                
                for route in self.routes:
                    route_data = self.df[self.df['station'] == route]['cargo_tons']
                    
                    route_analysis[route] = {
                        'mean_demand': float(route_data.mean()),
                        'std_dev': float(route_data.std()),
                        'min_demand': float(route_data.min()),
                        'max_demand': float(route_data.max()),
                        'cv': float(route_data.std() / route_data.mean()) if route_data.mean() > 0 else 0,  # Coefficient of variation
                        'total_shipments': int(len(route_data)),
                        'trend': self._calculate_trend(route_data)
                    }
                
                logger.info(f"✅ Analyzed demand for {len(route_analysis)} routes")
            else:
                # Overall demand analysis
                route_analysis['overall'] = {
                    'mean_demand': float(self.df['cargo_tons'].mean()),
                    'std_dev': float(self.df['cargo_tons'].std()),
                    'min_demand': float(self.df['cargo_tons'].min()),
                    'max_demand': float(self.df['cargo_tons'].max()),
                    'cv': float(self.df['cargo_tons'].std() / self.df['cargo_tons'].mean()),
                    'total_shipments': len(self.df),
                    'trend': self._calculate_trend(self.df['cargo_tons'])
                }
        
        except Exception as e:
            logger.error(f"Error in route demand analysis: {e}")
            route_analysis = {"error": str(e)}
        
        self.analysis_results['route_demand'] = route_analysis
        return route_analysis
    
    def _calculate_trend(self, series: pd.Series) -> str:
        """Calculate trend direction (increasing/decreasing/stable)"""
        if len(series) < 2:
            return "insufficient_data"
        
        first_half = series.iloc[:len(series)//2].mean()
        second_half = series.iloc[len(series)//2:].mean()
        
        change_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if abs(change_pct) < 5:
            return "stable"
        elif change_pct > 0:
            return f"increasing ({change_pct:.1f}%)"
        else:
            return f"decreasing ({abs(change_pct):.1f}%)"
    
    def analyze_temporal_patterns(self) -> Dict:
        """Analyze demand patterns by time period"""
        logger.info("⏰ Analyzing temporal patterns...")
        
        temporal_patterns = {}
        
        try:
            if 'date' in self.df.columns:
                # Day of week analysis
                self.df['day_of_week'] = self.df['date'].dt.day_name()
                dow_analysis = self.df.groupby('day_of_week')['cargo_tons'].agg(['mean', 'std', 'count'])
                temporal_patterns['day_of_week'] = dow_analysis.to_dict()
                
                # Month analysis
                self.df['month'] = self.df['date'].dt.month
                month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                              7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
                monthly = self.df.groupby('month')['cargo_tons'].agg(['mean', 'std', 'count'])
                temporal_patterns['monthly'] = {month_names[m]: v.to_dict() for m, v in monthly.iterrows()}
                
                # Quarter analysis
                self.df['quarter'] = self.df['date'].dt.quarter
                quarterly = self.df.groupby('quarter')['cargo_tons'].agg(['mean', 'std', 'count'])
                temporal_patterns['quarterly'] = quarterly.to_dict()
                
                logger.info("✅ Temporal pattern analysis completed")
            
        except Exception as e:
            logger.error(f"Error in temporal pattern analysis: {e}")
            temporal_patterns = {"error": str(e)}
        
        self.analysis_results['temporal_patterns'] = temporal_patterns
        return temporal_patterns
    
    def calculate_demand_statistics(self) -> Dict:
        """Calculate comprehensive demand statistics"""
        logger.info("📊 Calculating demand statistics...")
        
        stats = {
            'mean': float(self.df['cargo_tons'].mean()),
            'median': float(self.df['cargo_tons'].median()),
            'std_dev': float(self.df['cargo_tons'].std()),
            'min': float(self.df['cargo_tons'].min()),
            'max': float(self.df['cargo_tons'].max()),
            'q1': float(self.df['cargo_tons'].quantile(0.25)),
            'q3': float(self.df['cargo_tons'].quantile(0.75)),
            'iqr': float(self.df['cargo_tons'].quantile(0.75) - self.df['cargo_tons'].quantile(0.25)),
            'skewness': float(self.df['cargo_tons'].skew()),
            'kurtosis': float(self.df['cargo_tons'].kurtosis()),
            'cv': float(self.df['cargo_tons'].std() / self.df['cargo_tons'].mean()),
            'total_records': int(len(self.df))
        }
        
        self.analysis_results['statistics'] = stats
        logger.info("✅ Demand statistics calculated")
        
        return stats
    
    def identify_demand_peaks(self, percentile: float = 0.9) -> Dict:
        """Identify peak demand periods"""
        logger.info(f"🔺 Identifying demand peaks (>{percentile*100}th percentile)...")
        
        threshold = self.df['cargo_tons'].quantile(percentile)
        peaks = self.df[self.df['cargo_tons'] >= threshold]
        
        peak_info = {
            'threshold': float(threshold),
            'num_peaks': len(peaks),
            'percent_of_total': float(len(peaks) / len(self.df) * 100),
            'peak_dates': peaks['date'].dt.strftime('%Y-%m-%d').tolist() if 'date' in peaks.columns else [],
            'avg_peak_demand': float(peaks['cargo_tons'].mean()),
            'max_peak_demand': float(peaks['cargo_tons'].max())
        }
        
        self.analysis_results['demand_peaks'] = peak_info
        logger.info(f"✅ Identified {peak_info['num_peaks']} peak demand periods")
        
        return peak_info
    
    def get_comprehensive_analysis(self) -> Dict:
        """Get comprehensive demand analysis report"""
        logger.info("\n📈 Generating comprehensive demand analysis report...")
        
        report = {
            'data_summary': {
                'total_records': int(len(self.df)),
                'date_range': {
                    'start': str(self.df['date'].min()) if 'date' in self.df.columns else 'N/A',
                    'end': str(self.df['date'].max()) if 'date' in self.df.columns else 'N/A'
                },
                'routes_analyzed': len(self.routes)
            },
            'statistical_summary': self.calculate_demand_statistics(),
            'seasonal_patterns': self.detect_seasonal_patterns(),
            'route_demand': self.analyze_route_demand(),
            'temporal_patterns': self.analyze_temporal_patterns(),
            'demand_peaks': self.identify_demand_peaks()
        }
        
        logger.info("✅ Comprehensive analysis completed")
        return report


# Test the analyzer
if __name__ == "__main__":
    analyzer = HistoricalDemandAnalyzer()
    report = analyzer.get_comprehensive_analysis()
    
    print("\n" + "="*60)
    print("🚆 HISTORICAL DEMAND ANALYSIS REPORT")
    print("="*60)
    
    print("\n📊 Data Summary:")
    print(f"  Total Records: {report['data_summary']['total_records']}")
    print(f"  Routes Analyzed: {report['data_summary']['routes_analyzed']}")
    if report['data_summary']['date_range']['start'] != 'N/A':
        print(f"  Date Range: {report['data_summary']['date_range']['start']} to {report['data_summary']['date_range']['end']}")
    
    print("\n📈 Demand Statistics:")
    stats = report['statistical_summary']
    print(f"  Mean Demand: {stats['mean']:.2f} tons")
    print(f"  Std Dev: {stats['std_dev']:.2f} tons")
    print(f"  Min/Max: {stats['min']:.2f} / {stats['max']:.2f} tons")
    print(f"  Coefficient of Variation: {stats['cv']:.3f}")
    
    print("\n🔺 Demand Peaks:")
    peaks = report['demand_peaks']
    print(f"  Peak Threshold: {peaks['threshold']:.2f} tons")
    print(f"  Number of Peaks: {peaks['num_peaks']}")
    print(f"  Percentage of Data: {peaks['percent_of_total']:.1f}%")
    
    print("\n✅ Analysis complete!")
