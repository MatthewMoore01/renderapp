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
            @override
            def on_text_created(self, text) -> None:
                print(f"\nassistant > ", end="", flush=True)

            @override
            def on_text_delta(self, delta, snapshot):
                print(delta.value, end="", flush=True)

            def on_tool_call_created(self, tool_call):
                print(f"\nassistant > {tool_call.type}\n", flush=True)

            def on_tool_call_delta(self, delta, snapshot):
                if delta.type == 'code_interpreter':
                    if delta.code_interpreter.input:
                        print(delta.code_interpreter.input, end="", flush=True)
                    if delta.code_interpreter.outputs:
                        print(f"\n\noutput >", flush=True)
                        for output in delta.code_interpreter.outputs:
                            if output.type == "logs":
                                print(f"\n{output.logs}", flush=True)

        # Save the uploaded file
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Upload the file to OpenAI with the correct purpose
        uploaded_file = client.files.create(
            file=open(file_location, "rb"),
            purpose='vision'
        )

        # Create an assistant
        assistant = client.beta.assistants.create(
            name="Lateral Flow Test Identifier",
            description="You are an assistant that helps to identify lateral flow test results.",
            model="gpt-4-turbo",
            tools=[{"type": "file_search"}, {"type": "code_interpreter"}]
        )

        # Create a thread and run it with the assistant
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
                assistant_id=assistant.id,
                event_handler=EventHandler(),
        ) as stream:
            stream.until_done()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)