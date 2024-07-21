from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize the FastAPI app
app = FastAPI()

# Set your OpenAI API key from an environment variable for security

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI with the correct purpose
        file = client.files.create(
            file=open(file_location, "rb"),
            purpose='vision'
                                   )

        # Create a message with the image
        message = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that helps to identify lateral flow test results."
             },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please identify the result of this lateral flow test."
                    },
                    {
                        "type": "image_file",
                        "image_file": {"file_id": file.id}
                    },
                ],
            }
        ])

        # Find the assistant's response
        result = message.choices[0].message.content

        # Clean up the saved file
        os.remove(file_location)

        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)