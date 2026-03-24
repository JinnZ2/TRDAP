# TRDAP
Transport registration data access protocol

This is an Internet-Draft style document that could theoretically submit to the IETF or use as a blueprint for a real standards effort.

📄 TRDAP: Transport Registration Data Access Protocol

draft-trdap-emergency-transport-00

---

Abstract

This document describes TRDAP (Transport Registration Data Access Protocol), a lightweight, decentralized protocol for resource discovery and coordination between transportation hubs during emergencies and network outages. TRDAP enables hubs to share standardized resource data (fuel, medical supplies, transport capacity, shelter) over mesh networks including LoRa, Meshtastic, and ad-hoc WiFi. The protocol is inspired by the Internet's RDAP but optimized for intermittent connectivity and low-bandwidth environments.

---

1. Introduction

Transportation hubs (airports, train stations, ports, bus terminals) face critical coordination challenges during emergencies. Existing solutions rely on centralized servers and continuous internet connectivity—exactly what fails in disasters. TRDAP addresses this gap by providing:

· Decentralized resource discovery without central servers
· Standardized data formats for cross-agency interoperability
· Mesh-friendly design supporting LoRa, Meshtastic, and ad-hoc networks
· Emergency-specific features like urgency levels and priority routing

1.1. Relationship to Existing Standards

TRDAP draws inspiration from:

· RDAP (RFC 9082-9083) : Hierarchical query resolution model 
· IETF ECRIT framework : Emergency context resolution 
· NENA i3 / NG9-1-1 standards: Emergency data object formats 
· OASIS Emergency Interoperability: Information exchange patterns 

---

2. Terminology and Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

Transport Hub: A physical facility (airport, train station, port, bus terminal) participating in the TRDAP network.

Resource: Any asset that can be shared between hubs, including fuel, medical supplies, transport vehicles, shelter capacity, food, water, and personnel.

Mesh Network: A communication network where each hub can relay messages for others, requiring no centralized infrastructure.

Bootstrap Hub: A hub that maintains a registry of other hubs in its region and helps new hubs join the network.

---

3. Protocol Overview

TRDAP operates over UDP (preferred) or TCP, with a maximum message size of 512 bytes to accommodate LoRa and other low-bandwidth mesh technologies. Messages are JSON-encoded and follow a request-response pattern with optional broadcast.

```
+----------------+     Mesh Network     +----------------+
|   Hub A        |◄─────broadcast──────►|   Hub B        |
| - QUERY fuel   |                      | - RESPONSE fuel|
| - knows B,C    |◄─────relay──────────►| - knows D,E    |
+----------------+                      +----------------+
         │                                       │
         │ unicast                               │ unicast
         ▼                                       ▼
+----------------+                      +----------------+
|   Hub C        |                      |   Hub D        |
| - RESPONSE fuel|                      | - QUERY relay  |
+----------------+                      +----------------+
```

3.1. Message Format

All TRDAP messages share a common header structure:

```json
{
  "protocol": "TRDAP/1.0",
  "message_id": "uuid-v4-string",
  "type": "QUERY|RESPONSE|ANNOUNCE|PING|SYNC|REDIRECT|ERROR",
  "from": "hub-identifier",
  "to": "hub-identifier|ALL",
  "timestamp": "2025-03-05T14:30:00Z",
  "ttl": 3
}
```

---

4. Core Message Types

4.1. QUERY

Used to request resource information from other hubs.

```json
{
  "protocol": "TRDAP/1.0",
  "message_id": "a7f3d9e2-1a45-4b88-9c34-a82b1c4d7e2f",
  "type": "QUERY",
  "from": "JFK",
  "to": "ALL",
  "timestamp": "2025-03-05T14:30:00Z",
  "ttl": 3,
  "query": {
    "resource_type": "fuel_jet_a",
    "resource_category": "fuel",
    "location": {
      "type": "radius",
      "center": {"lat": 40.6413, "lon": -73.7781},
      "radius_km": 100
    },
    "urgency": "critical|high|medium|low",
    "min_quantity": 1000,
    "unit": "gallons",
    "response_limit": 5
  }
}
```

4.2. RESPONSE

Provides resource data in response to a query.

