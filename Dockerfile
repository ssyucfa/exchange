FROM python:3.9

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /exchange_api/
# Install dependencies:
COPY requirements.txt /exchange_api/
RUN pip install -r requirements.txt

COPY . /exchange_api/
CMD ["bash", "./start.sh"]