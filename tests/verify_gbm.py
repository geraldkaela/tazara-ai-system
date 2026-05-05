import os
import sys
import pandas as pd
import numpy as np
import logging

# Add project root to path
sys.path.append(os.getcwd())

from forecasting.demand_forecasting import DemandForecastingEngine
from forecasting.advanced_ml_models import ModelComparator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_gbm():
    print("\n" + "="*60)
    print("🧪 VERIFYING GBM INTEGRATION")
    print("="*60)
    
    # 1. Test DemandForecastingEngine with GBM
    print("\n📦 Testing DemandForecastingEngine...")
    engine = DemandForecastingEngine()
    
    print("Training GBM model...")
    gbm_result = engine.train_gbm()
    assert gbm_result['status'] == 'success', f"GBM training failed: {gbm_result.get('message')}"
    print(f"✅ GBM Trained. Metrics: {gbm_result['metrics']}")
    
    print("Generating GBM forecast...")
    forecast = engine.forecast_gbm(forecast_steps=7)
    assert 'forecast' in forecast, "GBM forecast failed"
    assert len(forecast['forecast']) == 7, f"Expected 7 steps, got {len(forecast['forecast'])}"
    print(f"✅ GBM Forecast: {forecast['forecast']}")
    
    print("Testing Ensemble with GBM...")
    ensemble = engine.ensemble_forecast(forecast_steps=7)
    assert 'gbm' in ensemble['models_combined'], "GBM should be in ensemble"
    print(f"✅ Ensemble with GBM generated: {ensemble['models_combined']}")

    # 2. Test ModelComparator with GBM
    print("\n📊 Testing ModelComparator...")
    data = engine.ts_data
    comparator = ModelComparator(data)
    results = comparator.compare_models()
    assert 'gbm' in results, "GBM should be in comparison results"
    print(f"✅ GBM included in ranking: {[name for name in results.keys()]}")

    print("\n" + "="*60)
    print("🎉 ALL GBM VERIFICATIONS PASSED!")
    print("="*60)

if __name__ == "__main__":
    try:
        verify_gbm()
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
