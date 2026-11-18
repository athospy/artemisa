from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artemisa', '0005_competition_is_demo'),
    ]

    # Only the new fields (same reason as 0005: older model changes still have no
    # migration and are left for a separate, checked one).
    operations = [
        migrations.AddField(
            model_name='competition',
            name='ai_recap',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='competition',
            name='ai_recap_input',
            field=models.TextField(blank=True, default=''),
        ),
    ]
