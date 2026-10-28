FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ARCHITECTURE.md ./
COPY src ./src
COPY examples ./examples
COPY docker/demo-entrypoint.sh /entrypoint.sh
RUN pip install --no-cache-dir . \
    && chmod +x /entrypoint.sh

ENV PYTHONPATH=/app
ENV UNDOOM_MODEL_PROVIDER=examples.order_lookup.fake:provider
ENV UNDOOM_DEMO_ROOT=/work
VOLUME ["/work"]
ENTRYPOINT ["/entrypoint.sh"]
