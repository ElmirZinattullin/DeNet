FROM python:3.11

ENV PYTHONBUFFERED = 1


COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY /api_app /src/api_app
COPY /db /src/db
COPY services /src/services
COPY settings.py /src/settings.py

#ENV DATABASE twitter-clone_db
#ENV DATABASE_USER twitter-clone
#ENV DATABASE_PASSWORD secret
#ENV DATABASE_PORT 5432
#ENV DEBUG 0
#ENV API_ROUTE /api

#CMD ["python", "src/settings.py"]

ENTRYPOINT ["uvicorn", "src.api_app.app:app", "--host", "0.0.0.0", "--port", "8000"]

#/static/images/2#
