FROM ubuntu:20.04

LABEL maintainer_name="Yang-Xijie"
LABEL maintainer_email="564197835@qq.com"

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    yosys \
    python3 python3-pip \
    nodejs npm && \ 
    pip install --no-cache-dir --upgrade -r requirements.txt \ 
    npm install --global netlistsvg

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
