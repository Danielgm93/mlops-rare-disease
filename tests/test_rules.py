
import json
from model.rules import predict_status

def test_all_labels():
    cases = [
        ({"fever":0.5,"pain":1,"days":0}, "NO ENFERMO"),
        ({"fever":2.0,"pain":3,"days":3}, "ENFERMEDAD LEVE"),
        ({"fever":6.0,"pain":6,"days":10,"comorbidity":1}, "ENFERMEDAD AGUDA"),
        ({"fever":4.0,"pain":4,"days":45}, "ENFERMEDAD CRÓNICA"),
    ]
    for x, y in cases:
        assert predict_status(x) == y
