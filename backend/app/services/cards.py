from datetime import date
from typing import Any, Dict, Optional, Tuple


def _today() -> date:
    return date.today()


def get_best_card(cursor, member_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    ???????????
    - ?????? > 0 ????
    - ????????????
    ?? (card_row, card_type)???????? (None, None)
    """
    if not member_id:
        return None, None

    try:
        cursor.execute(
            """
            SELECT *
            FROM member_cards
            WHERE member_id = %s
              AND start_date <= CURDATE()
              AND end_date >= CURDATE()
            """,
            (member_id,),
        )
        cards = cursor.fetchall() or []
    except Exception:
        return None, None

    best_times_card = None
    best_discount_card = None
    best_discount_value = None

    for c in cards:
        # ?? dict/tuple
        def get_val(obj, key):
            return obj.get(key) if isinstance(obj, dict) else None

        remaining = get_val(c, "remaining_times")
        discount = get_val(c, "discount")

        # ???????????
        if remaining is not None and remaining > 0:
            best_times_card = c
            break

        # ??????????
        try:
            d_val = float(discount or 100)
        except Exception:
            d_val = 100.0
        if best_discount_value is None or d_val < best_discount_value:
            best_discount_value = d_val
            best_discount_card = c

    if best_times_card:
        return best_times_card, (best_times_card.get("card_type") if isinstance(best_times_card, dict) else None)

    if best_discount_card:
        return best_discount_card, (best_discount_card.get("card_type") if isinstance(best_discount_card, dict) else None)

    return None, None


def consume_card_times(cursor, card: Dict[str, Any]) -> bool:
    """
    ????????????? True
    """
    if not card:
        return False
    card_id = card.get("id") if isinstance(card, dict) else None
    remaining = card.get("remaining_times") if isinstance(card, dict) else None
    if card_id is None or remaining is None:
        return False
    try:
        remaining_val = int(remaining)
        if remaining_val <= 0:
            return False
        cursor.execute(
            "UPDATE member_cards SET remaining_times = %s WHERE id = %s",
            (remaining_val - 1, card_id),
        )
        return True
    except Exception:
        return False
