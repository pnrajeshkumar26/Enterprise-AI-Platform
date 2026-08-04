from app.engines import LlamaEngine

engine = LlamaEngine()

response = engine.generate(
    "Explain FastAPI in one sentence."
)

print(response)