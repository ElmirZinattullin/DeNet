from fastapi import FastAPI, File, Path, Request, UploadFile, status
from schemas import Hello


app = FastAPI(
  debug=True
)


@app.get('/hello',
         )
async def hello() -> Hello:

    answer = Hello(name="Hello world!")
    return answer