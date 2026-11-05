# Lab 4 — H2 Reflection (M1 working draft)

1. In Lab 3, I called `service.handle()` directly from Python in the same process.
2. In Lab 4, `POST /v1/chat` allows another program to send a JSON request to the FastAPI server over HTTP.
3. FastAPI checks the incoming data and returns a standard HTTP status code with a JSON response.
4. Our team can connect a browser or mobile application to the backend without importing Python modules into the client.
5. This separation also makes the service easier to test, maintain, and extend as our project grows.

> Review and personalize these five lines before submitting an individual reflection.
