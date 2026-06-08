from apscheduler.schedulers.background import BackgroundScheduler

from services.backup_service import backup_expenses, backup_users

_scheduler = None


def start_scheduler(app):
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler()

    def run_with_app_context(task):
        with app.app_context():
            task()

    scheduler.add_job(
        func=lambda: run_with_app_context(backup_users),
        trigger='cron',
        hour=2,
        minute=0
    )

    scheduler.add_job(
        func=lambda: run_with_app_context(backup_expenses),
        trigger='cron',
        hour=2,
        minute=5
    )

    scheduler.start()
    _scheduler = scheduler

    print('Scheduler started: auto backup enabled')
    return scheduler
