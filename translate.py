import json, os, time, requests

CHECKPOINT_FILE = "progress.json"
OPENROUTER_KEY = "sk-or-..."
MODEL = "google/gemini-2.5-pro"  # o il modello scelto

def load_progress():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def translate_with_retry(text, context, retries=3):
    for attempt in range(retries):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Traduci EN→IT mantenendo tono e registro. Solo testo tradotto."},
                        {"role": "user", "content": f"CONTESTO:
{context}

TESTO:
{text}"}
                    ],
                    "temperature": 0.2
                },
                timeout=60
            )
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  ⚠️ Tentativo {attempt+1} fallito: {e}")
            time.sleep(5 * (attempt + 1))  # backoff esponenziale
    raise Exception(f"Chunk fallito dopo {retries} tentativi")

def translate_all(chunks_path):
    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    progress = load_progress()
    translated = [progress.get(str(i), "") for i in range(len(chunks))]

    for i, chunk in enumerate(chunks):
        if progress.get(str(i)):
            print(f"  ⏭️ Chunk {i+1}/{len(chunks)} già tradotto, salto.")
            continue

        context = "
".join(translated[max(0,i-2):i])
        print(f"  🔄 Chunk {i+1}/{len(chunks)}...")

        result = translate_with_retry(chunk["text"], context)
        translated[i] = result
        progress[str(i)] = result
        save_progress(progress)  # ← salva dopo ogni chunk

        time.sleep(0.8)  # rate limiting gentile

    print("
✅ Traduzione completata!")
    return translated
