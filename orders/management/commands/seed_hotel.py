import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from rooms.models import Room
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Seeds the database with rooms, menu items matching the design, and mock orders."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding categories and menu items...")

        # Categories
        cat_main, _ = Category.objects.get_or_create(name="Main Course")
        cat_breakfast, _ = Category.objects.get_or_create(name="Breakfast")
        cat_drinks, _ = Category.objects.get_or_create(name="Drinks")
        cat_desserts, _ = Category.objects.get_or_create(name="Desserts")
        cat_room_service, _ = Category.objects.get_or_create(name="Room Service")

        # Menu Items
        menu_items_data = [
            # Main Course
            {
                "name": "Signature Doro Wat",
                "description": "Slow-simmered chicken in berbere sauce, served with injera.",
                "price": Decimal("380.00"),
                "category": cat_main,
            },
            {
                "name": "Kitfo Special",
                "description": "Hand-minced beef, mitmita & spiced butter.",
                "price": Decimal("420.00"),
                "category": cat_main,
            },
            {
                "name": "Grilled Tilapia",
                "description": "Lake-fresh tilapia with lemon, herbs and rice.",
                "price": Decimal("460.00"),
                "category": cat_main,
            },
            # Breakfast
            {
                "name": "Full Ethiopian Breakfast",
                "description": "Ful, scrambled eggs, fresh bread & spiced tea.",
                "price": Decimal("260.00"),
                "category": cat_breakfast,
            },
            {
                "name": "Avocado & Mango Bowl",
                "description": "Layered tropical fruit with honey drizzle.",
                "price": Decimal("180.00"),
                "category": cat_breakfast,
            },
            # Drinks
            {
                "name": "Macchiato Classico",
                "description": "Single-origin Yirgacheffe, perfectly steamed milk.",
                "price": Decimal("90.00"),
                "category": cat_drinks,
            },
            {
                "name": "Fresh Spris Juice",
                "description": "Layered avocado, mango, papaya & guava.",
                "price": Decimal("140.00"),
                "category": cat_drinks,
            },
            {
                "name": "Honey Wine (Tej)",
                "description": "Traditional Ethiopian honey wine, chilled.",
                "price": Decimal("220.00"),
                "category": cat_drinks,
            },
            # Desserts
            {
                "name": "Baklava Trio",
                "description": "Pistachio, walnut & almond with rose syrup.",
                "price": Decimal("190.00"),
                "category": cat_desserts,
            },
            {
                "name": "Dark Chocolate Lava",
                "description": "Warm molten cake with vanilla bean ice cream.",
                "price": Decimal("210.00"),
                "category": cat_desserts,
            },
            # Room Service Specials
            {
                "name": "Late-Night Club Sandwich",
                "description": "Triple-stack chicken, bacon, egg & fries.",
                "price": Decimal("300.00"),
                "category": cat_room_service,
            },
            {
                "name": "Wellness Platter",
                "description": "Hummus, olives, crudités & warm pita.",
                "price": Decimal("240.00"),
                "category": cat_room_service,
            },
        ]

        menu_items = {}
        for item in menu_items_data:
            obj, created = MenuItem.objects.update_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "price": item["price"],
                    "category": item["category"],
                    "available": True,
                }
            )
            menu_items[item["name"]] = obj

        self.stdout.write("Seeding rooms...")
        rooms_data = [
            {"room_number": "101", "token": "0JamzVAqNDuP2yNnokh4FQ"},
            {"room_number": "102", "token": "r102tokenxyzabc1234567"},
            {"room_number": "201", "token": "r201tokenxyzabc1234567"},
            {"room_number": "202", "token": "r202tokenxyzabc1234567"},
            {"room_number": "305", "token": "r305tokenxyzabc1234567"},
            {"room_number": "404", "token": "r404tokenxyzabc1234567"},
        ]

        rooms = {}
        for r_data in rooms_data:
            room_obj, created = Room.objects.update_or_create(
                room_number=r_data["room_number"],
                defaults={
                    "unique_token": r_data["token"],
                    "is_active": True,
                }
            )
            rooms[r_data["room_number"]] = room_obj

        self.stdout.write("Clearing existing mock orders to prevent duplication...")
        Order.objects.all().delete()

        self.stdout.write("Seeding mock orders...")

        # Order 1: Pending (Room 101)
        o1 = Order.objects.create(room=rooms["101"], status=Order.Status.PENDING)
        o1_item1 = OrderItem.objects.create(order=o1, menu_item=menu_items["Signature Doro Wat"], quantity=1, price=menu_items["Signature Doro Wat"].price)
        o1_item2 = OrderItem.objects.create(order=o1, menu_item=menu_items["Fresh Spris Juice"], quantity=2, price=menu_items["Fresh Spris Juice"].price)
        o1.total = o1_item1.line_total + o1_item2.line_total
        o1.save()

        # Order 2: Cooking (Room 102)
        o2 = Order.objects.create(room=rooms["102"], status=Order.Status.COOKING)
        o2_item1 = OrderItem.objects.create(order=o2, menu_item=menu_items["Kitfo Special"], quantity=1, price=menu_items["Kitfo Special"].price)
        o2_item2 = OrderItem.objects.create(order=o2, menu_item=menu_items["Honey Wine (Tej)"], quantity=1, price=menu_items["Honey Wine (Tej)"].price)
        o2.total = o2_item1.line_total + o2_item2.line_total
        o2.save()

        # Order 3: Ready (Room 201)
        o3 = Order.objects.create(room=rooms["201"], status=Order.Status.READY)
        o3_item1 = OrderItem.objects.create(order=o3, menu_item=menu_items["Full Ethiopian Breakfast"], quantity=2, price=menu_items["Full Ethiopian Breakfast"].price)
        o3_item2 = OrderItem.objects.create(order=o3, menu_item=menu_items["Macchiato Classico"], quantity=2, price=menu_items["Macchiato Classico"].price)
        o3.total = o3_item1.line_total + o3_item2.line_total
        o3.save()

        # Order 4: Delivered (Room 202)
        o4 = Order.objects.create(room=rooms["202"], status=Order.Status.DELIVERED)
        o4_item1 = OrderItem.objects.create(order=o4, menu_item=menu_items["Late-Night Club Sandwich"], quantity=1, price=menu_items["Late-Night Club Sandwich"].price)
        o4_item2 = OrderItem.objects.create(order=o4, menu_item=menu_items["Dark Chocolate Lava"], quantity=1, price=menu_items["Dark Chocolate Lava"].price)
        o4.total = o4_item1.line_total + o4_item2.line_total
        o4.save()

        # Order 5: Pending (Room 305)
        o5 = Order.objects.create(room=rooms["305"], status=Order.Status.PENDING)
        o5_item1 = OrderItem.objects.create(order=o5, menu_item=menu_items["Grilled Tilapia"], quantity=1, price=menu_items["Grilled Tilapia"].price)
        o5_item2 = OrderItem.objects.create(order=o5, menu_item=menu_items["Wellness Platter"], quantity=1, price=menu_items["Wellness Platter"].price)
        o5.total = o5_item1.line_total + o5_item2.line_total
        o5.save()

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with test data!"))
