from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize the FastAPI app
app = FastAPI()

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI with the correct purpose
        uploaded_file_response = client.files.create(
            file=open(file_location, "rb"),
            purpose='vision'
        )
        uploaded_file_id = uploaded_file_response.get("id")

        if not uploaded_file_id:
            raise Exception("Failed to upload file to OpenAI")

        # Create an assistant
        assistant = client.beta.assistants.create(
            model="gpt-4-turbo",
            instructions="You are an assistant that helps to identify lateral flow test results.",
            name="Lateral Flow Test Identifier",
            tools=[{"type": "file_search"}],
            tool_resources={"file_ids": [uploaded_file_id]}
        )
        assistant_id = assistant.get("id")

        if not assistant_id:
            raise Exception("Failed to create assistant")

        # Create a thread and run it with the assistant
        stream = client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please identify the result of this lateral flow test."
                            },
                            {
                                "type": "image_file",
                                "image_file": {"file_id": uploaded_file_id}
                            }
                        ]
                    }
                ]
            },
            stream=True
        )

        # Collect the assistant's response
        result = ""
        for event in stream:
            if event["object"] == "thread.message.delta":
                deltas = event["delta"]["content"]
                for delta in deltas:
                    if delta["type"] == "text":
                        result += delta["text"]["value"]

        # Clean up the saved file
        os.remove(file_location)

        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)