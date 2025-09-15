from datetime import datetime
from db import get_sleep_data, get_achievements, insert_achievement
from utils import calculate_sleep_duration

def check_achievements(user_id):
    user_data = get_sleep_data(user_id)
    achievements = get_achievements(user_id)

    new_achievements = []

    if len(user_data) >= 3 and 'Сонный новичок' not in achievements:
        new_achievements.append('Сонный новичок')

    if len(user_data) >= 7 and 'Сонный эксперт' not in achievements:
        new_achievements.append('Сонный эксперт')

    if len(user_data) >= 30 and 'Мастер сна' not in achievements:
        new_achievements.append('Мастер сна')

    if len(user_data) >= 100 and 'Повелитель снов' not in achievements:
        new_achievements.append('Повелитель снов')

    if all(datetime.strptime(entry[0], '%H:%M').hour < 22 for entry in user_data[-5:]) and 'Ранняя пташка' not in achievements:
        new_achievements.append('Ранняя пташка')

    # Ночной сова: последние 5 записей с поздним отходом (>= 00:30)
    def is_late_bedtime(hhmm: str) -> bool:
        t = datetime.strptime(hhmm, '%H:%M')
        return t.hour > 0 or (t.hour == 0 and t.minute >= 30)

    if len(user_data) >= 5 and all(is_late_bedtime(entry[0]) for entry in user_data[-5:]) and 'Ночная сова' not in achievements:
        new_achievements.append('Ночная сова')

    # Идеальный сон: продолжительность последнего сна от 7 до 9 часов
    if user_data:
        last_sleep_entry = user_data[-1]
        sleep_duration = calculate_sleep_duration(last_sleep_entry[0], last_sleep_entry[1])
        if 7 <= sleep_duration <= 9 and 'Идеальный сон' not in achievements:
            new_achievements.append('Идеальный сон')

    # "Стабильный режим": ложится и встает примерно в одно и то же время (разница не более 30 минут) 5 дней подряд.
    def time_to_minutes(hhmm: str) -> int:
        t = datetime.strptime(hhmm, '%H:%M')
        minutes = t.hour * 60 + t.minute
        if t.hour < 12:  # Сдвигаем утренние часы вперед для корректного сравнения
            minutes += 24 * 60
        return minutes

    if len(user_data) >= 5 and 'Стабильный режим' not in achievements:
        last_five_entries = user_data[-5:]
        
        sleep_times_in_minutes = [time_to_minutes(entry[0]) for entry in last_five_entries]
        wake_times_in_minutes = [datetime.strptime(entry[1], '%H:%M').hour * 60 + datetime.strptime(entry[1], '%H:%M').minute for entry in last_five_entries]

        sleep_diff = max(sleep_times_in_minutes) - min(sleep_times_in_minutes)
        wake_diff = max(wake_times_in_minutes) - min(wake_times_in_minutes)

        if sleep_diff <= 30 and wake_diff <= 30:
            new_achievements.append('Стабильный режим')

    for achievement in new_achievements:
        insert_achievement(user_id, achievement)

    return new_achievements
