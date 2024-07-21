from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
import openai

# Initialize the FastAPI app
app = FastAPI()

# Set your OpenAI API key from an environment variable for security
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI with the correct purpose
        response = openai.File.create(
            file=open(file_location, "rb"),
            purpose='assistants'
        )
        file_id = response['id']

        # Create a message with the image
        message = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that helps to identify lateral flow test results."},
                {"role": "user", "content": "Please identify the result of this lateral flow test.", "files": [file_id]}
            ]
        )

        # Find the assistant's response
        result = message.choices[0].message['content']

        # Clean up the saved file
        os.remove(file_location)

        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)