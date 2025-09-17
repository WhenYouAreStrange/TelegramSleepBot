# -*- coding: utf-8 -*-

from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from db import get_sleep_data
from utils import calculate_sleep_duration


async def analyze_sleep_data(user_id: int) -> Optional[str]:
    """
    Анализирует данные о сне пользователя и возвращает персональный совет.
    """
    sleep_data = await get_sleep_data(user_id)

    if len(sleep_data) < 7:
        # Недостаточно данных для анализа, возвращаем None, чтобы отправить общий совет
        return None

    recent_sleep_data = sleep_data[-7:]
    durations = [calculate_sleep_duration(
        entry[0], entry[1]) for entry in recent_sleep_data]

    # 1. Анализ средней продолжительности сна
    avg_duration = sum(durations) / len(durations)
    if avg_duration < 7:
        return (
            f"Анализ вашего сна за последнюю неделю показывает, что вы спите в среднем {avg_duration:.1f} часов. "
            f"Это меньше рекомендуемых 7-9 часов. Постарайтесь ложиться спать раньше, чтобы увеличить продолжительность сна."
        )
    if avg_duration > 9:
        return (
            f"Анализ вашего сна за последнюю неделю показывает, что вы спите в среднем {avg_duration:.1f} часов. "
            f"Иногда слишком долгий сон может быть признаком некачественного отдыха. "
            f"Попробуйте проветривать комнату перед сном и избегать тяжелой пищи на ночь."
        )

    # 2. Анализ стабильности режима
    wake_times = [datetime.strptime(
        entry[1], '%H:%M') for entry in recent_sleep_data]
    time_diffs = [(wake_times[i+1] - wake_times[i]).total_seconds() /
                  3600 for i in range(len(wake_times) - 1)]
    # Используем абсолютные значения для разницы во времени
    abs_diffs = [abs(d) % 24 for d in time_diffs]
    avg_diff = sum(abs_diffs) / len(abs_diffs) if abs_diffs else 0

    if avg_diff > 1.5:  # Если среднее отклонение времени пробуждения больше 1.5 часов
        return (
            "Ваш график пробуждения за последнюю неделю был довольно нестабильным. "
            "Старайтесь просыпаться примерно в одно и то же время даже в выходные, "
            "чтобы наладить внутренние часы организма."
        )

    # 3. Анализ времени отхода ко сну
    sleep_times_dt = [datetime.strptime(
        s[0], '%H:%M') for s in recent_sleep_data]
    # Корректируем дату для времени после полуночи
    corrected_sleep_times = []
    for i, dt in enumerate(sleep_times_dt):
        if i > 0 and dt < corrected_sleep_times[i-1] - timedelta(hours=12):
            corrected_sleep_times.append(dt + timedelta(days=1))
        else:
            corrected_sleep_times.append(dt)

    late_sleep_count = sum(
        1 for t in corrected_sleep_times if t.hour >= 1 and t.hour < 12)
    if late_sleep_count >= 3:
        return (
            "Вы несколько раз за последнюю неделю ложились спать после часа ночи. "
            "Поздний отход ко сну может нарушать циркадные ритмы. "
            "Попробуйте сместить время отхода ко сну на более раннее."
        )

    return "Ваш режим сна за последнюю неделю выглядит стабильным и достаточным. Отличная работа! Продолжайте в том же духе."