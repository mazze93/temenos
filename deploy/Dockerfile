# Temenos — evidence-gated runtime. Build from a checkout that has pulled the
# vendored submodules:  git clone --recurse-submodules <repo>
FROM python:3.12-slim

# Non-root, no shell history, minimal surface.
RUN useradd --create-home --uid 10001 temenos
WORKDIR /app

# Layer the package and its vendored gate tools; install without build cache.
COPY pyproject.toml README.md LICENSE ./
COPY temenos/ ./temenos/
COPY policy/ ./policy/
COPY vendor/ ./vendor/

# Install the vendored gate tools as packages first (they outlive the
# editable/`vendor/` layout in a container), then temenos itself.
RUN pip install --no-cache-dir ./vendor/aletheia ./vendor/apatea . && \
    chown -R temenos:temenos /app

USER temenos
EXPOSE 8788

ENTRYPOINT ["temenos"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8788"]