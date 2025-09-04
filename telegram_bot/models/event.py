from dataclasses import dataclass

@dataclass
class CreateEventDTO:
    name: str
    start_date: str
    start_time: str
    event_type: str
    price_single: str
    price_couple: str
    status: str
    created_at: str

@dataclass
class EventDTO:
    id: str
    name: str
    description: str
    start_date: str
    start_time: str
    end_date: str
    end_time: str
    location: str  
    schedule: str
    event_type: str
    price_single: str
    price_couple: str
    price_include: str
    theme: str
    max_participants: str
    status: str
    participant_commitment: str
    line_rules: str
    place_rules: str
    balance: str
    is_public: bool
    main_group_id: str
    singles_group_id: str
    created_at: str
    updated_at: str