"""训练引擎 - 在 QThread 中运行模型训练"""
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional


class TrainingEngine(QThread):
    """后台训练线程"""

    epoch_completed = pyqtSignal(int, dict)  # (epoch, {train_loss, val_loss, ...})
    training_finished = pyqtSignal(dict)     # evals_result
    training_error = pyqtSignal(str)         # 错误消息
    progress_update = pyqtSignal(int, int)   # (current, total)

    def __init__(self, model, dataset, model_type: str = "pytorch", parent=None):
        super().__init__(parent)
        self.model = model
        self.dataset = dataset
        self.model_type = model_type
        self._should_stop = False
        self._callback = None
        # 允许对同一模型重新 patch
        if hasattr(model, "_qlib_gui_patched"):
            delattr(model, "_qlib_gui_patched")

    def run(self):
        try:
            from qlib_gui.core.training_hooks import TrainingCallback

            class EngineCallback(TrainingCallback):
                def __init__(self, engine):
                    self.engine = engine

                def on_epoch_end(self, epoch, metrics):
                    self.engine.epoch_completed.emit(epoch, metrics)
                    total = getattr(self.engine.model, 'n_epochs', 1)
                    self.engine.progress_update.emit(epoch + 1, total)
                    return self.engine._should_stop

                def on_train_end(self, evals_result):
                    self.engine.training_finished.emit(evals_result or {})

            self._callback = EngineCallback(self)

            from qlib_gui.core.training_hooks import apply_training_hook
            apply_training_hook(self.model, self.model_type, self._callback)

            if self.model_type == "lightgbm":
                self.model.fit(self.dataset, evals_result={})
            elif self.model_type == "sklearn":
                self.model.fit(self.dataset)
            else:
                self.model.fit(self.dataset)

        except Exception as e:
            self.training_error.emit(str(e))

    def request_stop(self):
        self._should_stop = True
