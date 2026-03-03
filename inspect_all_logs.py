import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import NotificationLog

def inspect_all_logs():
    logs = NotificationLog.objects.all().order_by('-created_at')[:20]
    if not logs:
        print("No notification logs found.")
        return

    print(f"{'ID':<5} | {'User':<15} | {'Status':<10} | {'Type':<15} | {'Message'}")
    print("-" * 100)
    for log in logs:
        notif_type = log.data.get('type', 'N/A')
        print(f"{log.id:<5} | {log.user.username:<15} | {log.status:<10} | {notif_type:<15} | {log.body[:30]}")

if __name__ == "__main__":
    inspect_all_logs()
