FROM ubuntu:20.04

LABEL maintainer_name="Yang-Xijie"
LABEL maintainer_email="564197835@qq.com"

WORKDIR /app

COPY . .

RUN sed -i 's/archive.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && apt-get update && apt-get install -y \
        yosys iverilog \
        python3 python3-pip \
    && pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
