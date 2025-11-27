from src.db import Database

def seed():
    db = Database()

    # ---------------------------
    # Add customers
    # ---------------------------
    customers = [
        {
            "name": "Imtiaz Group",
            "address": "Guj Mega - CQLA",
            "ntn": "B353738",
            "strn": "3277876321298",
            "contact": "03202019669",
            "email": ""
        },
        {
            "name": "Metro Cash & Carry",
            "address": "Karachi",
            "ntn": "B998877",
            "strn": "3271231231234",
            "contact": "0300-1122334",
            "email": ""
        },
        {
            "name": "Al Fatah Stores",
            "address": "Lahore",
            "ntn": "B445566",
            "strn": "3277899876543",
            "contact": "0301-9988776",
            "email": ""
        }
    ]

    for c in customers:
        db.add_customer(c)

    # ---------------------------
    # Add products
    # ---------------------------
    products = [
        {
            "name": "Maykey Hair Color Dark Brown 250ml",
            "description": "HC250DB",
            "unit_price": 700,
            "tax_rate": 18,
            "active": 1
        },
        {
            "name": "Maykey Hair Color Black 250ml",
            "description": "HC250BK",
                       "unit_price": 700,
            "tax_rate": 18,
            "active": 1
        },
        {
            "name": "Maykey Hair Color Dark Brown 30ml",
            "description": "HC30DB",
            "unit_price": 68.19,
            "tax_rate": 18,
            "active": 1
        }
    ]

    for p in products:
        db.add_product(p)

    print("✅ Sample customers and products added successfully.")

if __name__ == "__main__":
    seed()
