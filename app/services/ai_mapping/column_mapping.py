from google import genai

client = genai.Client(api_key="AIzaSyCqUDPh-e1fIN1XSNGpOpCaF5pOCJBbW54")
import json 

import asyncio

async def generate_column_mapping(all_sheet_preview, db_fields):
    prompt = f"""
You are a semantic data mapping expert analyzing both column names AND sample values.

TARGET SCHEMA:
{db_fields}

SOURCE COLUMNS:
{all_sheet_preview}

SAMPLE DATA (FIRST 2 ROWS):
{all_sheet_preview}

RULES:
1. Match based on BOTH column names AND data patterns and meanings.
2. Prioritize numeric fields for prices/quantities.
3. For product_name, find the column which completely reflects the name in detail.
3.For `description`, pick the field with the **longest, most detailed product text** (not short summaries).
4. Use date-like values for timestamp fields.
5. Do NOT map the same source column to more than one target field. Each source column must appear only once in the entire mapping.
6. Skip mapping and output of `supplier_id`.
7. If source column name has sheet prefix like `SheetName.ColumnName`, return only `ColumnName` (remove sheet name).
8. Ensure `"created_at"` and `"updated_at"` are mapped to different timestamp columns if available. If only one exists, assign it to `"created_at"` and leave `"updated_at"` as `null`.
9. Always include a `product_id` column as the identifier (shared or inferred).

RETURN FORMAT:
A flat JSON like:
{{ "db_field": "Matching Column Header Only (no sheet prefix)" }}

Respond only with the final JSON. No explanation.
"""

    def call_gemini():
        return client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        ).text

    response = await asyncio.to_thread(call_gemini)
    column_mapping_str = response.strip("```json\n").strip("```")
    raw_mapping = json.loads(column_mapping_str)

    seen_values = set()
    final_mapping = {}
    for k, v in raw_mapping.items():
        if v in seen_values:
            final_mapping[k] = None
        else:
            final_mapping[k] = v
            seen_values.add(v)

    return final_mapping


