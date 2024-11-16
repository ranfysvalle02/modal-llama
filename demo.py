import modal
import time
import subprocess
import requests

# Define the Docker image
docker_image = modal.Image.from_dockerfile("Dockerfile").pip_install("ollama", "langchain_ollama", "numpy")

# Create a Modal app
app = modal.App("ollama-demo")
volume = modal.Volume.from_name("ollama-models-volume", create_if_missing=True)
# Ollama saves its models in the ~/.ollama/models directory, which contains both model blobs and manifests.
@app.function(
    image=docker_image,
    volumes={"/root/.ollama/models": volume}, 
    gpu="any",
)
def run_ollama_demo():
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

    # Pull models if not already present
    subprocess.run(["ollama", "pull", "nomic-embed-text"])
    subprocess.run(["ollama", "pull", "llama3.2:3b"])

    from langchain_ollama import OllamaEmbeddings
    import numpy as np
    import ollama

    # Initialize OllamaEmbeddings
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
    )

    # Embed a sample text
    text = "Hello, world!"
    embedding = embeddings.embed_query(text)

    # Run a simple query with llama3.2:3b
    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": "Hello, world!"
            }
        ],
    )
    print(response['message']['content'])
    print(f"Embedded text: '{text}'")
    print(f"Embedding shape: {np.array(embedding).shape}")

    """
    Hello! It's nice to meet you. Is there something I can help you with or would you like to chat?
    Embedded text: 'Hello, world!'
    Embedding shape: (768,)
    """
    # Clean up
    ollama_process.terminate()
    ollama_process.wait()

if __name__ == "__main__":
    with modal.enable_remote_debugging():
        with app.run():
            run_ollama_demo.remote()
