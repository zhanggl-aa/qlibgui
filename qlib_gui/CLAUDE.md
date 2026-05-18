# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
python main.py
```

Requires: `PyQt6`, `pyqtgraph`, `qlib`, `pyyaml`, `torch` (for neural models), `lightgbm`/`xgboost`/`catboost` (for tree models). Qlib data must be initialized at `~/.qlib/qlib_data/cn_data` (download via `python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn`).

## Architecture

This is a **PyQt6 desktop GUI** for Microsoft's Qlib quantitative investment framework. The UI is in Chinese (中文). The app wraps 25 Qlib benchmark models with a visual pipeline: model selection → training → backtest → simulation.

### Three-layer structure

- **`core/`** — Business logic, no Qt widget imports (except QThread/QObject for engines)
- **`pages/`** — Six page widgets stacked in `MainWindow` via `QStackedWidget`, each is a full-screen view
- **`widgets/`** — Reusable UI components (charts, tables, panels)

### Data flow

`MainWindow` (`app.py`) is the orchestrator. Pages communicate **only through signals** — `MainWindow._connect_signals()` wires page signals to handlers that drive the pipeline:

1. **ModelPage** emits `training_requested(config)` → MainWindow creates model+dataset, launches `TrainingEngine`
2. **TrainingEngine** (QThread) emits `epoch_completed` / `training_finished` → TrainingPage updates charts
3. After training, **TrainingPage** emits `backtest_requested` → MainWindow runs `BacktestEngine` (QThread)
4. Backtest results flow to **BacktestPage**, which can navigate to **SimulationPage**

### Key core modules

- **`model_registry.py`** — Static manifest of 25 models (`MODEL_MANIFEST` list). On `discover_all()`, scans `examples/benchmarks/*/` YAML files to extract default kwargs, available datasets, and markets. Model classes are lazy-imported via `importlib`.
- **`training_hooks.py`** — Monkey-patches `model.fit()` to inject epoch-level callbacks. Three patch strategies: `patch_standard_pytorch_fit` (iterates `n_epochs`, calls `train_epoch`/`test_epoch`), `patch_lightgbm_fit` (replays all boosting iterations after fit), `patch_sklearn_fit` (single-shot, no iteration). Selected by `model_type` field in `ModelInfo`.
- **`training_engine.py`** / **`backtest_engine.py`** — QThread subclasses. TrainingEngine applies hooks then calls `model.fit()`. BacktestEngine calls `qlib.contrib.evaluate.backtest_daily`.
- **`simulation_engine.py`** — Runs in the **main thread** (not QThread). Step-by-step replay of trading days with manual `place_order()` and auto-trade via `TopkDropoutStrategy`. Uses `QTimer` for auto-play.
- **`config_parser.py`** — Reads/writes Qlib YAML workflow configs. `build_full_config()` assembles the complete config dict from model + dataset + backtest parameters.

### Widget details

- **`chart_widget.py`** — `RealtimeChart` wraps `pyqtgraph.PlotWidget` with series management and crosshair. `ReturnChart` adds strategy/benchmark/excess curves.
- **`sidebar.py`** — Navigation with `page_changed` signal; page IDs: `home`, `model`, `training`, `backtest`, `simulation`, `experiment`.
- **`metric_card.py`** — KPI card with title/value/unit; `MetricRow` lays them out horizontally.
- **`stock_table.py`** — Signal ranking table with position overlay.
- **`order_panel.py`** — Manual order entry (stock_id, amount, buy/sell), emits `order_submitted`.
- **`position_widget.py`** — Account summary + position table.
- **`param_editor.py`** — QTreeWidget-based key-value editor with type-preserving collection.

### Model categories

- **tree**: LightGBM, XGBoost, CatBoost, DoubleEnsemble, Linear (`model_type` = `lightgbm` or `sklearn`)
- **neural**: LSTM, GRU, ALSTM, MLP, Transformer, Localformer, TFT, TCN, SFM, TabNet (`model_type` = `pytorch` or `tensorflow`)
- **advanced**: GATs, HIST, IGMTF, KRNN, Sandwich, ADARNN, ADD, TCTS, TRA, GeneralPtNN (`model_type` = `pytorch`)

## Conventions

- All user-facing strings are in Chinese
- QThread engines use pyqtSignal for progress/result communication — never call widgets directly from worker threads
- The `_get_model_attr()` helper in `training_hooks.py` discovers the internal `nn.Module` by checking known attribute names — add new model attribute names there when adding new PyTorch models
- Page navigation is always via `sidebar.page_changed` signal → `MainWindow._switch_page()`, never direct
