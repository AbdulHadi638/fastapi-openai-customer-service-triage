LLM Powered Customer Support Triage API

A backend API that reads a customer support message and tells you what it's about (billing, bug, feature request, etc.) and how urgent it is  using an LLM. Built with Python, FastAPI, PostgreSQL, and Docker.

## What it does

Imagine a support inbox getting hundreds of messages a day. Someone has to read each one and figure out: what category is this, and how urgent? This project does that first step automatically.

You send it a message, and it sends back something like this:

```json
{
  "category": "bug",
  "urgency": "high",
  "confidence": 0.85,
  "reason": "Message describes a reproducible crash during export."
}
```

It's not just calling an LLM and hoping for the best. The response is checked against a strict schema every time, so `category` is always one of a fixed list, `confidence` is always a real number, etc. If the model returns something broken, the API gives it one chance to fix its own mistake before giving up cleanly.

Every message that comes through also gets saved to a Postgres database, along with its category and urgency. That's really the point of storing it  in a real setup, a support team wouldn't sit and call this API by hand for every message. Messages would flow in automatically, get classified, and land in the database. The team would then just look at the database and filter — "show me everything urgent," "show me all the billing stuff" — instead of reading every message themselves first.

## Tech stack

- **Backend:** Python + FastAPI
- **LLM:** OpenAI's Python SDK, pointed at OpenRouter (free, no credit card)
- **Validation:** Pydantic
- **Database:** PostgreSQL
- **Containerization:** Docker + Docker Compose
- **Frontend:** one plain HTML page, no framework

## Project files

```
main.py           → the API itself, the /triage endpoint
repository.py      → talks to Postgres, saves each result
log.sql            → creates the query_logs table on first run
prompts/           → the prompt sent to the LLM
triage.html        → the simple frontend
Dockerfile          → builds the app into a container
docker-compose.yml → runs the app + Postgres together
requirements.txt   → Python dependencies
.env.example       → template for your own .env file
```

## How it actually works

1. You submit a message to `/triage`.
2. It gets sent to the LLM along with instructions on exactly what shape to reply in.
3. The reply gets checked , is it valid JSON, does it match the schema?
4. If not, the model gets one more shot with its own broken answer and the error, and tries again.
5. If it still fails, you get a clear error instead of garbage data.
6. If it works, the result gets saved to Postgres and sent back to you.
7. If the LLM service itself is slow or down, it retries automatically a couple of times before giving up.

## Running it yourself

You'll need:
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- A free API key from [OpenRouter](https://openrouter.ai)

**1. Clone it:**
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

**2. Set up your `.env`:**

Copy `.env.example` to `.env`, then fill it in:
```env
OPENROUTER_API_KEY=your_actual_key_here

POSTGRES_USER=triage_user
POSTGRES_PASSWORD=triage_pass
POSTGRES_DB=triage_db

DATABASE_URL=postgresql://triage_user:triage_pass@db:5432/triage_db
```
(You can pick any username/password/db name you want , just make sure they match in both places. Leave `db` as-is in the URL, that's the internal name Docker uses for the database container.)

**3. Start it:**
```bash
docker compose up --build
```
First run takes a minute or two since it's downloading images. After that it's much faster.

**4. Open it up:**
- The app: [http://localhost:8000](http://localhost:8000)
- Auto-generated API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Testing it without the UI

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "My invoice charged me twice this month"}'
```

## Looking at what's stored in the database

```bash
docker compose exec db psql -U triage_user -d triage_db
```
Then:
```sql
SELECT * FROM query_logs ORDER BY created_at DESC;
```

## Stopping it

```bash
docker compose down
```
Add `-v` on the end if you want to wipe the database completely and start fresh next time.

## What's not built yet

This is a working core of a triage system , not a finished industry product. A few things I'd add if I kept going:

- An actual `/history` endpoint so you can pull past results through the API instead of only through the database directly
- Filtering/search on the query log (by category, urgency, or date range) to actually demonstrate the "team applies filters" workflow described above,as it will hapen in a real work environment

- Login/auth so queries can be tied to a specific person or team