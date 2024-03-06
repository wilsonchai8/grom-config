FROM python:3.8

RUN mkdir /opt/grom-config
WORKDIR /opt/grom-config
ADD requirements.txt /opt/grom-config/
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
ADD startup.py app.conf /opt/grom-config/
ADD src /opt/grom-config/src
CMD python3 startup.py -c app.conf
