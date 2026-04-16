import os
import json
import base64
import urllib.request
from datetime import datetime, timezone

PDF_URL = "https://www.meteoromania.ro/Upload-Produse/nivologie/nivologie.pdf"
OUTPUT_FILE = "data.json"
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash-preview-04-17:generateContent?key={GEMINI_API_KEY}"
)

PROMPT = """Ești un expert în procesarea buletinelor nivometeorlogice românești.
Extrage TOATE datele din acest buletin nivometeorologic și returnează DOAR un obiect JSON valid, fără text suplimentar, fără markdown, fără backticks.

Schema exactă pe care trebuie să o urmezi:
{
  "buletin_nivometeorologic": {
    "perioada": "string — intervalul de valabilitate exact din document",
    "rezumat_general": "string sau null — rezumatul de pe prima pagină dacă există",
    "masive": [
      {
        "nume": "string — numele exact al masivului/masivelor din document",
        "risc": {
          "peste_1800m": "number (1-5) sau null dacă nu e specificat pe altitudini",
          "sub_1800m": "number (1-5) sau null dacă nu e specificat pe altitudini",
          "general": "number (1-5) sau null dacă există separare pe altitudini"
        },
        "text_descriptiv": "string sau obiect cu chei peste_1800m/sub_1800m — copiază textul exact din document"
      }
    ],
    "strat_zapada": {
      "Carpatii_Meridionali": [{"statie": "string", "cm": "number sau string petice"}],
      "Carpatii_Orientali":   [{"statie": "string", "cm": "number sau string petice"}],
      "Carpatii_Occidentali": [{"statie": "string", "cm": "number sau string petice"}]
    },
    "temperaturi_prognozate": {
      "peste_1800m": {"minime": "string", "maxime": "string"},
      "sub_1800m":   {"minime": "string", "maxime": "string"}
    },
    "prognoza_vreme": "string — textul complet al prognozei vremii"
  }
}

Reguli stricte:
- Dacă un câmp nu există în document, folosește null — nu inventa date.
- Pentru strat_zapada, include TOATE stațiile menționate, inclusiv cele cu valori mici sau "petice".
- Pentru masive, include TOATE masivele menționate în document, indiferent de număr.
- Dacă masivul are text descriptiv separat pe altitudini, folosește obiect cu chei peste_1800m și sub_1800m.
- Dacă masivul are un singur text fără separare altitudinală, pune textul direct ca string.
- Returnează DOAR JSON. Niciun alt text."""


def fetch_pdf(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def call_gemini(pdf_bytes: bytes) -> dict:
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    payload = json.dumps({
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        GEMINI_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # strip markdown fences if Gemini adds them despite instructions
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(raw_text)


def validate(data: dict) -> None:
    """Basic sanity check — raises if data looks incomplete."""
    b = data.get("buletin_nivometeorologic", {})
    masive = b.get("masive", [])
    if len(masive) < 2:
        raise ValueError(f"Prea puține masive extrase: {len(masive)}. Parsare probabil eșuată.")
    for m in masive:
        r = m.get("risc", {})
        if all(v is None for v in r.values()):
            raise ValueError(f"Masivul '{m.get('nume')}' nu are niciun risc extras.")


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Descărcare PDF...")
    pdf_bytes = fetch_pdf(PDF_URL)
    print(f"  PDF descărcat: {len(pdf_bytes):,} bytes")

    print("  Trimitere la Gemini 2.5 Flash...")
    data = call_gemini(pdf_bytes)

    print("  Validare date...")
    validate(data)

    # adaugă metadata
    data["ultima_actualizare"] = datetime.now(timezone.utc).isoformat()
    data["sursa"] = PDF_URL

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    masive_count = len(data["buletin_nivometeorologic"].get("masive", []))
    print(f"  Salvat {OUTPUT_FILE} — {masive_count} masive extrase.")


if __name__ == "__main__":
    main()
