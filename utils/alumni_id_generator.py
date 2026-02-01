from models import Alumni

def generate_alumni_id():
    last_alumni = Alumni.query.order_by(Alumni.id.desc()).first()

    if not last_alumni:
        return "ALM-01"

    last_number = int(last_alumni.alumni_id.split("-")[1])
    new_number = last_number + 1

    return f"ALM-{new_number:02d}"
