SEED = 2026
HISTORY_MONTHS = 36
HISTORY_END = "2026-09"
FORECAST_MONTHS = 12
WARNING_HORIZON = 6
BACKTEST_MONTHS = 6

SOURCE_NOTE = "Synthetic data modelled on the structure of NCS, PLFS, e-Shram and NCVT."

STATES = {
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Krishnagiri", "Tiruchirappalli"],
    "Karnataka": ["Bengaluru Urban", "Mysuru", "Dharwad", "Tumakuru", "Belagavi"],
    "Delhi": ["New Delhi", "South", "North West", "East", "West"],
    "Uttar Pradesh": ["Lucknow", "Gautam Buddha Nagar", "Kanpur Nagar", "Varanasi", "Ghaziabad"],
}

DISTRICT_SIZE = {
    "Chennai": 1.4, "Coimbatore": 1.1, "Madurai": 0.9, "Krishnagiri": 0.7, "Tiruchirappalli": 0.8,
    "Bengaluru Urban": 1.6, "Mysuru": 0.8, "Dharwad": 0.7, "Tumakuru": 0.7, "Belagavi": 0.8,
    "New Delhi": 0.8, "South": 1.1, "North West": 1.2, "East": 1.0, "West": 1.1,
    "Lucknow": 1.1, "Gautam Buddha Nagar": 1.2, "Kanpur Nagar": 1.0, "Varanasi": 0.8, "Ghaziabad": 1.0,
}

SECTORS = {
    "Electrical and Power": "ELE",
    "Automotive": "ASC",
}

TRADES = [
    {"trade": "Electrician (Domestic)", "sector": "Electrical and Power", "nco": "7411.0100", "qp": "ELE/Q4601", "nsqf": 4, "base": 60, "growth": 0.02},
    {"trade": "Assistant Electrician", "sector": "Electrical and Power", "nco": "7411.0200", "qp": "ELE/Q4602", "nsqf": 3, "base": 35, "growth": 0.04},
    {"trade": "Solar PV Installer", "sector": "Electrical and Power", "nco": "7411.0601", "qp": "SGJ/Q0101", "nsqf": 4, "base": 20, "growth": 0.22},
    {"trade": "Lineman (LT)", "sector": "Electrical and Power", "nco": "7413.0101", "qp": "PSS/Q0101", "nsqf": 4, "base": 15, "growth": 0.05},
    {"trade": "Electrical Panel Assembler", "sector": "Electrical and Power", "nco": "8212.0300", "qp": "ELE/Q3101", "nsqf": 3, "base": 18, "growth": 0.06},
    {"trade": "Two-Wheeler Service Technician", "sector": "Automotive", "nco": "7231.0201", "qp": "ASC/Q1404", "nsqf": 4, "base": 50, "growth": -0.08},
    {"trade": "Four-Wheeler Service Technician", "sector": "Automotive", "nco": "7231.0101", "qp": "ASC/Q1401", "nsqf": 4, "base": 40, "growth": 0.04},
    {"trade": "EV Service Technician", "sector": "Automotive", "nco": "7231.0301", "qp": "ASC/Q1416", "nsqf": 4, "base": 14, "growth": 0.40},
    {"trade": "Auto Body Repair Technician", "sector": "Automotive", "nco": "7213.0201", "qp": "ASC/Q1419", "nsqf": 4, "base": 20, "growth": 0.03},
    {"trade": "Automotive Painter", "sector": "Automotive", "nco": "7132.0201", "qp": "ASC/Q1501", "nsqf": 3, "base": 15, "growth": 0.02},
]

TITLE_ALIASES = {
    "Electrician (Domestic)": ["Electrician", "Domestic Electrician", "Wireman", "House Wiring Electrician", "Electrical Fitter", "Electrician Domestic"],
    "Assistant Electrician": ["Assistant Electrician", "Electrician Helper", "Helper Electrical", "Junior Electrician"],
    "Solar PV Installer": ["Solar PV Installer", "Solar Technician", "Suryamitra", "Solar Panel Installer", "Rooftop Solar Fitter"],
    "Lineman (LT)": ["Lineman", "LT Lineman", "Line Man", "Distribution Lineman", "Electrical Lineman"],
    "Electrical Panel Assembler": ["Electrical Panel Assembler", "Panel Wireman", "Control Panel Assembler", "Switchboard Assembler"],
    "Two-Wheeler Service Technician": ["Two-Wheeler Service Technician", "Bike Mechanic", "Two Wheeler Mechanic", "Motorcycle Mechanic", "Scooter Mechanic"],
    "Four-Wheeler Service Technician": ["Four-Wheeler Service Technician", "Car Mechanic", "Auto Mechanic", "Four Wheeler Technician", "Motor Mechanic Vehicle"],
    "EV Service Technician": ["EV Service Technician", "Electric Vehicle Technician", "EV Mechanic", "EV Battery Technician", "E-Rickshaw Mechanic"],
    "Auto Body Repair Technician": ["Auto Body Repair Technician", "Denter", "Denting Technician", "Body Shop Technician", "Car Body Repairer"],
    "Automotive Painter": ["Automotive Painter", "Car Painter", "Spray Painter Automobile", "Auto Paint Technician"],
}

SOURCES = {
    "portal": {"label": "Job portal postings", "weight": 0.35, "unit": "postings per month"},
    "ncs": {"label": "NCS vacancies", "weight": 0.30, "unit": "vacancies per month"},
    "industry": {"label": "Industry hiring outlook", "weight": 0.20, "unit": "outlook score"},
    "eshram": {"label": "e-Shram registered workers", "weight": 0.15, "unit": "registered workers"},
}

PORTAL_DUPLICATION = 1.4
NCS_COVERAGE = 0.6

STATUS_BANDS = [
    {"status": "Oversupply", "min": 1.5, "max": None},
    {"status": "Watch (rising)", "min": 1.2, "max": 1.5},
    {"status": "Balanced", "min": 0.8, "max": 1.2},
    {"status": "Watch (falling)", "min": 0.6, "max": 0.8},
    {"status": "Shortage", "min": None, "max": 0.6},
]

STATUS_COLOURS = {
    "Oversupply": ("#DCE6F5", "#0B2E59"),
    "Watch (rising)": ("#FFF1D6", "#5C3B00"),
    "Balanced": ("#E3F1E3", "#1E4620"),
    "Watch (falling)": ("#FCE3CF", "#6B2E00"),
    "Shortage": ("#F6D5D5", "#7A1414"),
}

TARGET_RATIO = 1.0

PLANTED_RATIOS = [
    {"trade": "EV Service Technician", "districts": ["Coimbatore", "Krishnagiri", "Bengaluru Urban"], "ratio": 0.35},
    {"trade": "EV Service Technician", "districts": None, "ratio": 0.52},
    {"trade": "Solar PV Installer", "states": ["Uttar Pradesh", "Delhi"], "ratio": 0.42},
    {"trade": "Solar PV Installer", "states": None, "ratio": 0.56},
    {"trade": "Electrician (Domestic)", "districts": ["Madurai", "Kanpur Nagar"], "ratio": 2.3},
    {"trade": "Two-Wheeler Service Technician", "districts": ["Lucknow", "Varanasi", "Mysuru", "Tiruchirappalli"], "ratio": 1.85},
    {"trade": "Two-Wheeler Service Technician", "districts": None, "ratio": 1.55},
]
