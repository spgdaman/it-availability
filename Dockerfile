FROM python:3.7

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 8891

COPY . .

CMD streamlit run --server.port 8891 app.py