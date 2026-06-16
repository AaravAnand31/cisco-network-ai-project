def generate_command(user_input):
    text = user_input.lower()

    if "show interfaces" in text:
        return "show interfaces"

    elif "show ip" in text:
        return "show ip interface brief"

    elif "disable port 1" in text:
        return """
configure terminal
interface gigabitethernet0/1
shutdown
"""

    elif "enable port 1" in text:
        return """
configure terminal
interface gigabitethernet0/1
no shutdown
"""

    return "Unknown command"