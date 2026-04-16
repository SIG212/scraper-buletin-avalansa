# merglamunte.ro/avalanșă

Buletin nivometeorologic zilnic pentru Carpații României, generat automat din PDF-ul ANM.

## Cum funcționează

```
PDF ANM (zilnic) → parse.py → Gemini 2.5 Flash → data.json → index.html
```

GitHub Actions rulează `parse.py` în fiecare dimineață la 09:00 (ora României), descarcă PDF-ul de la meteoromania.ro, îl trimite la Gemini 2.5 Flash care extrage datele structurate, și salvează `data.json` în repo. Pagina `index.html` citește `data.json` la fiecare vizită și randează dinamic.

## Setup

### 1. Fork / clone repo

```bash
git clone https://github.com/TU/avalansa
cd avalansa
```

### 2. Adaugă API key Gemini

În repo-ul tău pe GitHub:
- Settings → Secrets and variables → Actions → New repository secret
- Name: `GEMINI_API_KEY`
- Value: cheia ta de la [Google AI Studio](https://aistudio.google.com/app/apikey)

### 3. Activează GitHub Pages

- Settings → Pages → Source: `Deploy from a branch`
- Branch: `main`, folder: `/ (root)`

Pagina va fi accesibilă la `https://TU.github.io/avalansa/`

### 4. Test manual

Poți rula parserul local sau din GitHub UI:
- Actions → "Actualizare buletin avalanșă" → Run workflow

## Fișiere

| Fișier | Rol |
|--------|-----|
| `index.html` | Pagina publică — citește `data.json` și randează dinamic |
| `parse.py` | Descarcă PDF ANM + apelează Gemini → salvează `data.json` |
| `data.json` | Output generat automat — nu edita manual |
| `.github/workflows/update.yml` | Cron zilnic 07:00 UTC |

## Schema data.json

```json
{
  "ultima_actualizare": "ISO 8601",
  "sursa": "URL PDF ANM",
  "buletin_nivometeorologic": {
    "perioada": "interval valabilitate",
    "rezumat_general": "string sau null",
    "masive": [
      {
        "nume": "Munții Făgăraș și Bucegi",
        "risc": {
          "peste_1800m": 3,
          "sub_1800m": 1,
          "general": null
        },
        "text_descriptiv": {
          "peste_1800m": "...",
          "sub_1800m": "..."
        }
      }
    ],
    "strat_zapada": {
      "Carpatii_Meridionali": [{"statie": "Vârful Omu", "cm": 218}],
      "Carpatii_Orientali": [],
      "Carpatii_Occidentali": []
    },
    "temperaturi_prognozate": {
      "peste_1800m": {"minime": "-2..3 grade", "maxime": "2...8 grade"},
      "sub_1800m": {"minime": "3...5 grade", "maxime": "8...14 grade"}
    },
    "prognoza_vreme": "..."
  }
}
```

## Note

- Dacă ANM nu publică buletin (weekend, sărbători), `data.json` rămâne neschimbat din ziua anterioară.
- Dacă parsarea eșuează (PDF indisponibil, structură neașteptată), workflow-ul eșuează cu eroare și `data.json` nu e suprascris — pagina continuă să afișeze datele anterioare.
- Costul estimat: ~$0.002 per zi cu Gemini 2.5 Flash.

## Sursa datelor

Datele provin din [buletinul nivometeorologic ANM](https://www.meteoromania.ro/Upload-Produse/nivologie/nivologie.pdf), elaborat de Administrația Națională de Meteorologie, Sibiu.
