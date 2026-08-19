"""
Thin view layer — delegates all logic to the analyzer service.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services.analyzer import analyze_upload
from .services.parser import ParseError


@require_http_methods(["GET"])
def upload_page(request: HttpRequest) -> HttpResponse:
    return render(request, "preview/upload.html")


@require_http_methods(["POST"])
def analyze(request: HttpRequest) -> HttpResponse:
    uploaded = request.FILES.get("csv_file")
    if not uploaded:
        return render(request, "preview/upload.html", {"error": "Please select a CSV file to upload."})

    if not uploaded.name.endswith(".csv"):
        return render(request, "preview/upload.html", {"error": "Only .csv files are accepted."})

    try:
        file_bytes = uploaded.read()
        result = analyze_upload(file_bytes)
    except ParseError as exc:
        return render(request, "preview/upload.html", {"error": str(exc)})
    except UnicodeDecodeError:
        return render(request, "preview/upload.html", {"error": "File is not valid UTF-8."})
    except Exception:
        return render(request, "preview/upload.html", {"error": "Unable to process the file. Please check the format."})

    return render(request, "preview/results.html", {"result": result, "filename": uploaded.name})
