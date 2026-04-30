import logging

from app.main import app


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
