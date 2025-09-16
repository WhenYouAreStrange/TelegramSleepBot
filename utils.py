import os
import random
import re
from datetime import datetime, timedelta
from typing import List
from dotenv import load_dotenv, dotenv_values


def load_lines(filename: str) -> List[str]:
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        return lines
    except FileNotFoundError:
        return []


def load_tips(filename: str = 'sleep_tips.txt') -> List[str]:
    return load_lines(filename)


def load_exercises(filename: str = 'sleep_exercises.txt') -> List[str]:
    return load_lines(filename)


def is_valid_time(time_str: str) -> bool:
    match = re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', time_str)
    return bool(match)


def choose_random_non_repeating(user_last_map: dict, user_id: int, items: List[str]) -> str | None:
    if not items:
        return None
    choice = random.choice(items)
    # Avoid repeating previous item for the same user
    if user_id in user_last_map and len(items) > 1:
        while choice == user_last_map[user_id]:
            choice = random.choice(items)
    user_last_map[user_id] = choice
    return choice


def calculate_sleep_duration(sleep_time: str, wake_time: str) -> float:
    sleep_dt = datetime.strptime(sleep_time, '%H:%M')
    wake_dt = datetime.strptime(wake_time, '%H:%M')
    if wake_dt < sleep_dt:
        wake_dt += timedelta(days=1)
    duration = (wake_dt - sleep_dt).seconds / 3600
    return duration


def get_token_from_dotenv_file() -> str:
    config = dotenv_values(".env")
    token = config.get('TELEGRAM_BOT_TOKEN')
    if token:
        return token
    raise RuntimeError('Telegram bot token is not set in .env file.')
