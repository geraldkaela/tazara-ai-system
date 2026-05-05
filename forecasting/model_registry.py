"""Model registry and versioning system for forecasting models.

Tracks trained models, versions, metrics, and supports model selection/comparison.
Maintains a registry JSON file (`models/model_registry.json`) with metadata for all models.

Usage:
    python -m forecasting.model_registry --list
    python -m forecasting.model_registry --select lstm
    python -m forecasting.model_registry --compare
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


REGISTRY_PATH = Path("models/model_registry.json")
METRICS_PATH = Path("metrics/training_metrics.json")
MODELS_DIR = Path("models")


def load_registry() -> dict:
    """Load model registry from JSON."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {"models": {}, "selected": None}


def save_registry(registry: dict) -> None:
    """Save model registry to JSON."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Saved registry to {REGISTRY_PATH}")


def register_model(name: str, model_type: str, path: str, metrics: dict) -> None:
    """Register a new model version."""
    registry = load_registry()
    
    if name not in registry["models"]:
        registry["models"][name] = {"versions": []}
    
    version_num = len(registry["models"][name]["versions"]) + 1
    version_info = {
        "version": version_num,
        "timestamp": datetime.now().isoformat(),
        "type": model_type,
        "path": path,
        "metrics": metrics,
        "status": "active"
    }
    registry["models"][name]["versions"].append(version_info)
    logger.info(f"Registered {name} v{version_num}")
    
    save_registry(registry)


def list_models() -> None:
    """List all registered models and versions."""
    registry = load_registry()
    
    print("\n" + "="*70)
    print("📦 MODEL REGISTRY")
    print("="*70)
    
    if not registry["models"]:
        print("No models registered yet.")
        return
    
    for model_name, model_info in registry["models"].items():
        print(f"\n🔹 {model_name.upper()}")
        for v in model_info["versions"]:
            print(f"   Version {v['version']} ({v['type']})")
            print(f"   📅 {v['timestamp']}")
            print(f"   📁 {v['path']}")
            print(f"   📊 Metrics:")
            for metric_name, metric_val in v["metrics"].items():
                if metric_name not in ["model_path", "error"]:
                    print(f"      {metric_name}: {metric_val:.4f}" if isinstance(metric_val, float) else f"      {metric_name}: {metric_val}")
    
    if registry["selected"]:
        print(f"\n✅ Currently selected model: {registry['selected']}")
    print()


def select_model(name: str) -> None:
    """Select a model as the active model."""
    registry = load_registry()
    
    if name not in registry["models"]:
        logger.error(f"Model '{name}' not found in registry")
        return
    
    registry["selected"] = name
    save_registry(registry)
    logger.info(f"Selected model: {name}")
    print(f"✅ Selected model: {name}")


def compare_models() -> None:
    """Compare all registered models by key metrics."""
    registry = load_registry()
    
    print("\n" + "="*70)
    print("📊 MODEL COMPARISON")
    print("="*70)
    
    if not registry["models"]:
        print("No models to compare.")
        return
    
    # Collect best version per model
    comparisons = []
    for model_name, model_info in registry["models"].items():
        if model_info["versions"]:
            latest = model_info["versions"][-1]
            metrics = latest.get("metrics", {})
            comparisons.append({
                "name": model_name,
                "type": latest["type"],
                "rmse": metrics.get("rmse", float("inf")),
                "mae": metrics.get("mae", float("inf")),
                "r2": metrics.get("r2", -1),
                "version": latest["version"],
                "timestamp": latest["timestamp"]
            })
    
    # Sort by RMSE (lower is better)
    comparisons.sort(key=lambda x: x["rmse"])
    
    print("\nRanked by RMSE (lower is better):\n")
    for rank, comp in enumerate(comparisons, 1):
        winner = "🏆" if rank == 1 else "  "
        print(f"{winner} {rank}. {comp['name']} (v{comp['version']})")
        print(f"   Type: {comp['type']}")
        print(f"   RMSE: {comp['rmse']:.4f} | MAE: {comp['mae']:.4f} | R²: {comp['r2']:.4f}")
        print(f"   📅 {comp['timestamp']}\n")
    
    best = comparisons[0]
    print(f"✅ Best model: {best['name']} with RMSE={best['rmse']:.4f}")
    print()


def sync_from_metrics() -> None:
    """Sync new trained models from metrics JSON to registry."""
    if not METRICS_PATH.exists():
        logger.warning(f"Metrics file not found: {METRICS_PATH}")
        return
    
    with open(METRICS_PATH) as f:
        metrics_data = json.load(f)
    
    # Register LSTM if present
    if "lstm" in metrics_data and "model_path" in metrics_data["lstm"]:
        lstm_metrics = {k: v for k, v in metrics_data["lstm"].items() if k != "model_path"}
        register_model("lstm", "LSTM", metrics_data["lstm"]["model_path"], lstm_metrics)
    
    # Register ARIMA if present
    if "arima" in metrics_data and "model_path" in metrics_data["arima"]:
        arima_metrics = {k: v for k, v in metrics_data["arima"].items() if k != "model_path"}
        register_model("arima", "ARIMA", metrics_data["arima"]["model_path"], arima_metrics)
        
    # Register GBM if present
    if "gbm" in metrics_data and "model_path" in metrics_data["gbm"]:
        gbm_metrics = {k: v for k, v in metrics_data["gbm"].items() if k != "model_path"}
        register_model("gbm", "GBM", metrics_data["gbm"]["model_path"], gbm_metrics)


def _cli():
    parser = argparse.ArgumentParser(description="Model registry and versioning")
    parser.add_argument("--list", action="store_true", help="List all models and versions")
    parser.add_argument("--select", type=str, help="Select a model as active")
    parser.add_argument("--compare", action="store_true", help="Compare all models")
    parser.add_argument("--sync", action="store_true", help="Sync models from training metrics")
    
    args = parser.parse_args()
    
    if args.sync:
        sync_from_metrics()
    
    if args.list:
        list_models()
    elif args.select:
        select_model(args.select)
    elif args.compare:
        compare_models()
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
