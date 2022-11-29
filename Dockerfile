# For more information, please refer to https://aka.ms/vscode-docker-python
FROM ubuntu:20.04

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .

RUN apt-get update -y && apt-get install -y libpq-dev python-dev
RUN apt-get install -y python3 pip

RUN pip install -r requirements.txt

WORKDIR /app
COPY . /app

CMD [ "python", "app.py" ]