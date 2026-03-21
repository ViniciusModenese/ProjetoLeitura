from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leitura', '0005_perfil_foto_perfil'),
    ]

    operations = [
        migrations.AddField(
            model_name='livro',
            name='criador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='livros_adicionados', to=settings.AUTH_USER_MODEL),
        ),
    ]
