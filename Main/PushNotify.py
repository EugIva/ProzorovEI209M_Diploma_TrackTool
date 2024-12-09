from notifypy import Notify


def notify_popup(title, message):
    """
    Уведомление о выполнении операции
    """
    notification = Notify()
    notification.title = f"{title}"
    notification.message = f"{message}"
    notification.application_name = "TrackTool"
    notification.icon = "Content/UI/logo.ico"
    notification.audio = "Content/Sound/pushMessage.wav"
    # notification.audio = "Content/Sound/seatbelt.wav"

    notification.send(block=False)
