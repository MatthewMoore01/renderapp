from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
from openai import OpenAI, AssistantEventHandler
from typing_extensions import override

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize the FastAPI app
app = FastAPI()

@app.post("/identify-lateral-flow-test/")
async def identify_lateral_flow_test(file: UploadFile = File(...)):
    try:

        class EventHandler(AssistantEventHandler):
            def __init__(self):
                self.result = ""

            @override
            def on_text_created(self, text) -> None:
                self.result += "\nassistant > "

            @override
            def on_text_delta(self, delta, snapshot):
                self.result += delta.value

            def on_tool_call_created(self, tool_call):
                self.result += f"\nassistant > {tool_call.type}\n"

            def on_tool_call_delta(self, delta, snapshot):
                if delta.type == 'code_interpreter':
                    if delta.code_interpreter.input:
                        self.result += delta.code_interpreter.input
                    if delta.code_interpreter.outputs:
                        self.result += f"\n\noutput >"
                        for output in delta.code_interpreter.outputs:
                            if output.type == "logs":
                                self.result += f"\n{output.logs}"

        event_handler = EventHandler()

        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI with the correct purpose
        uploaded_file = client.files.create(
            file=open(file_location, "rb"),
            purpose='vision'
        )

        # Create a thread
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please identify the result of this lateral flow test."
                        },
                        {
                            "type": "image_file",
                            "image_file": {"file_id": uploaded_file.id}
                        }
                    ]
                }
            ]
        )

        with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id='asst_zLWEETO02q3El9LXec4PfNJi',
                event_handler=event_handler,
        ) as stream:
            stream.until_done()

        # Clean up the saved file
        os.remove(file_location)

        return {"result": event_handler.result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)