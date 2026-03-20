from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('call', '0014_message_is_delivered_messagereaction'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE call_gameinvite ADD COLUMN IF NOT EXISTS game_type VARCHAR(20) DEFAULT 'chess';",
            reverse_sql="ALTER TABLE call_gameinvite DROP COLUMN IF EXISTS game_type;"
        ),
        migrations.RunSQL(
            sql="ALTER TABLE call_gameinvite ADD COLUMN IF NOT EXISTS board_id INTEGER;",
            reverse_sql="ALTER TABLE call_gameinvite DROP COLUMN IF EXISTS board_id;"
        ),
        # Add a dummy operation for GameMove if needed, but usually it doesn't have missing columns
        migrations.RunSQL(
            sql="ALTER TABLE call_gamemove ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;",
            reverse_sql="ALTER TABLE call_gamemove DROP COLUMN IF EXISTS timestamp;"
        ),
    ]
