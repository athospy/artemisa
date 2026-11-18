from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artemisa', '0004_archer_club_name'),
    ]

    # Only the new field. models.py also has older changes with no migration yet
    # (unique constraints, an index, validators); those are left for a separate,
    # checked migration because a unique constraint can fail on existing data.
    operations = [
        migrations.AddField(
            model_name='competition',
            name='is_demo',
            field=models.BooleanField(default=False),
        ),
    ]
