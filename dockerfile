FROM python:latest-alpine

WORKDIR /usr/app/src
COPY main.py ./
COPY grams.pkl ./
COPY mp3List.py ./

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt


#CMD [ "python", "./main.py" ]
CMD python ./main.py