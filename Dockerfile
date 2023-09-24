FROM python:3.10

WORKDIR /app
COPY requirements.txt bot.py .

RUN apt update && apt install -y ffmpeg
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["bot.py"]