```json
{
  "protocol": "TRDAP/1.0",
  "message_id": "a8e3b5d2-3b67-4a12-8f45-c7d8e2f4a6b8",
  "in_response_to": "a7f3d9e2-1a45-4b88-9c34-a82b1c4d7e2f",
  "type": "RESPONSE",
  "from": "EWR",
  "to": "JFK",
  "timestamp": "2025-03-05T14:30:05Z",
  "data": {
    "hub": {
      "id": "EWR",
      "type": "airport",
      "name": "Newark Liberty International",
      "location": {"lat": 40.6895, "lon": -74.1745},
      "status": "limited",
      "last_seen": "2025-03-05T14:30:05Z"
    },
    "resources": [
      {
        "resource_id": "fuel-ewr-001",
        "type": "fuel_jet_a",
        "category": "fuel",
        "quantity": 25000,
        "unit": "gallons",
        "status": "available",
        "updated": "2025-03-05T14:15:00Z",
        "quality": "premium",
        "location_within_hub": "Terminal B, Gate 23"
      }
    ],
    "needs": [
      {
        "resource_type": "medical_kits",
        "quantity_needed": 50,
        "unit": "units",
        "urgency": "high"
      }
    ],
    "routes": [
      {
        "from_hub": "EWR",
        "to_hub": "JFK",
        "mode": "road",
        "status": "open",
        "estimated_minutes": 45,
        "last_verified": "2025-03-05T14:00:00Z"
      }
    ]
  }
}
```

4.3. ANNOUNCE

Used for presence discovery and capability advertisement.

```json
{
  "protocol": "TRDAP/1.0",
  "message_id": "b2c4d6e8-f0a1-2b3c-4d5e-6f7a8b9c0d1e",
  "type": "ANNOUNCE",
  "from": "LGA",
  "to": "ALL",
  "timestamp": "2025-03-05T14:35:00Z",
  "ttl": 2,
  "data": {
    "hub": {
      "id": "LGA",
      "type": "airport",
      "location": {"lat": 40.7769, "lon": -73.8740},
      "status": "operational"
    },
    "capabilities": ["query", "relay", "storage"],
    "resource_summary": {
      "fuel_jet_a": {"available": true},
      "medical_kits": {"available": true},
      "buses": {"available": false}
    },
    "bootstrap": true
  }
}
```

4.4. REDIRECT

Used to direct queries to hubs with better knowledge, mirroring RDAP's redirection model.

```json
{
  "protocol": "TRDAP/1.0",
  "message_id": "c3d5e7f9-a1b2-3c4d-5e6f-7a8b9c0d1e2f",
  "type": "REDIRECT",
  "from": "EWR",
  "to": "JFK",
  "timestamp": "2025-03-05T14:32:00Z",
  "data": {
    "original_query_id": "a7f3d9e2-1a45-4b88-9c34-a82b1c4d7e2f",
    "redirect_to": ["PHL", "BOS"],
    "reason": "better_coverage",
    "ttl_remaining": 2
  }
}
```

4.5. SYNC

Used for bulk data synchronization between trusted hubs.

```json
{
  "protocol": "TRDAP/1.0",
  "message_id": "d4e6f8a0-b1c2-3d4e-5f6a-7b8c9d0e1f2a",
  "type": "SYNC",
  "from": "JFK",
  "to": "EWR",
  "timestamp": "2025-03-05T14:40:00Z",
  "data": {
    "full_update": false,
    "since": "2025-03-05T14:00:00Z",
    "resources": [...],  // Array of resource records
    "routes": [...],      // Array of route records
    "peers": ["LGA", "PHL", "BOS"]
  }
}
```

---

5. Resource Taxonomy and Naming

TRDAP uses a hierarchical resource naming system to ensure interoperability across different hub types and regions.

5.1. Resource Categories

