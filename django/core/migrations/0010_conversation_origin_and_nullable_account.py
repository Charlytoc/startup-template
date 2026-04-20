import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_conversation_message_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='origin',
            field=models.CharField(
                choices=[('integration', 'Integration'), ('web', 'Web chat')],
                default='integration',
                help_text="Where this conversation happens (an external integration vs. the in-app web chat).",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='integration_account',
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    'Channel this conversation lives on (Telegram bot, Instagram account, ...). '
                    'Null for web-chat conversations.'
                ),
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations',
                to='core.integrationaccount',
            ),
        ),
    ]
