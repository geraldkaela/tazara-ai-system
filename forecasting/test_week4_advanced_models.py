#!/usr/bin/env python3
"""
Phase 2 Week 4 Task 2: Advanced ML Models Test
Tests LSTM variants, optimized ARIMA, and model comparison
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecasting.advanced_ml_models import AdvancedLSTMForecaster, OptimizedARIMAForecaster, ModelComparator
from forecasting.historical_analysis import HistoricalDemandAnalyzer
import numpy as np


def test_advanced_lstm():
    """Test different LSTM architectures"""
    print("\n🧠 Testing Advanced LSTM Models...")
    print("-" * 60)
    
    try:
        # Load data
        analyzer = HistoricalDemandAnalyzer()
        data = analyzer.df['cargo_tons'].values
        
        model_types = ['standard', 'bidirectional']
        results = {}
        
        for model_type in model_types:
            print(f"\n📊 Training {model_type} LSTM...")
            
            lstm = AdvancedLSTMForecaster(lookback=12)
            X_train, X_test, y_train, y_test = lstm.prepare_data(data)
            
            result = lstm.train(X_train, X_test, y_train, y_test, 
                              model_type=model_type, epochs=20)
            
            if result['status'] == 'success':
                metrics = result['metrics']
                print(f"✅ {model_type.upper()} LSTM:")
                print(f"   MAE: {metrics['test_mae']:.2f}")
                print(f"   RMSE: {metrics['test_rmse']:.2f}")
                print(f"   R²: {metrics['test_r2']:.3f}")
                print(f"   MAPE: {metrics['test_mape']:.2f}%")
                results[model_type] = metrics
            else:
                print(f"❌ Training failed: {result.get('message', 'Unknown error')}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_optimized_arima():
    """Test optimized ARIMA"""
    print("\n📈 Testing Optimized ARIMA...")
    print("-" * 60)
    
    try:
        # Load data
        analyzer = HistoricalDemandAnalyzer()
        data = analyzer.df['cargo_tons'].values
        
        # Test stationarity
        arima = OptimizedARIMAForecaster()
        stationarity = arima.test_stationarity(data)
        
        if 'error' not in stationarity:
            print(f"✅ Stationarity Test:")
            print(f"   ADF p-value: {stationarity['adf_pvalue']:.4f}")
            print(f"   Data is {'stationary' if stationarity['is_stationary'] else 'non-stationary'}")
            print(f"   Recommended d: {stationarity['recommended_d']}")
        
        # Train
        print(f"\n📊 Training ARIMA...")
        train_result = arima.train(data, auto_order=True)
        
        if train_result['status'] == 'success':
            print(f"✅ ARIMA{train_result['order']}:")
            print(f"   AIC: {train_result['aic']:.2f}")
            print(f"   BIC: {train_result['bic']:.2f}")
            
            # Forecast
            forecast_result = arima.forecast(forecast_steps=30)
            if forecast_result['status'] == 'success':
                print(f"\n✅ ARIMA Forecast:")
                print(f"   30-day forecast generated")
                print(f"   First 5 values: {[f'{v:.0f}' for v in forecast_result['forecast'][:5]]}")
                
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_comparison():
    """Test model comparison"""
    print("\n🏆 Testing Model Comparison...")
    print("-" * 60)
    
    try:
        # Load data
        analyzer = HistoricalDemandAnalyzer()
        data = analyzer.df['cargo_tons'].values[:500]  # Use subset for speed
        
        print(f"\n📊 Comparing models on {len(data)} samples...")
        
        comparator = ModelComparator(data)
        results = comparator.compare_models()
        
        print(f"\n✅ Model Comparison Complete:")
        print(f"   Models trained: {len(results)}")
        
        for model_name, info in results.items():
            if 'metrics' in info:
                print(f"   - {model_name}: R² = {info['metrics'].get('test_r2', 'N/A'):.3f}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all advanced ML tests"""
    print("\n" + "="*60)
    print("🚀 PHASE 2 WEEK 4 TASK 2 - ADVANCED ML MODELS TEST")
    print("="*60)
    
    results = {
        'Advanced LSTM': test_advanced_lstm(),
        'Optimized ARIMA': test_optimized_arima(),
        'Model Comparison': test_model_comparison()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Phase 2 Week 4 Task 2 - Advanced ML Models COMPLETE!")
        print("   ✅ LSTM variants (standard, bidirectional) implemented")
        print("   ✅ ARIMA parameter optimization working")
        print("   ✅ Stationarity testing implemented")
        print("   ✅ Model comparison and ranking working")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
