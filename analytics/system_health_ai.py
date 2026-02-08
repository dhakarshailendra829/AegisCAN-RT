class SystemHealthAI:

    def __init__(self,event_bus):

        self.bus=event_bus

        self.bus.subscribe("system.metrics",self.on_metrics)

    def on_metrics(self,data):

        cpu=data.get("cpu",0)
        ram=data.get("ram",0)

        if cpu>85 or ram>85:

            self.bus.publish("system.alert",{
                "type":"RESOURCE_OVERLOAD",
                "msg":"System resources critical",
                "cpu":cpu,
                "ram":ram
            })
