import time

class CyberAttackClassifier:

    def __init__(self,event_bus):

        self.bus = event_bus
        self.timestamps=[]

        self.bus.subscribe("can.data",self.on_data)

    def on_data(self,data):

        now=time.time()
        self.timestamps.append(now)

        self.timestamps=[t for t in self.timestamps if now-t<1]

        if len(self.timestamps)>80:

            self.bus.publish("security.alert",{
                "type":"DOS_ATTACK",
                "msg":"Possible CAN Flood Attack"
            })
