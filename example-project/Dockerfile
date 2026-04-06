# Example Dockerfile with governance issues
FROM python:3.12

# No USER directive — runs as root (D4)
# Secret in ENV (D4)
ENV OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901

COPY . /app
WORKDIR /app

RUN pip install openai

CMD ["python", "agent.py"]
