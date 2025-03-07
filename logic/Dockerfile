FROM python:3.10
WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /usr/local/app/

RUN useradd app
USER app

CMD ["python3", "main.py"]