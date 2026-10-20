SEED = 2026
HISTORY_MONTHS = 36
HISTORY_END = "2026-09"
FORECAST_MONTHS = 12
WARNING_MONTHS = 6
BACKTEST_MONTHS = 6
BAND_LEVEL = 0.80
EMERGING_GROWTH = 0.15
STATE = "Tamil Nadu"

DISTRICTS = {
    "Chennai": {"x": 80.27, "y": 13.08, "size": 1.6},
    "Krishnagiri": {"x": 78.21, "y": 12.52, "size": 0.8},
    "Salem": {"x": 78.15, "y": 11.66, "size": 0.9},
    "Coimbatore": {"x": 76.96, "y": 11.02, "size": 1.2},
    "Tiruppur": {"x": 77.62, "y": 11.10, "size": 0.9},
    "Tiruchirappalli": {"x": 78.70, "y": 10.80, "size": 0.9},
    "Madurai": {"x": 78.12, "y": 9.93, "size": 1.0},
    "Tirunelveli": {"x": 77.70, "y": 8.71, "size": 0.8},
}

TRADES = [
    {"trade": "Electrician (Domestic)", "short": "Electrician", "sector": "Electrical and Power", "nco": "7411.0100", "qp": "ELE/Q4601", "nsqf": 4, "base": 60, "growth": 0.02},
    {"trade": "Assistant Electrician", "short": "Asst. Electrician", "sector": "Electrical and Power", "nco": "7411.0200", "qp": "ELE/Q4602", "nsqf": 3, "base": 35, "growth": 0.04},
    {"trade": "Solar PV Installer", "short": "Solar PV", "sector": "Electrical and Power", "nco": "7411.0601", "qp": "SGJ/Q0101", "nsqf": 4, "base": 20, "growth": 0.22},
    {"trade": "Lineman (LT)", "short": "Lineman", "sector": "Electrical and Power", "nco": "7413.0101", "qp": "PSS/Q0101", "nsqf": 4, "base": 15, "growth": 0.05},
    {"trade": "Electrical Panel Assembler", "short": "Panel Assembler", "sector": "Electrical and Power", "nco": "8212.0300", "qp": "ELE/Q3101", "nsqf": 3, "base": 18, "growth": 0.06},
    {"trade": "Two-Wheeler Service Technician", "short": "Two-Wheeler", "sector": "Automotive", "nco": "7231.0201", "qp": "ASC/Q1404", "nsqf": 4, "base": 50, "growth": -0.10},
    {"trade": "Four-Wheeler Service Technician", "short": "Four-Wheeler", "sector": "Automotive", "nco": "7231.0101", "qp": "ASC/Q1401", "nsqf": 4, "base": 40, "growth": 0.04},
    {"trade": "EV Service Technician", "short": "EV Technician", "sector": "Automotive", "nco": "7231.0301", "qp": "ASC/Q1416", "nsqf": 4, "base": 14, "growth": 0.38},
    {"trade": "Auto Body Repair Technician", "short": "Auto Body Repair", "sector": "Automotive", "nco": "7213.0201", "qp": "ASC/Q1419", "nsqf": 4, "base": 20, "growth": 0.02},
    {"trade": "Automotive Painter", "short": "Auto Painter", "sector": "Automotive", "nco": "7132.0201", "qp": "ASC/Q1501", "nsqf": 3, "base": 15, "growth": 0.02},
]

SECTORS = ["Electrical and Power", "Automotive"]

WEIGHTS = {"portal": 0.35, "ncs": 0.30, "industry": 0.20, "eshram": 0.15}
PORTAL_DUPLICATION = 1.4
NCS_COVERAGE = 0.6

BANDS = [
    ("Shortage", None, 0.6),
    ("Watch (falling)", 0.6, 0.8),
    ("Balanced", 0.8, 1.2),
    ("Watch (rising)", 1.2, 1.5),
    ("Oversupply", 1.5, None),
]

GROWTH_BOOST = [
    ("EV Service Technician", ["Chennai", "Coimbatore", "Krishnagiri"], 0.15),
    ("Solar PV Installer", ["Tirunelveli", "Madurai"], 0.12),
]

SUPPLY_STORIES = [
    ("EV Service Technician", ["Chennai", "Coimbatore", "Krishnagiri"], 0.38),
    ("EV Service Technician", None, 0.50),
    ("Solar PV Installer", ["Tirunelveli", "Madurai"], 0.42),
    ("Solar PV Installer", None, 0.52),
    ("Electrician (Domestic)", ["Madurai", "Tiruchirappalli"], 2.0),
    ("Two-Wheeler Service Technician", ["Salem", "Tirunelveli"], 1.85),
    ("Two-Wheeler Service Technician", None, 1.50),
    ("Four-Wheeler Service Technician", ["Chennai"], 1.32),
    ("Auto Body Repair Technician", ["Tiruppur"], 0.74),
]

REALLOCATION = {"donor_keep": 1.1, "receiver_target": 1.0, "block": 10}

ALIASES = {
    "Electrician (Domestic)": ["Electrician", "Domestic Electrician", "Wireman", "Electrical Fitter", "House Wiring Technician"],
    "Assistant Electrician": ["Assistant Electrician", "Electrician Helper", "Asst Electrician", "Junior Electrician"],
    "Solar PV Installer": ["Solar PV Installer", "Solar Panel Fitter", "Solar Technician", "Suryamitra", "Rooftop Solar Installer"],
    "Lineman (LT)": ["Lineman", "LT Lineman", "Line Man", "Distribution Lineman"],
    "Electrical Panel Assembler": ["Panel Assembler", "Electrical Panel Assembler", "Control Panel Wireman", "Switchboard Assembler"],
    "Two-Wheeler Service Technician": ["Two-Wheeler Service Technician", "Bike Mechanic", "Two Wheeler Mechanic", "Motorcycle Mechanic", "Scooter Mechanic"],
    "Four-Wheeler Service Technician": ["Four-Wheeler Service Technician", "Car Mechanic", "Auto Mechanic", "Four Wheeler Technician"],
    "EV Service Technician": ["EV Service Technician", "EV Mechanic", "Electric Vehicle Technician", "EV Battery Technician", "E-Rickshaw Mechanic"],
    "Auto Body Repair Technician": ["Auto Body Repair Technician", "Denter", "Denting Technician", "Body Shop Technician"],
    "Automotive Painter": ["Automotive Painter", "Car Painter", "Auto Paint Technician", "Spray Painter Automobile"],
}

MATCH_MINIMUM = 70
