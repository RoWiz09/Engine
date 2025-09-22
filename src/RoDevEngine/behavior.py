class Behavior:
    def __init__(self):
        self.enabled = True
        
    def update(self, dt:float):
        """
            Runs every tick.
            Args:
                dt (float): Deltatime
        """
        pass

    def fixed_update(self):
        """
            Runs 50 times every second.
        """
        pass

    def on_unloaded(self):
        """
            Called when the scene unloads!
        """
        pass