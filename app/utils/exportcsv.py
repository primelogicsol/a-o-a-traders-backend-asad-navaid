import csv
from io import StringIO
from fastapi.responses import Response

def generate_csv(data: list, header: list, filename: str) -> Response:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    
    for row in data:
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
