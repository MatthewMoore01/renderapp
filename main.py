from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
from openai import OpenAI

client = OpenAI() # Initialize OpenAI Client
app = FastAPI()

openai.api_key = 'sk-proj-bKmMrLvoLMlazLgYwbIsT3BlbkFJxZpw40MFZntiEXZJqHuj'

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI
        response = client.beta.file.create(
            file=open(file_location, "rb"),
            purpose='assistants'
        )
        file_id = response['id']

        # Create a thread
        thread = client.beta.threads.create()

        # Add a message with the image
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Please identify the result of this lateral flow test.",
            file_ids=[file_id]
        )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id='asst_zLWEETO02q3El9LXec4PfNJi'
        )

        # Retrieve the messages in the thread
        messages = client.beta.threads.messages.(
            thread_id=thread.id
        )

        # Find the assistant's response
        result = ""
        for msg in messages['data']:
            if msg['role'] == 'assistant':
                result = msg['content']
                break

        # Clean up the saved file
        os.remove(file_location)

        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)