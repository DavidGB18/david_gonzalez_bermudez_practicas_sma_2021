FROM python:3.9

ENV TZ=Europe/Madrid
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY . /SistemasMultiagentes

WORKDIR /SistemasMultiagentes

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./chatbot.py" ]