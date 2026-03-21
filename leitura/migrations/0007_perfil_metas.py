from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leitura', '0006_livro_criador'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='meta_livros_ano',
            field=models.PositiveIntegerField(default=12),
        ),
        migrations.AddField(
            model_name='perfil',
            name='meta_resenhas',
            field=models.PositiveIntegerField(default=50),
        ),
    ]
