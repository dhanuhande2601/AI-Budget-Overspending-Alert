from app import app
from scheduler.job import start_scheduler

start_scheduler(app)

if __name__ == "__main__":
    app.run()