```
resource
├── fuel
│   ├── aviation
│   │   ├── jet_a
│   │   ├── jet_a1
│   │   └── avgas
│   ├── automotive
│   │   ├── gasoline_87
│   │   ├── gasoline_89
│   │   ├── gasoline_93
│   │   ├── diesel
│   │   └── biodiesel
│   ├── marine
│   │   ├── marine_diesel
│   │   └── bunker_fuel
│   └── rail
│       ├── diesel_rail
│       └── electric_capacity
├── transport
│   ├── vehicles
│   │   ├── buses
│   │   ├── ambulances
│   │   ├── shuttles
│   │   ├── trucks
│   │   └── vans
│   ├── rail
│   │   ├── locomotives
│   │   ├── passenger_cars
│   │   └── freight_cars
│   ├── water
│   │   ├── ferries
│   │   ├── tugboats
│   │   └── barges
│   └── air
│       ├── helicopters
│       └── cargo_planes
├── medical
│   ├── supplies
│   │   ├── trauma_kits
│   │   ├── ventilators
│   │   ├── oxygen_tanks
│   │   └── medications
│   ├── personnel
│   │   ├── doctors
│   │   ├── nurses
│   │   └── paramedics
│   └── facilities
│       ├── treatment_areas
│       └── isolation_units
├── food
│   ├── water
│   │   ├── bottled
│   │   └── bulk_tanks
│   ├── meals
│   │   ├── hot
│   │   ├── mres
│   │   └── shelf_stable
│   └── supplies
│       ├── infant_formula
│       └── pet_food
├── shelter
│   ├── space
│   │   ├── waiting_areas
│   │   ├── conference_rooms
│   │   └── parking_garages
│   ├── supplies
│   │   ├── blankets
│   │   ├── cots
│   │   └── hygiene_kits
│   └── support
│       ├── generators
│       ├── lighting
│       └── heaters
├── power
│   ├── generators
│   ├── fuel_cells
│   ├── battery_banks
│   └── solar_units
└── personnel
    ├── operations
    │   ├── coordinators
    │   └── communicators
    ├── technical
    │   ├── mechanics
    │   └── electricians
    └── support
        ├── volunteers
        └── security
```

5.2. Resource Status Values

Resources MUST have one of the following status values:

Status Description
available Resource is fully available for sharing
limited Resource is available but quantities are low
critical Resource is nearly depleted
depleted Resource is exhausted
reserved Resource is committed to specific use
contaminated Resource is present but unsafe (e.g., contaminated fuel)

5.3. Hub Types

Hubs MUST identify their type using these standardized values:

Hub Type Description
airport Commercial or general aviation airport
train_station Passenger or freight rail terminal
bus_terminal Bus station or transit center
port Maritime port or harbor
highway_rest Highway rest area or service plaza
rail_yard Rail maintenance or storage yard
ferry_terminal Ferry landing or terminal
heliport Helicopter landing facility

---

6. Discovery and Bootstrap

6.1. Discovery Methods

TRDAP implementations SHOULD support multiple discovery methods in order of preference:

1. Radio mesh (Meshtastic, LoRa): Primary method for off-grid operation
2. WiFi ad-hoc: When available but internet is down
3. Bluetooth Low Energy: Short-range discovery
4. Audio encoding: DTMF or modem tones for extreme cases
5. Optical: Light pulses/Morse code for visual discovery

6.2. Bootstrap Process

When a hub joins the network for the first time:

1. Listen on all available interfaces for ANNOUNCE messages (minimum 5 minutes)
2. If peers discovered:
   · Request SYNC from nearest peer
   · Update neighborhood tables
3. If no peers discovered:
   · Become a bootstrap hub
   · Begin broadcasting ANNOUNCE at higher power/longer interval
   · Maintain registry of hubs that later join

6.3. Neighborhood Gradient

Hubs maintain knowledge of their "neighborhood" in concentric tiers:

· Tier 1 (direct radio range): 0-5 km
· Tier 2 (one hop): 5-20 km
· Tier 3 (two hops): 20-50 km

This gradient enables efficient routing without full network maps.

---

7. Query Resolution

7.1. Local Resolution

When a hub receives a QUERY:

1. Check local resources first
2. If match found, send RESPONSE directly to query originator
3. If no match, decrement TTL and forward to known peers

7.2. Redirection

If a hub knows of another hub with better information (e.g., regional resource database), it MAY send a REDIRECT instead of forwarding the query.

7.3. Response Aggregation

Query originators SHOULD:

· Collect responses for a configurable time window (default: 30 seconds)
· Deduplicate responses from the same hub
· Sort by relevance (distance, quantity, freshness)

7.4. Urgency Handling

QUERY messages include an urgency field that affects forwarding behavior:

Urgency Forwarding Behavior
critical Flood network immediately, ignore TTL limits
high Forward to all known peers
medium Forward only to hubs likely to have resource
low Cache query, forward during next scheduled sync

---

8. Security Considerations

8.1. Threat Model

