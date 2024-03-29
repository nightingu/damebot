FROM python:3.8.7

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip install --extra-index-url https://mirrors.bfsu.edu.cn/pypi/web/simple -r requirements.txt

COPY . .

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH "/app"

CMD [ "python", "main.py" ]
