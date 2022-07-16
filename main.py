
from pyparsing import javaStyleComment
from sim_model_bom import callprocess
import json
from io import StringIO


x = callprocess()[0]

j = x.to_json(orient='records')



from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return json.loads(j)



