FROM python:3.8-slim

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT [ "python3" ]

CMD [ "main.py" ]
