from botasaurus_server.server import Server
from botasaurus_server import task_routes
from botasaurus_server.task_routes import OK_MESSAGE
from bottle import run, get
import backend.scrapers


@get("/health")
def get_api():
    return OK_MESSAGE


if __name__ == "__main__":
    print("Running backend...")
    task_routes.executor.load()
    task_routes.executor.start()

    if not Server.get_scrapers_names():
        raise RuntimeError("No scrapers found. Please add a scraper using Server.add_scraper.")

    host = '0.0.0.0'
    debug = False
    run(
        host=host,
        port=8080,
        debug=debug
    )

