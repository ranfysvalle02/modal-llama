# modal-ollama

---

Integrating Ollama's serverless platform with Modal can streamline the deployment and scaling of AI and machine learning applications. Here's a step-by-step guide to setting up and running your application:

**1. Understanding Modal:**

Modal is a serverless cloud platform designed to simplify the deployment and scaling of applications in AI, machine learning, and data processing. By abstracting away the complexities of infrastructure management, Modal enables developers to focus on writing code without the need to handle servers, containers, or scaling logistics.

**2. Modal's Container Runtime:**

Modal utilizes a custom container runtime that allows developers to define the exact environment their code must run within. This flexibility is crucial for applications requiring specific system packages, Python libraries, or other dependencies. Containers in Modal function as lightweight virtual machines, isolating programs to ensure consistent and reproducible execution environments. [Modal employs the sandboxed gVisor container runtime for enhanced security.](https://cloud.google.com/blog/products/identity-security/open-sourcing-gvisor-a-sandboxed-container-runtime) 

**3. Volumes in Modal:**

Modal provides mutable volumes, such as `modal.Volume`, designed for high-performance file serving. These volumes can be simultaneously attached to multiple Modal functions, supporting concurrent reading and writing. However, unlike networked filesystems, `modal.Volume` does not automatically synchronize writes between mounted volumes, making it best suited for write-once, read-many I/O workloads. 

**4. Key Features and Differentiators of Modal:**

- **Serverless Execution:** Run any code remotely within seconds, eliminating the need for manual server management. 

- **Customizable Environments:** Define container environments directly in code or utilize pre-built backends, allowing for tailored execution contexts. 

- **Seamless Scaling:** Effortlessly scale applications horizontally to thousands of containers, with support for GPU acceleration when needed. 

- **Web Endpoints and Scheduling:** Serve functions as [web endpoints](https://modal.com/docs/guide/webhooks) and deploy persistent scheduled jobs with ease. 

**5. Dockerfile Configuration:**

```dockerfile
FROM python:3.10

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

RUN mkdir -p /root/.ollama/models

ENV OLLAMA_HOST=0.0.0.0
```

**6. Modal Application Setup:**

```python
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
```

**7. Key Considerations:**

- **Model Storage:** Ollama stores models in the `~/.ollama/models` directory. By mounting this directory as a volume in Modal, you ensure that models persist across function invocations.

- **[GPU Utilization](https://modal.com/docs/guide/gpu):** The `gpu="any"` parameter in the `@app.function` decorator allows the function to utilize available GPU resources, enhancing performance for model inference tasks.

- **Model Management:** The script checks for the presence of required models and pulls them if they are not already available, ensuring that the necessary resources are in place before execution.

**8. Running the Application:**

```
modal run demo.py
```

By leveraging Modal's serverless capabilities alongside Ollama's AI models, you can efficiently deploy and scale your applications without the overhead of managing underlying infrastructure. 
