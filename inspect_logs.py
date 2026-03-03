import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import NotificationLog

def inspect_logs():
    logs = NotificationLog.objects.all().order_by('-created_at')[:10]
    if not logs:
        print("No notification logs found.")
        return

    print(f"{'ID':<5} | {'User':<15} | {'Status':<10} | {'Message ID':<40} | {'Internal ID'}")
    print("-" * 100)
    for log in logs:
        internal_id = log.data.get('id', 'N/A')
        print(f"{log.id:<5} | {log.user.username:<15} | {log.status:<10} | {str(log.message_id):<40} | {internal_id}")

if __name__ == "__main__":
    inspect_logs()
