from custom_exceptions import (
    PLCSystemError,
    CycleTimeExceededError,
    CurrentLoopSensorError,
    WatchdogTimeoutError,
)

MIN_CYCLE_MS = 1.0
MAX_CYCLE_MS = 50.0
MIN_CURRENT_MA = 3.8
MAX_CURRENT_MA = 20.5


def validate_cycle_time(raw_cycle_ms: object) -> float:
    """Валідує час циклу PLC у межах 1..50 мс за парадигмою EAFP."""
    try:
        cycle_ms = float(raw_cycle_ms)
    except (TypeError, ValueError) as exc:
        raise PLCSystemError(f"Некоректний формат часу циклу '{raw_cycle_ms}'.", error_code=1100) from exc

    if cycle_ms < MIN_CYCLE_MS or cycle_ms > MAX_CYCLE_MS:
        raise CycleTimeExceededError(
            cycle_ms=cycle_ms,
            min_allowed_ms=MIN_CYCLE_MS,
            max_allowed_ms=MAX_CYCLE_MS,
        )
    return cycle_ms


def validate_current_loop_channel(channel_cfg: dict) -> tuple[int, float]:
    """Валідує канал струмової петлі 4..20 мА (3.8..20.5 мА) за парадигмою EAFP."""
    try:
        ch_id = int(channel_cfg["channel"])
        current_ma = float(channel_cfg["current_ma"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PLCSystemError("Помилка структури або типів даних каналу струмової петлі.", error_code=1200) from exc

    if current_ma < MIN_CURRENT_MA or current_ma > MAX_CURRENT_MA:
        raise CurrentLoopSensorError(
            channel_id=ch_id,
            current_ma=current_ma,
            min_allowed_ma=MIN_CURRENT_MA,
            max_allowed_ma=MAX_CURRENT_MA,
        )
    return ch_id, current_ma


def validate_watchdog_interval(raw_elapsed_ms: object, timeout_ms: float = 100.0) -> float:
    """Перевіряє інтервал сторожового таймера PLC."""
    try:
        elapsed_ms = float(raw_elapsed_ms)
        limit_ms = float(timeout_ms)
    except (TypeError, ValueError) as exc:
        raise PLCSystemError("Некоректні числові параметри сторожового таймера.", error_code=1300) from exc

    if elapsed_ms > limit_ms:
        raise WatchdogTimeoutError(elapsed_ms=elapsed_ms, timeout_ms=limit_ms)
    return elapsed_ms


def validate_plc_snapshot(snapshot: dict) -> dict:
    """Комплексна валідація стану контролера PLC."""
    try:
        raw_cycle = snapshot["cycle_ms"]
        channels = snapshot["channels"]
        raw_watchdog = snapshot["watchdog_ms"]
    except (KeyError, TypeError) as exc:
        raise PLCSystemError("Відсутні обов'язкові поля у знімку стану PLC.", error_code=1001) from exc

    valid_cycle = validate_cycle_time(raw_cycle)

    try:
        iterator = iter(channels)
    except TypeError as exc:
        raise PLCSystemError("Поле 'channels' має бути ітерованою колекцією.", error_code=1201) from exc

    validated_channels = []
    for ch in iterator:
        validated_channels.append(validate_current_loop_channel(ch))

    valid_watchdog = validate_watchdog_interval(raw_watchdog)

    return {
        "cycle_ms": valid_cycle,
        "channels": validated_channels,
        "watchdog_ms": valid_watchdog,
    }
