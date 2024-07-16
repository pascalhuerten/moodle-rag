import uvicorn
from fastapi import FastAPI
from src.routes.main_router import router as main_router
from src.setup import load_embedding_function, load_vectorstore
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize app
app = FastAPI()

# Store resources in app's state so they can be accessed in views
app.state.EMBEDDINGFUNTION = load_embedding_function()

def update_vectorstore():
    app.state.VECTORSTORE = load_vectorstore(app.state.EMBEDDINGFUNTION)

update_vectorstore()
scheduler = BackgroundScheduler()
scheduler.add_job(update_vectorstore, 'interval', days=1)

# Register routes
app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    scheduler = BackgroundScheduler()

    from apscheduler.schedulers.background import BackgroundScheduler
    from fastapi import FastAPI
    from scrape_moodle import scrape_moodle_data
    
    app = FastAPI()
    
    def run_job():
        print("Running job: Scrape moodle data")
        scrape_moodle_data()
        print("Job done")
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_job, 'interval', days=1)
    scheduler.start()