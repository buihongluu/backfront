"""Chuẩn topic MQTT dùng chung (FEAT-CORE-04).

Không module nào gọi trực tiếp module khác — giao tiếp qua các topic này.
"""


def camera_person_detected(camera_id: str) -> str:
    return f"camera/{camera_id}/person_detected"


def camera_fire_detected(camera_id: str) -> str:
    return f"camera/{camera_id}/fire_detected"


def camera_ppe_violation(camera_id: str) -> str:
    return f"camera/{camera_id}/ppe_violation"


def radar_stroke_detected(radar_id: str) -> str:
    return f"radar/{radar_id}/stroke_detected"


def radar_fall_detected(radar_id: str) -> str:
    return f"radar/{radar_id}/fall_detected"


def device_status(device_id: str) -> str:
    return f"device/{device_id}/status"


def alert(level: str) -> str:
    return f"alert/{level}"


ATTENDANCE_CHECKIN = "attendance/checkin"
NOTIFICATION_SEND = "notification/send"
