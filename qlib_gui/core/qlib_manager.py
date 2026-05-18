"""Qlib 初始化管理器 - 单例模式"""
import os
from pathlib import Path


class QlibManager:
    """确保 qlib.init() 只调用一次"""

    _initialized = False
    _provider_uri = os.path.expanduser("~/.qlib/qlib_data/cn_data")
    _region = "cn"
    _init_error = ""
    _init_error_type = None  # "not_installed" | "init_failed" | "no_data" | None

    @classmethod
    def initialize(cls, provider_uri: str = None, region: str = None) -> bool:
        if cls._initialized:
            return True
        if provider_uri:
            cls._provider_uri = provider_uri
        if region:
            cls._region = region
        if not cls.check_data_available():
            cls._init_error = f"数据目录不存在或为空: {cls._provider_uri}"
            cls._init_error_type = "no_data"
            return False
        try:
            import qlib
        except ImportError:
            cls._init_error = "qlib 未安装。请运行: pip install pyqlib"
            cls._init_error_type = "not_installed"
            return False
        try:
            qlib.init(provider_uri=cls._provider_uri, region=cls._region)
            cls._initialized = True
            cls._init_error = ""
            cls._init_error_type = None
            return True
        except Exception as e:
            cls._init_error = str(e)
            cls._init_error_type = "init_failed"
            return False

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._initialized

    @classmethod
    def check_data_available(cls) -> bool:
        path = Path(cls._provider_uri)
        return path.exists() and any(path.iterdir()) if path.exists() else False

    @classmethod
    def get_provider_uri(cls) -> str:
        return cls._provider_uri

    @classmethod
    def set_provider_uri(cls, uri: str):
        cls._provider_uri = os.path.expanduser(uri)

    @classmethod
    def get_last_error(cls) -> str:
        """返回最后一次初始化错误消息"""
        return cls._init_error

    @classmethod
    def get_last_error_type(cls) -> str:
        """返回最后一次初始化错误类型: not_installed / init_failed / no_data / None"""
        return cls._init_error_type
