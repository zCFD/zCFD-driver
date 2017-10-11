

class Message:
    """Encodes and decodes messages between client and service"""
    # def __init__(self):

    @staticmethod
    def start():
        return 'CMD:start'

    @staticmethod
    def is_start(packet):
        return packet == Message.start()

    @staticmethod
    def stop():
        return 'CMD:stop'

    @staticmethod
    def is_stop(packet):
        return packet == Message.stop()

    @staticmethod
    def dump():
        return 'CMD:stop'

    @staticmethod
    def is_dump(packet):
        return packet == Message.dump()

    @staticmethod
    def config(configtxt):
        return 'CMD:config: ' + configtxt

    @staticmethod
    def is_config(packet):
        return packet.startswith("CMD:config:")

    @staticmethod
    def get_config(packet):
        return packet[12:]

    @staticmethod
    def log(logtxt):
        return 'LOG: ' + logtxt

    @staticmethod
    def is_log(packet):
        return packet.startswith("LOG:")

    @staticmethod
    def get_log(packet):
        return packet[5:]
