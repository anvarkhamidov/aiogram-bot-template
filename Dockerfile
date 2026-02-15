FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

RUN mkdir -p data

EXPOSE ${PORT:-8000}

CMD ["python", "start.py"]
