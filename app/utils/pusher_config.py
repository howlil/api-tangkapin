from pusher import Pusher

pusher_client = Pusher(
    app_id = "1911283",
    key = "ef6ded14f456b73f9a12",
    secret = "275efadb307fd2df90b7",
    cluster = "ap1",
    ssl=True
)

def send_notification(channel, event, data):
    """Helper function untuk mengirim notifikasi via Pusher"""
    try:
        pusher_client.trigger(channel, event, data)
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False