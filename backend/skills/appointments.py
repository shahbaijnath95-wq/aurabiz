from skills.base import Skill


class AppointmentsSkill(Skill):
    name = "appointments"
    description = "Book, confirm, remind, reschedule - calendar management"
    capabilities = ["book_appointment", "confirm", "remind", "reschedule", "cancel"]

    async def execute(self, context: dict) -> dict:
        action = context.get("action", "book")
        customer_name = context.get("customer_name", "Customer")
        date = context.get("date", "")
        time = context.get("time", "")

        if action == "confirm":
            response = f"{customer_name} ji, aapka appointment {date} ko {time} bhai confirm ho gaya! ✅"
        elif action == "remind":
            response = f"{customer_name} ji, yaad rakhein - aapka appointment kal {time} bhai hai. 📅 Confirm karein!"
        elif action == "reschedule":
            response = f"{customer_name} ji, appointment reschedule karna hai? 📅 Naya din aur time bataiye."
        else:
            response = f"{customer_name} ji, appointment book karna hai? 📅 Kaunsa din aur time suitable hai?"

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
