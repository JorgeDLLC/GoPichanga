from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from applications.users.models import User, UserRole
from applications.field.models import Field, Equipment, FieldEquipment
from applications.booking.factories import BookingFactory, ExtraRequest
from applications.booking.exceptions import SlotNotAvailable, ExtraOutOfStock
from applications.booking.models import BookingStatus

class BookingFactoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(nombre="Reg", email="r@e.com", password="x", rol=UserRole.REGULAR)
        self.field = Field.objects.create(
            owner=self.user, name="Cancha 1", type="futbol",
            address="X", price_hour=50, has_lights=False
        )
        eq = Equipment.objects.create(type='chalecos')
        self.fe = FieldEquipment.objects.create(field=self.field, equipment=eq, stock=10, price_per_unit=3)

    def test_create_ok(self):
        start = timezone.now() + timedelta(hours=1)
        end   = start + timedelta(hours=2)
        booking = BookingFactory.create(
            user=self.user,
            field=self.field,
            start=start, end=end,
            extras=[ExtraRequest(fe_id=self.fe.id, quantity=5)],
        )
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.extras.first().quantity, 5)

    def test_fail_out_of_stock(self):
        start = timezone.now() + timedelta(hours=1)
        end   = start + timedelta(hours=2)
        with self.assertRaises(ExtraOutOfStock):
            BookingFactory.create(
                user=self.user,
                field=self.field,
                start=start, end=end,
                extras=[ExtraRequest(fe_id=self.fe.id, quantity=15)],
            )
