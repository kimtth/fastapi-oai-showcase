'''
@TODO
https://www.freecodecamp.org/news/how-to-add-jwt-authentication-in-fastapi/
'''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


@app.get("/token/new")
async def getToken():
    pass


@app.get("/token/check")
async def checkToken():
    pass
