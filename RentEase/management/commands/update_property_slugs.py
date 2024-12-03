from django.core.management.base import BaseCommand
from RentEase.models import Property
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Updates slugs for all properties'

    def handle(self, *args, **options):
        properties = Property.objects.all()
        updated_count = 0

        for property in properties:
            if not property.slug:
                base_slug = slugify(property.title)
                slug = base_slug
                counter = 1
                
                while Property.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                property.slug = slug
                property.save()
                updated_count += 1
                self.stdout.write(f"Updated slug for property '{property.title}' to '{slug}'")

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} properties'))
