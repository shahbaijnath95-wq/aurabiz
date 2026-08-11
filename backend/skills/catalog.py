from skills.base import Skill
from services.catalog_service import CatalogService


class CatalogSkill(Skill):
    name = "catalog"
    description = "Product search, availability, alternatives, recommendations"
    capabilities = ["search_products", "check_availability", "recommend", "alternatives"]

    def __init__(self, db=None):
        self.db = db

    async def execute(self, context: dict) -> dict:
        query = context.get("query", "")
        business_id = context.get("business_id", "")
        business_name = context.get("business_name", "")

        if not self.db or not business_id:
            if query:
                response = f"Aap kya dhoondh rahe hain {query}? Mere paas bahut acche options hain! Price aur availability bata du?"
            else:
                response = f"Hamare paas bahut acche products hain! Kya specifically kuch dhoondh rahe hain? Main suggest kar sakta hun."
            return {"response": response, "skill": self.name, "products": []}

        try:
            catalog_svc = CatalogService(self.db)
            products = await catalog_svc.search_products(business_id, query, limit=5)

            if products:
                # Format product list for response
                product_lines = []
                for p in products[:5]:
                    stock_status = "Available" if p.get("stock", 0) > 0 else "Out of Stock"
                    product_lines.append(
                        f"• {p['name']} - Rs{p['price']} ({stock_status})"
                    )
                response = (
                    f"Ye products mil rahe hain {business_name} mein:\n\n"
                    + "\n".join(product_lines)
                    + "\n\nKoi product chahiye? Price ya detail bata du?"
                )
            else:
                response = f"Abhi '{query}' se related products nahi mil rahe. Koi aur cheez dhoondh rahe hain?"

            return {"response": response, "skill": self.name, "products": products}
        except Exception as e:
            return {
                "response": f"Catalog search mein dikkat aa rahi hai. Phir se try karein.",
                "skill": self.name,
                "products": [],
            }

    def format_response(self, result: str) -> str:
        return result
