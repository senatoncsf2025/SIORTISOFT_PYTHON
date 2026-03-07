

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0002_registro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registro',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros', to='myApp.usuario'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='cedula',
            field=models.CharField(max_length=20),
        ),
    ]
