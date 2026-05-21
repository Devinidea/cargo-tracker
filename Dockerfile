FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db_schema.py /app/
COPY static /app/static

RUN mkdir -p /data

EXPOSE 5180

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["gunicorn", "--bind", "0.0.0.0:5180", "--workers", "2", "--timeout", "120", "app:app"]
