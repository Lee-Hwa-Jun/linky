from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('links', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='click_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
