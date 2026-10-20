"""Полезные функции."""


def installment_schedule(amount: int, months: int) -> list[int]:
    """Строит график рассрочки.

    Сумма к оплате делится на срок в копейках. Сумма всех платежей графика
    ровно равна сумме к оплате; лишние копейки распределяются по одной
    в первые платежи.

    Args:
        amount: Сумма к оплате в копейках.
        months: Срок рассрочки в месяцах.

    Returns:
        Список платежей в копейках, сумма которых ровно равна ``amount``.

    Raises:
        ValueError: Если ``months`` не положительное или ``amount`` отрицательное.

    Examples:
        >>> installment_schedule(1990000, 3)
        [663334, 663333, 663333]
    """
    if months <= 0:
        msg = "months must be positive"
        raise ValueError(msg)
    if amount < 0:
        msg_0 = "amount must be non-negative"
        raise ValueError(msg_0)

    base, extra = divmod(amount, months)
    # extra первых платежей получают на 1 копейку больше
    return [base + 1] * extra + [base] * (months - extra)
