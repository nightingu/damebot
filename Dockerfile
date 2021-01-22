FROM python:3.8.7

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip install -i https://mirrors.bfsu.edu.cn/pypi/web/simple -r requirements.txt

COPY . .

ENV PYTHONPATH "${PYTHONPATH}:/app"

ENTRYPOINT [ "python" ]

CMD [ "main.py" ]
