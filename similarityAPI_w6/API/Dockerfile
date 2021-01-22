FROM python:latest

WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install ./en_core_web_sm-2.3.1.tar.gz
CMD ["python","app.py"]