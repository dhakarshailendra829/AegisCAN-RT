import numpy as np
from collections import deque

class AnomalyDetector:

    def __init__(self,event_bus,window=50):

        self.bus = event_bus
        self.history = deque(maxlen=window)

        self.bus.subscribe("can.data",self.on_data)

    def on_data(self,data):

        angle = data.get("angle",0)
        latency = data.get("latency",0)

        self.history.append([angle,latency])

        if len(self.history) < 20:
            return

        arr = np.array(self.history)

        mean = np.mean(arr,axis=0)
        std = np.std(arr,axis=0)

        if std[0]==0 or std[1]==0:
            return

        z = (arr[-1]-mean)/std

        if abs(z[0])>3 or abs(z[1])>3:

            self.bus.publish("security.alert",{
                "type":"ANOMALY",
                "msg":"Abnormal CAN Behaviour Detected",
                "data":data
            })
