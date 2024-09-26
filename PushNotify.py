from notifypy import Notify


def notify_popup(title, message):
    notification = Notify()
    notification.title = f"{title}"
    notification.message = f"{message}"
    notification.application_name = "TrackTool"
    notification.icon = "content/UI/logo.ico"
    notification.audio = "content/Sound/pushMessage.wav"
    # notification.audio = "content/Sound/seatbelt.wav"

    notification.send(block=False)
