from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the FastAPI app
app = FastAPI()

# Set your OpenAI API key from an environment variable for security
client = OpenAI(api_key='OPENAI_API_KEY')

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI
        response = client.files.create(file=open(file_location, "rb"),
        purpose='answers')
        file_id = response.id

        # Create a thread (if this is needed by your specific OpenAI API use case)
        thread_response = openai.Thread.create()
        thread_id = thread_response['id']

        # Add a message with the image
        message_response = openai.Message.create(
            thread_id=thread_id,
            role="user",
            content="Please identify the result of this lateral flow test.",
            file_ids=[file_id]
        )

        # Run the assistant
        run_response = openai.Thread.run(
            thread_id=thread_id,
            assistant_id='asst_zLWEETO02q3El9LXec4PfNJi'
        )

        # Retrieve the messages in the thread
        messages = openai.Message.list(thread_id=thread_id)

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
