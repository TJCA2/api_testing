"""A small API for validating GUI detection output."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="GUI Detection Result Validator", version="1.0.0")

SUPPORTED_UI_CLASSES = [
    "button", "icon_button", "text_input", "checkbox", "dropdown", "tab",
    "menu_item", "other_interactable",
]


class Detection(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    bbox: tuple[int, int, int, int]


class ValidationRequest(BaseModel):
    screenshot_width: int = Field(gt=0)
    screenshot_height: int = Field(gt=0)
    min_confidence: float = Field(default=0.3, ge=0, le=1)
    detections: list[Detection] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gui-detection-validator"}


@app.get("/classes")
def classes():
    return {"classes": SUPPORTED_UI_CLASSES, "count": len(SUPPORTED_UI_CLASSES)}


@app.post("/validate")
def validate_detections(request: ValidationRequest):
    """Report semantic issues in model detections; malformed requests return HTTP 422."""
    issues = []
    for index, detection in enumerate(request.detections):
        x1, y1, x2, y2 = detection.bbox
        if detection.label not in SUPPORTED_UI_CLASSES:
            issues.append({"index": index, "code": "UNKNOWN_CLASS"})
        if x1 >= x2 or y1 >= y2:
            issues.append({"index": index, "code": "INVALID_BOX_ORDER"})
        if x1 < 0 or y1 < 0 or x2 > request.screenshot_width or y2 > request.screenshot_height:
            issues.append({"index": index, "code": "OUT_OF_BOUNDS"})
        if detection.confidence < request.min_confidence:
            issues.append({"index": index, "code": "LOW_CONFIDENCE"})

    return {
        "valid": len(issues) == 0,
        "detections_checked": len(request.detections),
        "issues": issues,
    }
