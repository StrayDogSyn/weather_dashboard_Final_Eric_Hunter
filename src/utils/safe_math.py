"""Safe mathematical operations to prevent runtime errors."""

import logging
from typing import Union

logger = logging.getLogger(__name__)


def safe_divide(
    numerator: Union[int, float, None],
    denominator: Union[int, float, None],
    fallback: Union[int, float] = 0,
) -> Union[int, float]:
    """
    Safely divide two numbers, handling None values and zero division.

    Args:
        numerator: The number to be divided
        denominator: The number to divide by
        fallback: Value to return if division fails (default: 0)

    Returns:
        Result of division or fallback value
    """
    try:
        if numerator is None or denominator in (None, 0):
            logger.debug(f"Division failed: numerator={numerator}, denominator={denominator}")
            return fallback
        return numerator / denominator
    except (TypeError, ZeroDivisionError) as e:
        logger.warning(f"Division failed with error: {e}")
        return fallback


def safe_percentage(
    value: Union[int, float, None], total: Union[int, float, None], fallback: Union[int, float] = 0
) -> Union[int, float]:
    """
    Safely calculate percentage, handling None values and zero division.

    Args:
        value: The value to calculate percentage for
        total: The total value
        fallback: Value to return if calculation fails (default: 0)

    Returns:
        Percentage value or fallback
    """
    return safe_divide(value, total, fallback) * 100


def safe_average(values: list, fallback: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely calculate average of a list, handling empty lists and None values.

    Args:
        values: List of numbers to average
        fallback: Value to return if calculation fails (default: 0)

    Returns:
        Average value or fallback
    """
    if not values:
        return fallback

    # Filter out None values
    valid_values = [v for v in values if v is not None]

    if not valid_values:
        return fallback

    return safe_divide(sum(valid_values), len(valid_values), fallback)
