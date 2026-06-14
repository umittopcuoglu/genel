"""Full seed script: room types, rooms, rate plans, guests, reservations."""
import requests
import json

BASE = "http://localhost:8000/api/v1"

# Login
r = requests.post(f"{BASE}/auth/login", json={"email": "superadmin@hotelops.com", "password": "Super123!"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Room Types
print("=== Room Types ===")
room_types = {}
for rt in [
    {"name": "Standard", "code": "STD", "base_price": 150.0, "max_occupancy": 2, "description": "Standart oda, şehir manzaralı"},
    {"name": "Deluxe", "code": "DLX", "base_price": 250.0, "max_occupancy": 2, "description": "Deluxe oda, deniz manzaralı, minibar"},
    {"name": "Suite", "code": "STE", "base_price": 450.0, "max_occupancy": 4, "description": "Suit oda, oturma odası, jakuzi"},
    {"name": "Family", "code": "FAM", "base_price": 350.0, "max_occupancy": 5, "description": "Aile odası, iki yatak odası"},
]:
    r = requests.post(f"{BASE}/front-office/room-types", json=rt, headers=h)
    d = r.json()
    room_types[rt["code"]] = d["id"]
    print(f"  {rt['name']} -> {d['id']}")

# Rooms
print("\n=== Rooms ===")
room_configs = [
    (range(101, 111), 1, "STD"),
    (range(201, 209), 2, "DLX"),
    (range(301, 305), 3, "STE"),
    (range(401, 405), 4, "FAM"),
]
count = 0
for nums, floor, code in room_configs:
    for n in nums:
        r = requests.post(f"{BASE}/front-office/rooms", json={
            "number": str(n), "floor": floor,
            "room_type_id": room_types[code], "status": "clean"
        }, headers=h)
        count += 1
print(f"  {count} rooms created")

# Rate Plans
print("\n=== Rate Plans ===")
for rp in [
    {"name": "Standart Tarife", "code": "BAR", "room_type_id": room_types["STD"], "base_rate": 150.0, "currency": "TRY", "is_active": True},
    {"name": "Deluxe Tarife", "code": "DLX-BAR", "room_type_id": room_types["DLX"], "base_rate": 250.0, "currency": "TRY", "is_active": True},
    {"name": "Suite Tarife", "code": "STE-BAR", "room_type_id": room_types["STE"], "base_rate": 450.0, "currency": "TRY", "is_active": True},
    {"name": "Aile Tarife", "code": "FAM-BAR", "room_type_id": room_types["FAM"], "base_rate": 350.0, "currency": "TRY", "is_active": True},
]:
    r = requests.post(f"{BASE}/rate-plans", json=rp, headers=h)
    d = r.json()
    print(f"  {d.get('name', d)}")

# Guests
print("\n=== Guests ===")
guest_data = [
    {"first_name": "Ahmet", "last_name": "Yılmaz", "email": "ahmet@example.com", "phone": "+905551234567", "nationality": "TUR"},
    {"first_name": "Elif", "last_name": "Kaya", "email": "elif@example.com", "phone": "+905559876543", "nationality": "TUR"},
    {"first_name": "Mehmet", "last_name": "Demir", "email": "mehmet@example.com", "phone": "+905553456789", "nationality": "TUR", "is_vip": True, "notes": "VIP misafir"},
    {"first_name": "John", "last_name": "Smith", "email": "john@example.com", "phone": "+441234567890", "nationality": "GBR", "is_vip": True, "company": "Smith Corp"},
    {"first_name": "Maria", "last_name": "Schmidt", "email": "maria@example.com", "phone": "+491234567890", "nationality": "DEU"},
    {"first_name": "Ayşe", "last_name": "Çelik", "email": "ayse@example.com", "phone": "+905554567890", "nationality": "TUR"},
    {"first_name": "Can", "last_name": "Öztürk", "email": "can@example.com", "phone": "+905555678901", "nationality": "TUR"},
    {"first_name": "Zeynep", "last_name": "Arslan", "email": "zeynep@example.com", "phone": "+905556789012", "nationality": "TUR"},
]
guest_ids = []
for g in guest_data:
    r = requests.post(f"{BASE}/front-office/guests", json=g, headers=h)
    d = r.json()
    guest_ids.append(d["id"])
    print(f"  {g['first_name']} {g['last_name']} -> {d['id']}")

# Reservations
print("\n=== Reservations ===")
reservations = [
    {"guest_id": guest_ids[0], "room_type_id": room_types["STD"], "check_in": "2026-06-14", "check_out": "2026-06-17", "adults": 2, "children": 0, "source": "direct", "notes": "Erken check-in istendi"},
    {"guest_id": guest_ids[1], "room_type_id": room_types["DLX"], "check_in": "2026-06-16", "check_out": "2026-06-20", "adults": 2, "children": 1, "source": "ota"},
    {"guest_id": guest_ids[2], "room_type_id": room_types["STE"], "check_in": "2026-06-15", "check_out": "2026-06-22", "adults": 2, "children": 2, "source": "direct", "notes": "VIP - Balayı"},
    {"guest_id": guest_ids[3], "room_type_id": room_types["STE"], "check_in": "2026-06-14", "check_out": "2026-06-18", "adults": 2, "children": 0, "source": "corporate", "notes": "Corporate rate"},
    {"guest_id": guest_ids[4], "room_type_id": room_types["DLX"], "check_in": "2026-06-17", "check_out": "2026-06-19", "adults": 1, "children": 0, "source": "ota"},
    {"guest_id": guest_ids[5], "room_type_id": room_types["STD"], "check_in": "2026-06-18", "check_out": "2026-06-21", "adults": 1, "children": 0, "source": "direct"},
    {"guest_id": guest_ids[6], "room_type_id": room_types["DLX"], "check_in": "2026-06-19", "check_out": "2026-06-23", "adults": 2, "children": 0, "source": "ota"},
    {"guest_id": guest_ids[7], "room_type_id": room_types["FAM"], "check_in": "2026-06-20", "check_out": "2026-06-25", "adults": 2, "children": 3, "source": "direct"},
]
for res in reservations:
    r = requests.post(f"{BASE}/reservations", json=res, headers=h)
    d = r.json()
    print(f"  {d.get('id', d)}")

print("\n✅ Full seed complete!")
print(f"  Room Types: {len(room_types)}")
print(f"  Rooms: {count}")
print(f"  Guests: {len(guest_ids)}")
print(f"  Reservations: {len(reservations)}")
