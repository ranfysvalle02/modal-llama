import modal
import time

from fastapi import Request
from fastapi.responses import JSONResponse
# Define the Docker image
#docker_image = modal.Image.from_dockerfile("Dockerfile").pip_install("fastapi", "requests", "ollama")
docker_image = modal.Image.debian_slim().apt_install("curl").run_commands(
    "curl -fsSL https://ollama.com/install.sh | sh", 
    "ollama serve &"
).pip_install("fastapi", "requests", "ollama")

# Create a Modal app
app = modal.App("ollama-demo")
volume = modal.Volume.from_name("ollama-models-volume", create_if_missing=True)
# Ollama saves its models in the ~/.ollama/models directory, which contains both model blobs and manifests.

@app.function(
    image=docker_image,
    volumes={"/root/.ollama/models": volume}, 
    gpu="any"
)
@modal.web_endpoint(method="POST")
async def run_ollama_demo(request: dict):
    import subprocess
    import requests

    # Start Ollama server
    ollama_process = subprocess.Popen(["ollama", "serve"])
    
    # Wait for Ollama to start
    for _ in range(30):  # Try for 30 seconds
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                print("Ollama server is ready")
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
    else:
        raise Exception("Ollama server failed to start")
    
    subprocess.run(["ollama", "pull", "llama3.2:3b"])

    import ollama

    q = request.get("q", "Hello, world!")
    # Run a simple query with llama3.2:3b
    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": q
            }
        ],
    )
    print(response['message']['content'])
    """
    Hello! It's nice to meet you. Is there something I can help you with or would you like to chat?
    Embedded text: 'Hello, world!'
    Embedding shape: (768,)
    """
    # Clean up
    ollama_process.terminate()
    ollama_process.wait()
    return JSONResponse(content={"q":q, "ai_response": response['message']['content']})

if __name__ == "__main__":
    with modal.enable_remote_debugging():
        with app.run():
            run_ollama_demo.remote()
