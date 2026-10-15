FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PUID=0
ENV PGID=0
ENV EXEC_TOOL=gosu
ENV SIWAN_HOST=0.0.0.0
ENV SIWAN_PORT=8080
ENV SIWAN_AUTH_TYPE=none
ENV SIWAN_USERNAME=admin
ENV SIWAN_PASSWORD=

ENV APP_PATH=/app
ENV SIWAN_PATH=/data

RUN mkdir -p ${APP_PATH}
RUN mkdir -p ${SIWAN_PATH}

RUN apt update && apt install -y \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_PATH}

COPY LICENSE pyproject.toml .python-version uv.lock* ./

ENV UV_NO_MANAGED_PYTHON=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --compile-bytecode --no-dev

COPY server ./server
COPY client/dist ./client/dist

COPY entrypoint.sh healthcheck.sh /
RUN chmod +x /entrypoint.sh /healthcheck.sh

VOLUME /data
EXPOSE 8080/tcp
HEALTHCHECK --interval=60s --timeout=10s CMD /healthcheck.sh

ENTRYPOINT [ "/entrypoint.sh" ]
