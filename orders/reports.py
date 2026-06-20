import calendar
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from orders.models import Order, OrderItem

# Revenue is recognised only on delivered orders (confirmed with stakeholder).

def _revenue(queryset):
    return queryset.aggregate(total=Sum("total"))["total"] or Decimal("0.00")


def get_daily_report(day=None):
    """Totals for a single day (defaults to today, local time)."""
    day = day or timezone.localdate()
    orders = Order.objects.filter(created_at__date=day)
    delivered = orders.filter(status=Order.Status.DELIVERED)
    return {
        "date": day,
        "total_orders": orders.count(),
        "delivered_orders": delivered.count(),
        "revenue": _revenue(delivered),
    }


def get_monthly_report(year=None, month=None):
    """Totals for a calendar month (defaults to the current month)."""
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    orders = Order.objects.filter(created_at__year=year, created_at__month=month)
    delivered = orders.filter(status=Order.Status.DELIVERED)

    top_items = list(
        OrderItem.objects.filter(
            order__created_at__year=year,
            order__created_at__month=month,
            order__status=Order.Status.DELIVERED,
        )
        .annotate(
            item_total=ExpressionWrapper(
                F("price") * F("quantity"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .values("menu_item__name")
        .annotate(
            quantity=Sum("quantity"),
            revenue=Sum("item_total"),
        )
        .order_by("-quantity", "menu_item__name")[:10]
    )

    return {
        "year": year,
        "month": month,
        "month_label": f"{calendar.month_name[month]} {year}",
        "order_count": orders.count(),
        "revenue": _revenue(delivered),
        "top_items": top_items,
    }
