from datetime import datetime
import pytz

def get_local_time():
    local_timezone = pytz.timezone("Asia/Jakarta")
    return datetime.now(local_timezone).isoformat()