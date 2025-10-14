# message_templates.py
from datetime import datetime

def get_valid_register(sn: str = "ZX0006827500") -> dict:
    """Devuelve un mensaje válido de registro con timestamp actual."""
    return {
        "cmd": "reg",
        "sn": sn,
        "devinfo": {
            "modelname": "tfs30",
            "usersize": 3000,
            "fpsize": 3000,
            "cardsize": 3000,
            "pwdsize": 3000,
            "logsize": 100000,
            "useduser": 1000,
            "usedfp": 1000,
            "usedcard": 2000,
            "usedpwd": 400,
            "usedlog": 100000,
            "usednewlog": 5000,
            "fpalgo": "thbio3.0",
            "firmware": "th600w v6.1",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }

INVALID_REGISTER = {
    "cmd": "reg",
    # "sn" intencionalmente omitido
    "devinfo": {"modelname": "tfs30", "usersize": 3000},
}

MALFORMED_JSON = '{"cmd": "reg", "sn": "BAD_SN", "devinfo": {"modelname":"tfs30"'
