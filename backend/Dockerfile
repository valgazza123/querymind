FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system querymind && adduser --system --ingroup querymind querymind
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN chown -R querymind:querymind /app
USER querymind

EXPOSE 8000
CMD ["gunicorn", "querymind_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4"]
