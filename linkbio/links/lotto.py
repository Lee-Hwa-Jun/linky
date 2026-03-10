from __future__ import annotations

from datetime import date, time, timedelta

from django.utils import timezone

BASE_DRAW_DATE = date(2026, 3, 14)
BASE_DRAW_ROUND = 1215
DRAW_CUTOFF_TIME = time(21, 0)


def normalize_lotto_numbers(numbers) -> list[int]:
    normalized = sorted(int(number) for number in numbers)
    if len(normalized) != 6:
        raise ValueError("로또 번호는 6개여야 합니다.")
    if len(set(normalized)) != 6:
        raise ValueError("로또 번호는 중복될 수 없습니다.")
    if any(number < 1 or number > 45 for number in normalized):
        raise ValueError("로또 번호는 1부터 45 사이여야 합니다.")
    return normalized


def determine_draw_date(now=None) -> date:
    local_now = timezone.localtime(now or timezone.now())
    weekday = local_now.weekday()
    days_until_saturday = (5 - weekday) % 7
    target_date = local_now.date() + timedelta(days=days_until_saturday)

    if weekday == 5 and local_now.time() >= DRAW_CUTOFF_TIME:
        return target_date + timedelta(days=7)
    if weekday == 6:
        return local_now.date() + timedelta(days=6)
    return target_date


def draw_date_to_code(draw_date: date) -> str:
    return draw_date.strftime("%Y%m%d")


def calculate_draw_round(draw_date: date) -> int:
    if draw_date.weekday() != 5:
        raise ValueError("추첨일은 토요일이어야 합니다.")

    delta_days = (draw_date - BASE_DRAW_DATE).days
    if delta_days % 7 != 0:
        raise ValueError("기준 추첨일과 같은 주 단위 날짜만 지원합니다.")
    return BASE_DRAW_ROUND + (delta_days // 7)


def get_draw_metadata(now=None) -> tuple[date, str, int]:
    draw_date = determine_draw_date(now=now)
    return draw_date, draw_date_to_code(draw_date), calculate_draw_round(draw_date)


def evaluate_ticket(ticket_numbers, winning_numbers, bonus_number=None) -> dict[str, object]:
    normalized_ticket = normalize_lotto_numbers(ticket_numbers)
    normalized_winning = normalize_lotto_numbers(winning_numbers)
    matched_numbers = sorted(set(normalized_ticket) & set(normalized_winning))
    match_count = len(matched_numbers)
    bonus_match = bonus_number in normalized_ticket if bonus_number else False

    if match_count == 6:
        prize_rank = 1
    elif match_count == 5 and bonus_match:
        prize_rank = 2
    elif match_count == 5:
        prize_rank = 3
    elif match_count == 4:
        prize_rank = 4
    elif match_count == 3:
        prize_rank = 5
    else:
        prize_rank = 0

    return {
        "ticket_numbers": normalized_ticket,
        "winning_numbers": normalized_winning,
        "matched_numbers": matched_numbers,
        "match_count": match_count,
        "bonus_match": bonus_match,
        "prize_rank": prize_rank,
    }
