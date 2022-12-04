FROM nginx:stable-alpine

RUN mkdir -p /wwwroot
COPY conf/ /conf

WORKDIR /usr/app/src
COPY main.py ./
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD python ./main.py