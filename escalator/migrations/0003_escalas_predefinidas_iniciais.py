from django.db import migrations

def criar_escalas_predefinidas(apps, schema_editor):
    EscalaPredefinida = apps.get_model('escalator', 'EscalaPredefinida')
    exemplos = [
        {"nome": "12x36", "descricao": "12h trabalho, 36h descanso", "horas_trabalho": 12, "horas_descanso": 36},
        {"nome": "24x48", "descricao": "24h trabalho, 48h descanso", "horas_trabalho": 24, "horas_descanso": 48},
        {"nome": "5x2", "descricao": "5 dias trabalho, 2 dias descanso", "horas_trabalho": 8, "horas_descanso": 16},
        {"nome": "6x1", "descricao": "6 dias trabalho, 1 dia descanso", "horas_trabalho": 8, "horas_descanso": 16},
        {"nome": "4x2", "descricao": "4 dias trabalho, 2 dias descanso", "horas_trabalho": 8, "horas_descanso": 16},
        {"nome": "6x2", "descricao": "6 dias trabalho, 2 dias descanso", "horas_trabalho": 8, "horas_descanso": 16},
    ]
    for ex in exemplos:
        EscalaPredefinida.objects.get_or_create(**ex)

class Migration(migrations.Migration):
    dependencies = [
        ('escalator', '0002_escalapredefinida'),
    ]
    operations = [
        migrations.RunPython(criar_escalas_predefinidas),
    ] 