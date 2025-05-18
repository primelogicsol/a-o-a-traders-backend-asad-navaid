import asyncio
from google import genai
import json
from app.utils.model_fileds import build_image_model_prompt

client = genai.Client(api_key="AIzaSyCqUDPh-e1fIN1XSNGpOpCaF5pOCJBbW54")

async def generate_image_mapping(all_sheet_preview):
    model_fields_prompt = build_image_model_prompt()
    prompt = f"""
You are a semantic mapping expert.

Map columns from the SOURCE sheets to the TARGET database schema. Use both column names and sample values to make accurate matches.

---

## TARGET DATABASE MODELS

{model_fields_prompt}

---

## SOURCE SHEETS (HEADERS + SAMPLE ROWS):

{all_sheet_preview}

---

## RULES:

1. ABSOLUTELY DO NOT include `product_id` in the output. Not even as `null`.
2. If `product_id` appears in the TARGET schema, IGNORE it completely.
3. If any mapping includes `product_id`, it is INVALID.
4. Return only one best-matching SOURCE column name for each TARGET field.
5. If no good match exists, assign `null` to that field.
6. DO NOT create new keys or sheet-prefixed fields like "sheet_XYZ_fieldname".
7. DO NOT assign the same source column to multiple target fields.
8. Prefer columns with `.pdf` values for `msds_image`.
9. Use keywords like "alt", "variant", "brand", "logo" to identify matching fields.
10. Only return keys matching the TARGET model fields listed above.

---

## OUTPUT FORMAT (strict flat JSON):

{{"image": "...",
  "image_variant1": "...",
  ...
  "msds_image_url": "..."
}}

Return only this JSON. No sheet names. No explanation. No extra fields.
"""

    def call_gemini():
        return client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt,
        ).text
    
    response = await asyncio.to_thread(call_gemini)

    mapping_str = response.strip("```json\n").strip("```")
    raw_mapping = json.loads(mapping_str)

    forbidden_keys = {"product_id"}
    clean_mapping = {k: v for k, v in raw_mapping.items() if k not in forbidden_keys}

    return clean_mapping
