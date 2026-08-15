from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import time
import random

import repository

load_dotenv()


app = FastAPI()


client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    timeout=30.0
)


class TriageRequest(BaseModel):
    text: str


class TriageResult(BaseModel):
    category: str
    urgency: str
    confidence: float
    reason: str


def load_prompt():
    with open("triage-prompt.md", "r", encoding="utf-8") as file:
        return file.read()


def call_llm(prompt, text):

    for attempt in range(3):

        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            )

            return response

        except Exception as error:

            error_code = getattr(error, "status_code", None)

            if error_code == 429 or (
                error_code is not None and
                500 <= error_code <= 599
            ):
                if attempt < 2:
                    wait_time = (2 ** attempt) + random.uniform(0, 0.5)
                    time.sleep(wait_time)
                    continue

            raise error


def parse_result(raw_text):
    try:
        data = json.loads(raw_text)
        return TriageResult.model_validate(data)
    except Exception:
        return None


@app.get("/")
def home():
    return FileResponse("frontend.html")


@app.post("/triage", response_model=TriageResult)
def triage(request: TriageRequest):

    prompt = load_prompt()

    try:
        response = call_llm(prompt, request.text)

    except Exception as error:
        error_code = getattr(error, "status_code", None)

        if error_code in [400, 401, 403]:
            raise HTTPException(
                status_code=error_code,
                detail="LLM request failed."
            )

        raise HTTPException(
            status_code=504,
            detail="LLM service is unavailable."
        )

    parsed = parse_result(response.choices[0].message.content)

    if parsed is not None:
        repository.save_query_log(
            input_text=request.text,
            category=parsed.category,
            urgency=parsed.urgency,
            confidence=parsed.confidence,
            reason=parsed.reason
        )
        return parsed

    # repair retry — send the model its own broken output plus what went wrong
    repair = call_llm(
        prompt,
        f"Your previous response was invalid:\n{response.choices[0].message.content}\n\n"
        "Return only valid JSON matching the required schema."
    )

    parsed = parse_result(repair.choices[0].message.content)

    if parsed is not None:
        repository.save_query_log(
            input_text=request.text,
            category=parsed.category,
            urgency=parsed.urgency,
            confidence=parsed.confidence,
            reason=parsed.reason
        )
        return parsed

    raise HTTPException(
        status_code=422,
        detail="LLM response could not be validated."
    )