TRDAP operates in environments where:

· Physical access to hubs may be compromised
· Radio communications can be intercepted
· False information could cause resource misallocation

8.2. Security Requirements

Implementations MUST:

1. Encrypt all communications using TLS or equivalent when available
2. Support HMAC signatures for message authentication in low-bandwidth environments
3. Validate hub identities through pre-shared keys or certificate exchange
4. Rate-limit announcements to prevent denial-of-service
5. Implement message expiration to prevent replay attacks

8.3. Authentication

Hubs SHOULD establish trust relationships through:

· Pre-deployment key exchange for known agencies
· Certificate chains for hierarchical trust
· Web of trust for ad-hoc relationships

8.4. Privacy

Resource information may reveal sensitive operational data. Implementations SHOULD:

· Support anonymized queries for sensitive resources
· Allow hubs to mark resources as "private" (respond only to authenticated peers)
· Encrypt all stored data at rest

---

9. IANA Considerations

This document requests IANA to establish a new registry:

9.1. TRDAP Resource Types Registry

IANA is requested to create a registry for TRDAP resource types with the following subregistries:

· Resource Categories: fuel, transport, medical, food, shelter, power, personnel
· Resource Status Values: available, limited, critical, depleted, reserved, contaminated
· Hub Types: airport, train_station, bus_terminal, port, highway_rest, rail_yard, ferry_terminal, heliport

9.2. Registration Policy

New values MUST be documented in a standards-track RFC or by a recognized emergency management standards organization (e.g., NENA, ETSI, OASIS) .

---

10. Acknowledgments

This document borrows concepts from the IETF ECRIT working group's work on emergency registries , the OASIS Emergency Interoperability Member Section , and ongoing work in ETSI and 3GPP on emergency communications .

---

11. References

11.1. Normative References

· [RFC2119] Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119, March 1997.
· [RFC9082] Hollenbeck, S., and A. Newton, "Registration Data Access Protocol (RDAP) Query Format", RFC 9082, June 2021.
· [RFC9083] Hollenbeck, S., and A. Newton, "Registration Data Access Protocol (RDAP) Response Profile", RFC 9083, June 2021.

11.2. Informative References

· [NENAi3] NENA, "NENA i3 Standard for Next-Generation 9-1-1", NENA STA-010.3-2021.
· [ECRIT] IETF, "Emergency Context Resolution with Internet Technologies (ECRIT) Working Group", https://datatracker.ietf.org/wg/ecrit/ .
· [OASIS-EI] OASIS, "Emergency Interoperability Member Section", https://www.oasis-emergency.org/ .
· [ETSI-EMTEL] ETSI, "Emergency Communications (EMTEL)", https://www.etsi.org/committee/emtel .

---

Appendix A: Example Implementations

A.1. Python Minimal Hub

```python
import json
import time
import uuid

class TRDAPHub:
    def __init__(self, hub_id, lat, lon):
        self.hub_id = hub_id
        self.location = (lat, lon)
        self.resources = {}
        self.peers = {}
        
    def query(self, resource_type, radius_km=50):
        query_id = str(uuid.uuid4())
        message = {
            "protocol": "TRDAP/1.0",
            "message_id": query_id,
            "type": "QUERY",
            "from": self.hub_id,
            "to": "ALL",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ttl": 3,
            "query": {
                "resource_type": resource_type,
                "location": {
                    "center": {"lat": self.location[0], "lon": self.location[1]},
                    "radius_km": radius_km
                }
            }
        }
        return self._broadcast(message)
```

---

Appendix B: Deployment Scenarios

B.1. Airport Emergency

During a major weather event:

· JFK loses internet but maintains radio mesh
· Queries for fuel and medical supplies
· EWR responds with available jet fuel
· LGA responds with medical kits
· Port Authority bus terminal offers ground transport

B.2. Regional Coordination

Multiple transportation hubs form a mesh across a metropolitan region:

· Tier 1: Direct radio neighbors
· Tier 2: One-hop relays
· Tier 3: Regional resource coordination

---

Next Steps

This draft provides the foundation. To move toward a real standard:

1. Submit to IETF ECRIT working group for consideration 
2. Coordinate with OASIS Emergency Interoperability for alignment 
3. Engage ETSI EMTEL for European requirements 
4. Develop reference implementation for testing
5. Conduct interoperability testing with multiple hub type
