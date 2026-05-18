"""PyTorch 模型训练钩子 - 拦截 fit() 实现 epoch 级回调"""
import copy
import numpy as np
import torch
from typing import Callable, Optional

_PATCHED_ATTR = "_qlib_gui_patched"


class TrainingCallback:
    """训练回调基类"""
    def on_epoch_end(self, epoch: int, metrics: dict):
        pass

    def on_train_end(self, evals_result: dict):
        pass


def patch_alstm_ts_fit(model, callback: TrainingCallback):
    """ALSTM TS 模型 - 支持 pytorch_alstm_ts 模块中的 ALSTM"""
    if getattr(model, _PATCHED_ATTR, False):
        return
    original_fit = model.fit

    def patched_fit(dataset, evals_result=None, save_path=None, reweighter=None):
        if evals_result is None:
            evals_result = {}

        from qlib.data.dataset.handler import DataHandlerLP
        dl_train = dataset.prepare("train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
        dl_valid = dataset.prepare("valid", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)

        if dl_train.empty or dl_valid.empty:
            raise ValueError("数据为空，请检查数据集配置")

        dl_train.config(fillna_type="ffill+bfill")
        dl_valid.config(fillna_type="ffill+bfill")

        wl_train = np.ones(len(dl_train))
        wl_valid = np.ones(len(dl_valid))

        from torch.utils.data import DataLoader
        from qlib.contrib.model.pytorch_alstm_ts import ConcatDataset

        train_loader = DataLoader(
            ConcatDataset(dl_train, wl_train),
            batch_size=model.batch_size,
            shuffle=True,
            num_workers=model.n_jobs,
            drop_last=True,
        )
        valid_loader = DataLoader(
            ConcatDataset(dl_valid, wl_valid),
            batch_size=model.batch_size,
            shuffle=False,
            num_workers=model.n_jobs,
            drop_last=True,
        )

        from qlib.utils import get_or_create_path
        save_path = get_or_create_path(save_path)
        stop_steps = 0
        best_score = -np.inf
        best_epoch = 0
        evals_result["train"] = []
        evals_result["valid"] = []
        best_param = None

        model.fitted = True
        should_stop = False

        for step in range(model.n_epochs):
            model.train_epoch(train_loader)
            train_loss, train_score = model.test_epoch(train_loader)
            val_loss, val_score = model.test_epoch(valid_loader)

            evals_result["train"].append(train_score)
            evals_result["valid"].append(val_score)

            metrics = {
                "train_loss": train_loss,
                "train_score": train_score,
                "val_loss": val_loss,
                "val_score": val_score,
                "best_score": best_score,
                "best_epoch": best_epoch,
                "stop_steps": stop_steps,
            }

            if val_score > best_score:
                best_score = val_score
                stop_steps = 0
                best_epoch = step
                best_param = copy.deepcopy(model.ALSTM_model.state_dict())
            else:
                stop_steps += 1
                if stop_steps >= model.early_stop:
                    should_stop = True

            should_stop = should_stop or callback.on_epoch_end(step, metrics)
            if should_stop:
                break

        if best_param is not None:
            model.ALSTM_model.load_state_dict(best_param)
            torch.save(best_param, save_path)

        if hasattr(model, 'use_gpu') and model.use_gpu:
            torch.cuda.empty_cache()

        callback.on_train_end(evals_result)
        return evals_result

    setattr(model, _PATCHED_ATTR, True)
    model.fit = patched_fit


class QtSignalCallback(TrainingCallback):
    """发射 Qt 信号的回调"""
    def __init__(self, epoch_signal, finished_signal=None, stop_check: Callable = None):
        self._epoch_signal = epoch_signal
        self._finished_signal = finished_signal
        self._stop_check = stop_check or (lambda: False)

    def on_epoch_end(self, epoch: int, metrics: dict):
        if self._epoch_signal:
            self._epoch_signal.emit(epoch, metrics)
        return self._stop_check()

    def on_train_end(self, evals_result: dict):
        if self._finished_signal:
            self._finished_signal.emit(evals_result)


def patch_standard_pytorch_fit(model, callback: TrainingCallback):
    """为标准 PyTorch 模型替换 fit() 方法，在每 epoch 后调用回调

    适用于: LSTM, GRU, ALSTM, MLP, Transformer, Localformer, TCN, SFM, TabNet, GATs, ADD, KRNN, Sandwich
    这些模型共享相同的 train_epoch/test_epoch/fit 模式
    """
    if getattr(model, _PATCHED_ATTR, False):
        return
    original_fit = model.fit

    def patched_fit(dataset, evals_result=None, save_path=None):
        from qlib.data.dataset.handler import DataHandlerLP
        if evals_result is None:
            evals_result = {}

        df_train, df_valid, df_test = dataset.prepare(
            ["train", "valid", "test"],
            col_set=["feature", "label"],
            data_key=DataHandlerLP.DK_L,
        )
        if df_train.empty or df_valid.empty:
            raise ValueError("数据为空，请检查数据集配置")

        x_train, y_train = df_train["feature"], df_train["label"]
        x_valid, y_valid = df_valid["feature"], df_valid["label"]

        from qlib.utils import get_or_create_path
        save_path = get_or_create_path(save_path)
        stop_steps = 0
        best_score = -np.inf
        best_epoch = 0
        evals_result["train"] = []
        evals_result["valid"] = []
        best_param = None

        model.fitted = True
        should_stop = False

        for step in range(model.n_epochs):
            model.train_epoch(x_train, y_train)
            train_loss, train_score = model.test_epoch(x_train, y_train)
            val_loss, val_score = model.test_epoch(x_valid, y_valid)

            evals_result["train"].append(train_score)
            evals_result["valid"].append(val_score)

            metrics = {
                "train_loss": train_loss,
                "train_score": train_score,
                "val_loss": val_loss,
                "val_score": val_score,
                "best_score": best_score,
                "best_epoch": best_epoch,
                "stop_steps": stop_steps,
            }

            if val_score > best_score:
                best_score = val_score
                stop_steps = 0
                best_epoch = step
                # 获取模型参数 - 尝试不同的属性名
                model_attr = _get_model_attr(model)
                if model_attr is not None:
                    best_param = copy.deepcopy(model_attr.state_dict())
            else:
                stop_steps += 1
                if stop_steps >= model.early_stop:
                    should_stop = True

            should_stop = should_stop or callback.on_epoch_end(step, metrics)
            if should_stop:
                break

        if best_param is not None:
            model_attr = _get_model_attr(model)
            if model_attr is not None:
                model_attr.load_state_dict(best_param)
                torch.save(best_param, save_path)

        if hasattr(model, 'use_gpu') and model.use_gpu:
            torch.cuda.empty_cache()

        callback.on_train_end(evals_result)
        return evals_result

    setattr(model, _PATCHED_ATTR, True)
    model.fit = patched_fit


def _get_model_attr(model):
    """获取模型的内部 nn.Module 属性"""
    for attr_name in ["lstm_model", "gru_model", "alstm_model", "dnn_model",
                       "transformer_model", "localformer_model", "tcn_model",
                       "sfm_model", "tabnet_model", "gats_model", "add_model",
                       "krnn_model", "sandwich_model", "model"]:
        if hasattr(model, attr_name):
            attr = getattr(model, attr_name)
            if isinstance(attr, torch.nn.Module):
                return attr
    return None


def patch_lightgbm_fit(model, callback: TrainingCallback):
    """LightGBM 模型 - 训练完成后一次性回放所有迭代"""
    if getattr(model, _PATCHED_ATTR, False):
        return
    original_fit = model.fit

    def patched_fit(dataset, num_boost_round=None, early_stopping_rounds=None,
                    verbose_eval=20, evals_result=None, reweighter=None, **kwargs):
        if evals_result is None:
            evals_result = {}
        original_fit(dataset, num_boost_round=num_boost_round,
                     early_stopping_rounds=early_stopping_rounds,
                     verbose_eval=verbose_eval, evals_result=evals_result,
                     reweighter=reweighter, **kwargs)
        # 回放所有迭代结果
        for key in evals_result:
            for metric_name, values in evals_result[key].items():
                for i, v in enumerate(values):
                    metrics = {f"{metric_name}_{key}": v}
                    callback.on_epoch_end(i, metrics)
        callback.on_train_end(evals_result)
        return evals_result

    setattr(model, _PATCHED_ATTR, True)
    model.fit = patched_fit


def patch_sklearn_fit(model, callback: TrainingCallback):
    """sklearn 类模型 (XGBoost, CatBoost, Linear) - 即时完成，fit 后计算评分"""
    if getattr(model, _PATCHED_ATTR, False):
        return
    original_fit = model.fit

    def patched_fit(dataset, **kwargs):
        kwargs.pop("evals_result", None)
        result = original_fit(dataset, **kwargs)

        # fit 完成后尝试计算 IC 评分
        metrics = {"status": "completed", "train_loss": 0, "val_loss": 0,
                   "train_score": 0, "val_score": 0}
        try:
            from qlib.data.dataset.handler import DataHandlerLP
            df_train, df_valid = dataset.prepare(
                ["train", "valid"],
                col_set=["feature", "label"],
                data_key=DataHandlerLP.DK_L,
            )
            if not df_train.empty:
                pred_train = model.predict(df_train["feature"])
                label_train = df_train["label"].iloc[:, 0]
                metrics["train_score"] = float(np.corrcoef(pred_train, label_train)[0, 1])
            if not df_valid.empty:
                pred_valid = model.predict(df_valid["feature"])
                label_valid = df_valid["label"].iloc[:, 0]
                metrics["val_score"] = float(np.corrcoef(pred_valid, label_valid)[0, 1])
        except Exception:
            pass

        callback.on_epoch_end(0, metrics)
        callback.on_train_end({"train": [metrics["train_score"]], "valid": [metrics["val_score"]]})
        return result

    setattr(model, _PATCHED_ATTR, True)
    model.fit = patched_fit


# 模型类型到 patch 函数的映射
PATCH_MAP = {
    "pytorch": patch_standard_pytorch_fit,
    "lightgbm": patch_lightgbm_fit,
    "sklearn": patch_sklearn_fit,
    "alstm_ts": patch_alstm_ts_fit,
}


def apply_training_hook(model, model_type: str, callback: TrainingCallback):
    """根据模型类型应用对应的训练钩子"""
    if getattr(model, _PATCHED_ATTR, False):
        return
    patch_fn = PATCH_MAP.get(model_type)
    if patch_fn:
        patch_fn(model, callback)
