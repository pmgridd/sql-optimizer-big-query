FROM python:3.11-slim

WORKDIR /app

COPY ./Pipfile /app/Pipfile
RUN pip install --no-cache-dir pipenv  \
    && pipenv install \
    && pipenv requirements > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY ./src /app/src

ENTRYPOINT ["python", "-m", "src.lgraph.main_dynamic"]
# ENTRYPOINT ["python", "-m", "src.lgraph.main"]
