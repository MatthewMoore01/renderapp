from fastapi import FastAPI, UploadFile, File
import openai
import uvicorn

app = FastAPI()

openai.api_key = 'sk-proj-bKmMrLvoLMlazLgYwbIsT3BlbkFJxZpw40MFZntiEXZJqHuj'

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    # Save the uploaded file
    with open(file.filename, "wb") as f:
        f.write(await file.read())

    # Upload the file to OpenAI
    response = openai.File.create(
        file=open(file.filename, "rb"),
        purpose='assistants'
    )
    file_id = response['id']

    # Create a thread
    thread = openai.Thread.create()

    # Add a message with the image
    message = openai.Message.create(
        thread_id=thread.id,
        role="user",
        content="Please identify the result of this lateral flow test.",
        file_ids=[file_id]
    )

    # Run the assistant
    run = openai.Run.create(
        thread_id=thread.id,
        assistant_id='asst_zLWEETO02q3El9LXec4PfNJi'
    )

    # Retrieve the messages in the thread
    messages = openai.Message.list(
        thread_id=thread.id
    )

    # Find the assistant's response
    result = ""
    for msg in messages['data']:
        if msg['role'] == 'assistant':
            result = msg['content']
            break

    return {"result": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
