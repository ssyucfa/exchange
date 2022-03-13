FROM python:3.9-slim as compiler
ENV PYTHONUNBUFFERED 1

WORKDIR /exchange_api/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /exchange_api/requirements.txt
RUN pip install -Ur requirements.txt

FROM python:3.9-slim as runner
WORKDIR /exchange_api/
COPY --from=compiler /opt/venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"
RUN export CONFIGPATH="/exchange_api/config.yml"
COPY . /exchange_api/
