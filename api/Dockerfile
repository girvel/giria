FROM python:3.10
WORKDIR /usr/local/app

COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./* /usr/local/app
CMD ["fastapi", "run", "main.py", "--port", "80"]