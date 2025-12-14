ARG DEVICE=cpu

FROM python:3.11-bookworm@sha256:e39286476f84ffedf7c3564b0b74e32c9e1193ec9ca32ee8a11f8c09dbf6aafe AS builder-cpu

FROM builder-cpu AS builder-cuda

FROM builder-${DEVICE} AS builder

ARG DEVICE
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv

RUN apt-get update && apt-get install -y --no-install-recommends g++

COPY --from=ghcr.io/astral-sh/uv:0.8.15@sha256:a5727064a0de127bdb7c9d3c1383f3a9ac307d9f2d8a391edc7896c54289ced0 /uv /uvx /bin/
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --extra ${DEVICE} --no-dev --no-editable --no-install-project --compile-bytecode --no-progress --active --link-mode copy

FROM python:3.11-slim-bookworm@sha256:2c5bc243b1cc47985ee4fb768bb0bbd4490481c5d0897a62da31b7f30b7304a7 AS prod-cpu

ENV LD_PRELOAD=/usr/lib/libmimalloc.so.2 \
    MACHINE_LEARNING_MODEL_ARENA=false

FROM docker.io/nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS prod-cuda

ENV LD_PRELOAD=/usr/lib/libmimalloc.so.2 \
    MACHINE_LEARNING_MODEL_ARENA=false

COPY --from=builder-cuda /usr/local/bin/python3 /usr/local/bin/python3
COPY --from=builder-cuda /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder-cuda /usr/local/lib/libpython3.11.so /usr/local/lib/libpython3.11.so

FROM prod-${DEVICE} AS prod

ARG DEVICE

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini ccache libgl1 libglib2.0-0 libgomp1 $(if ! [ "$DEVICE" = "openvino" ] && ! [ "$DEVICE" = "rocm" ]; then echo "libmimalloc2.0"; fi) && \
    apt-get autoremove -yqq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s "/usr/lib/$(arch)-linux-gnu/libmimalloc.so.2" /usr/lib/libmimalloc.so.2

WORKDIR /usr/src
ENV TRANSFORMERS_CACHE=/cache \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/usr/src \
    DEVICE=${DEVICE} \
    VIRTUAL_ENV=/opt/venv \
    MACHINE_LEARNING_CACHE_FOLDER=/cache

# prevent core dumps
RUN echo "hard core 0" >> /etc/security/limits.conf && \
    echo "fs.suid_dumpable 0" >> /etc/sysctl.conf && \
    echo 'ulimit -S -c 0 > /dev/null 2>&1' >> /etc/profile

COPY --from=builder /opt/venv /opt/venv
COPY scripts/healthcheck.py .
COPY immich_ml immich_ml

ARG BUILD_ID
ARG BUILD_IMAGE
ARG BUILD_SOURCE_REF
ARG BUILD_SOURCE_COMMIT

ENV IMMICH_BUILD=${BUILD_ID}
ENV IMMICH_BUILD_URL=https://github.com/immich-app/immich/actions/runs/${BUILD_ID}
ENV IMMICH_BUILD_IMAGE=${BUILD_IMAGE}
ENV IMMICH_BUILD_IMAGE_URL=https://github.com/immich-app/immich/pkgs/container/immich-machine-learning
ENV IMMICH_REPOSITORY=immich-app/immich
ENV IMMICH_REPOSITORY_URL=https://github.com/immich-app/immich
ENV IMMICH_SOURCE_REF=${BUILD_SOURCE_REF}
ENV IMMICH_SOURCE_COMMIT=${BUILD_SOURCE_COMMIT}
ENV IMMICH_SOURCE_URL=https://github.com/immich-app/immich/commit/${BUILD_SOURCE_COMMIT}

ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "immich_ml"]

HEALTHCHECK CMD python3 healthcheck.py
