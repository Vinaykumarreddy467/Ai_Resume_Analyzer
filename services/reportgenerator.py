"""Report saving service."""

import json
import os
import datetime
from services.logger import get_logger

log = get_logger("reportgenerator")


def save_reports(report_data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = report_data.get("candidate_name", "unknown")
    role = report_data.get("candidate_role", "unknown")
    name = name.lower().replace(" ", "_")
    role = role.lower().replace(" ", "_")
    filename = f"{name}_{role}_{timestamp}.json"

    os.makedirs("reports", exist_ok=True)
    report_path = os.path.join("reports", filename)

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=4)

    log.info("Report saved: %s (%d keys)", report_path, len(report_data))
    return report_path
