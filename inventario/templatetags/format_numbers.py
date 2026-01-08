from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def format_decimal(value, decimals=3):
    """Format a numeric value:
    - Quantize to `decimals` decimal places
    - Remove trailing zeros and decimal point when not needed
    - Returns empty string for None
    """
    if value is None:
        return ''
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        try:
            d = Decimal(str(value))
        except Exception:
            return str(value)

    # Build quantization unit like '0.001' for decimals=3
    if int(decimals) > 0:
        quant = Decimal('0.' + '0' * (int(decimals) - 1) + '1')
    else:
        quant = Decimal('1')

    try:
        q = d.quantize(quant)
    except (InvalidOperation, ValueError):
        q = d

    # Normalize to remove trailing zeros and avoid scientific notation
    normalized = q.normalize()
    # Use 'f' format to ensure non-scientific string
    s = format(normalized, 'f')
    return s

@register.filter
def format_money(value):
    """Format money with 2 decimals, but trim if .00"""
    return format_decimal(value, 2)
