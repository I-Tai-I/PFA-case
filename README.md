# PFA-case
My solution for a case in the hiring process of the PFA Softwaredeveloper role. 

## Content
This project implements a **domain-restricted AI chat API** built with FastAPI and Google Gemini.

- `routes.py` — Defines the FastAPI application, API endpoints, request validation, and error handling.
- `agent.py` — Implements the domain-restricted AI agent and manages chat sessions and persistence.
- `fictional_knowledge_base.txt` — Contains the restricted knowledge base used to constrain model responses.
- `chats.json` — Stores persistent chat history in JSON format. (Only exists after being run)
- `Dockerfile` — Defines the container configuration for running the application with Docker.
- `requirements.txt` — Lists the Python dependencies required to run the project.
- `logger.py` — Configures application logging used across the project. 
- `README.md` - Markdown file describing the project. You are reading it right now.
- `.gitignore` - Instructions for git to ignore files, mostly those created by running the app locally.
- `favicon.ico` - The PFA favicon, to make the browser tab look like it's part of PFA pension.

The main files of interest are `routes.py` and `agent.py`.

### `routes.py`
Defines the FastAPI application and API endpoints:
- `POST /chat` — Create or continue a chat session
- `GET /chat/{chat_id}` — Retrieve stored chat history
- `GET /` — Health check

Handles request validation, error handling, and OpenAPI documentation.

### `agent.py`
Contains the `DomainRestrictedAgent` class.

Responsibilities:
- Connects to Google Gemini using an API key
- Enforces strict knowledge-base restriction
- Persists conversation histories in `chats.json`

## Run the code

Remember to replace `YOUR_KEY_HERE` with your Google AI studio API key that you can find at https://aistudio.google.com/api-keys.

### Run locally in active virtual environment located in the PFA-case folder:
``` bash

set GOOGLE_API_KEY=YOUR_KEY_HERE

python -m pip install --upgrade pip

pip install -r requirements.txt

uvicorn routes:app --reload

```

### Run in docker:
``` bash

docker build -t pfa-agent .

docker run -p 8000:8000 -e GOOGLE_API_KEY=YOUR_KEY_HERE pfa-agent

```


## Access documentation:
Regardless how you run the code, you can access the documentation as follows: 

Swagger documentation at "http://127.0.0.1:8000/docs" 

ReDoc documentation at "http://127.0.0.1:8000/redoc"