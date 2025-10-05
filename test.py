def create_dynamic_class(class_name, methods_code):
    local_namespace = {}
    class_definition = f"""
class {class_name}:
    def __init__(self, value):
        self.value = value
        from RoDevEngine.core.logger import Logger, configure_loggers, LoggingLevels
        configure_loggers(log_level=LoggingLevels.DEBUG, log_to_console=True)

        Logger("DYNAMIC").log_info(f"Instance of {class_name} created with value: {{value}}")
    {methods_code}
"""
    exec(class_definition, globals(), local_namespace)
    return local_namespace[class_name]

# Define some methods for the class
methods = """
    def greet(self):
        return f"Hello from {self.value}!"
"""

# Create the class dynamically
MyDynamicClass = create_dynamic_class("MyDynamicClass", methods)

# Use the dynamically created class
instance = MyDynamicClass("Python")
print(instance.greet())