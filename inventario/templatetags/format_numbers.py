from django import template
from decimal import Decimal, InvalidOperation
import re
from decimal import ROUND_HALF_UP

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
    """Format money for display in CLP: no decimals and dot as thousands separator."""
    if value is None:
        return ''
    # Round to 0 decimals
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        try:
            d = Decimal(str(value))
        except Exception:
            return str(value)
    rounded = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    # Return plain integer string without thousands separators
    return str(int(rounded))


@register.filter
def strip_decimals_in_text(value):
    """Find numbers with decimal part in a string and round them to 0 decimals.

    Examples:
    - 'Total: 123.45 CLP' -> 'Total: 123 CLP'
    - '1.0 items' -> '1 items'
    Non-numeric text is left intact.
    """
    if value is None:
        return ''
    s = str(value)

    # 1) Handle numbers that already use dots as thousands separators, e.g. 1.234 or 12.345.678
    def _grouped_repl(match):
        num = match.group(0)
        try:
            # remove dots then return plain integer string
            n = int(num.replace('.', ''))
            return str(n)
        except Exception:
            return num

    result = re.sub(r"\b\d{1,3}(?:\.\d{3})+\b", _grouped_repl, s)

    # 2) Handle decimal numbers like 1234.56 -> round to integer and group
    # Only match decimal numbers with 1-2 fractional digits to avoid
    # misinterpreting grouped thousands like '15.000' (which has 3-digit groups).
    def _decimal_repl(match):
        num = match.group(0)
        try:
            d = Decimal(num)
            rounded = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return str(int(rounded))
        except Exception:
            return num

    result = re.sub(r"\b\d+\.\d{1,2}\b", _decimal_repl, result)

    # 3) Handle plain integers (no dots) -> add grouping
    def _int_repl(match):
        num = match.group(0)
        try:
            return str(int(num))
        except Exception:
            return num

    result = re.sub(r"\b\d+\b", _int_repl, result)
    return result
