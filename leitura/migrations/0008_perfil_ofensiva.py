from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leitura', '0007_perfil_metas'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='ofensiva_atual',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='perfil',
            name='ultimo_acesso_ofensiva',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
