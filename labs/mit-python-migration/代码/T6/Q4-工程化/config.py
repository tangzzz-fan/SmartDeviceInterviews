"""
T6-Q4 配置模块：环境变量 + 默认值 + 启动校验（fail fast）

类比 iOS：env 变量 ≈ xcconfig 分环境、代码默认值 ≈ Info.plist 基线、
启动校验 ≈ AppDelegate 里的 precondition——缺必填项宁可启动时炸，
不要运行到一半拿 None 去调 API。
"""
import os
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class GatewayConfig:
    api_key: str            # 必填：没有 key 启动即炸
    concurrency: int = 4    # 默认值兜底
    per_call_timeout: float = 30.0
    max_retries: int = 3
    endpoint: str = "https://api.mock-llm.local/v1"

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        api_key = env.get("LLM_API_KEY", "").strip()
        if not api_key:
            raise ConfigError(
                "缺必填配置 LLM_API_KEY（环境变量未设置）——fail fast，拒绝带病启动"
            )

        def read(name, default, cast):
            raw = env.get(name)
            if raw is None or raw == "":
                return default
            try:
                return cast(raw)
            except ValueError as e:
                raise ConfigError(f"配置 {name}={raw!r} 无法解析为 {cast.__name__}") from e

        return cls(
            api_key=api_key,
            concurrency=read("LLM_GATEWAY_CONCURRENCY", 4, int),
            per_call_timeout=read("LLM_GATEWAY_TIMEOUT", 30.0, float),
            max_retries=read("LLM_GATEWAY_MAX_RETRIES", 3, int),
            endpoint=env.get("LLM_ENDPOINT", "https://api.mock-llm.local/v1"),
        )
