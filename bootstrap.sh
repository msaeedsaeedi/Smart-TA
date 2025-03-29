docker run -it --rm \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/submissions:/app/submissions" \
  smart-ta