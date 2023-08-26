from fastapi import FastAPI

import account
import controller
import note

app = FastAPI()
app.include_router(account.router, prefix="/account")


@app.on_event("startup")
async def startup():
    await controller.on_start()
    await note.prepare_dir()


@app.on_event("shutdown")
async def shutdown():
    await controller.on_stop()
