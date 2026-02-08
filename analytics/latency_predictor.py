from collections import deque
import numpy as np

class LatencyPredictor:

    def __init__(self,event_bus):

        self.bus = event_bus
        self.latencies = deque(maxlen=100)

        self.bus.subscribe("can.data",self.on_data)

    def on_data(self,data):

        latency = data.get("latency",0)

        self.latencies.append(latency)

        if len(self.latencies)<20:
            return

        arr = np.array(self.latencies)

        trend = np.polyfit(range(len(arr)),arr,1)[0]

        if trend>50:

            self.bus.publish("system.warning",{
                "type":"LATENCY_RISE",
                "msg":"Latency trend increasing",
                "slope":trend
            })
