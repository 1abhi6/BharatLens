from fastapi import FastAPI
from src.api.routers.chat import router

app = FastAPI()

app.include_router(router=router)


if __name__ == "__main__":
    app.run()
