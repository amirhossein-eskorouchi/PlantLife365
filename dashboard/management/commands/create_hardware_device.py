from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from dashboard.models import HardwareDevice


class Command(BaseCommand):
    help = "Create or ensure a HardwareDevice exists (id, pin, optional owner)."

    def add_arguments(self, parser):
        parser.add_argument('--device-id', required=True, help='Device ID to create/ensure')
        parser.add_argument('--secret-pin', required=True, help='Secret PIN for the device')
        parser.add_argument('--name', default='', help='Optional name for the device')
        parser.add_argument('--owner', help='Optional username to claim the device')
        parser.add_argument('--activate', action='store_true', help='Set is_active to True')

    def handle(self, *args, **options):
        device_id = options['device_id']
        secret_pin = options['secret_pin']
        name = options.get('name') or ''
        owner_username = options.get('owner')
        activate = options.get('activate')

        User = get_user_model()
        owner = None
        if owner_username:
            try:
                owner = User.objects.get(username=owner_username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{owner_username}' not found. Continuing without owner."))

        device, created = HardwareDevice.objects.get_or_create(
            device_id=device_id,
            defaults={
                'secret_pin': secret_pin,
                'name': name,
                'owner': owner,
                'is_active': True if activate else True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created HardwareDevice '{device_id}' (id={device.id})."))
        else:
            changed = False
            if device.secret_pin != secret_pin:
                device.secret_pin = secret_pin
                changed = True
            if name and device.name != name:
                device.name = name
                changed = True
            if owner and device.owner != owner:
                device.owner = owner
                changed = True
            if activate and not device.is_active:
                device.is_active = True
                changed = True
            if changed:
                device.save()
                self.stdout.write(self.style.SUCCESS(f"Updated existing HardwareDevice '{device_id}'."))
            else:
                self.stdout.write(self.style.SUCCESS(f"HardwareDevice '{device_id}' already exists; no changes made."))

        self.stdout.write(f"device_id={device.device_id} is_active={device.is_active} owner={device.owner}")
