class PLCSystemError(Exception):
    """Базовий виняток підсистеми керування промисловим контролером PLC."""

    def __init__(self, message: str, error_code: int = 1000) -> None:
        self.error_code = error_code
        super().__init__(f"[PLC-ERR {error_code}] {message}")


class CycleTimeExceededError(PLCSystemError):
    """Перевищення або порушення допустимого часу циклу PLC (1.0 .. 50.0 мс)."""

    def __init__(
        self,
        cycle_ms: float,
        min_allowed_ms: float = 1.0,
        max_allowed_ms: float = 50.0,
        error_code: int = 1101,
    ) -> None:
        self.cycle_ms = cycle_ms
        self.min_allowed_ms = min_allowed_ms
        self.max_allowed_ms = max_allowed_ms
        self.delta_ms = (
            max(0.0, cycle_ms - max_allowed_ms)
            if cycle_ms > max_allowed_ms
            else max(0.0, min_allowed_ms - cycle_ms)
        )
        super().__init__(
            f"Недопустимий час циклу PLC: {cycle_ms:.3f} мс (допустимо {min_allowed_ms:.1f}..{max_allowed_ms:.1f} мс, відхилення {self.delta_ms:.3f} мс).",
            error_code=error_code,
        )


class CurrentLoopSensorError(PLCSystemError):
    """Помилка аналогового входу струмової петлі 4..20 мА (допустимо 3.8 .. 20.5 мА)."""

    def __init__(
        self,
        channel_id: int,
        current_ma: float,
        min_allowed_ma: float = 3.8,
        max_allowed_ma: float = 20.5,
        error_code: int = 1202,
    ) -> None:
        self.channel_id = channel_id
        self.current_ma = current_ma
        self.min_allowed_ma = min_allowed_ma
        self.max_allowed_ma = max_allowed_ma
        super().__init__(
            f"Канал AI#{channel_id}: струм {current_ma:.3f} мА поза межами {min_allowed_ma:.1f}..{max_allowed_ma:.1f} мА.",
            error_code=error_code,
        )


class WatchdogTimeoutError(PLCSystemError):
    """Помилка сторожового таймера (Watchdog) контролера PLC."""

    def __init__(
        self,
        elapsed_ms: float,
        timeout_ms: float = 100.0,
        error_code: int = 1303,
    ) -> None:
        self.elapsed_ms = elapsed_ms
        self.timeout_ms = timeout_ms
        self.overrun_ms = max(0.0, elapsed_ms - timeout_ms)
        super().__init__(
            f"Спрацював сторожовий таймер PLC: {elapsed_ms:.2f} мс при ліміті {timeout_ms:.2f} мс (+{self.overrun_ms:.2f} мс).",
            error_code=error_code,
        )
