class BrainToolRegistry:
    def __init__(self, tools: dict): self.tools=tools
    def call(self, name, **kwargs):
        if name not in self.tools: raise KeyError(f'Unknown brain tool: {name}')
        return self.tools[name](**kwargs)
