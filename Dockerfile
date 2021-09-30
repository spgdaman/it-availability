FROM python:3.7

EXPOSE 8891

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD streamlit run --server.port 8889 app.py