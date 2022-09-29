FROM python:3
LABEL maintainer sturm@uni-trier.de
RUN apt-get update && apt-get install -y
WORKDIR auth
RUN pip install --upgrade pip
COPY requirements.txt ./
COPY *.py ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 4344
CMD [ "python", "netatmo_oauth.py", "--file", "/coreef/keys/netatmo.json", "--path", "/coreef/keys/netatmo_token.json" ]

