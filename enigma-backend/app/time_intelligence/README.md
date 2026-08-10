# Time Intelligence

Time Intelligence provides domain-independent timezone analysis and customer time context for Enigma.

## Purpose

Time Intelligence enables Enigma to:
- Understand customer time context relative to Enigma's local time
- Analyze deadline feasibility considering timezone differences
- Determine availability windows for communication
- Calculate working hour overlap
- Handle DST (Daylight Saving Time) changes
- Provide business intelligence for time-sensitive decisions

## Architecture

### Core Components

- **contracts.py**: Core data structures and enums
- **timezone_service.py**: Timezone conversion and DST handling
- **customer_time.py**: Customer time context and timezone inference
- **deadline_analysis.py**: Deadline feasibility and risk analysis
- **availability.py**: Availability window analysis
- **working_hours.py**: Working hour overlap analysis
- **registry.py**: Timezone mappings for countries, cities, and platforms

### Design Principles

1. **No Fake Timezones**: Unknown timezone ≠ guessed timezone
2. **Priority-Based Inference**: Explicit > Location > Platform > Country > Unknown
3. **DST Awareness**: Handles daylight saving time changes
4. **Domain Independence**: Can be used across all Enigma domains
5. **No Silent Failures**: All timezone errors are explicit

## Timezone Inference Priority

```
Explicit customer timezone
        ↓
Customer location
        ↓
Known platform/location metadata
        ↓
Country inference (low confidence)
        ↓
UNKNOWN
```

## Usage Examples

### Basic Time Conversion

```python
from app.time_intelligence.timezone_service import TimezoneService

service = TimezoneService(enigma_timezone="Africa/Cairo")

conversion = service.convert_time(
    time_str="2026-08-10T17:00:00",
    from_timezone="America/Toronto",
    to_timezone="Africa/Cairo",
)

print(f"Customer time: {conversion.original_time}")
print(f"Enigma time: {conversion.target_time}")
print(f"Offset: {conversion.offset_hours:+.1f} hours")
```

### Customer Time Context

```python
from app.time_intelligence.customer_time import CustomerTimeAnalyzer
from app.time_intelligence.contracts import TimezoneInfo, TimezoneSource

analyzer = CustomerTimeAnalyzer()

customer_tz = TimezoneInfo(
    timezone="America/Toronto",
    source=TimezoneSource.EXPLICIT,
    confidence=1.0,
)

context = analyzer.create_customer_time_context(customer_tz)

print(f"Customer time: {context.customer_current_time}")
print(f"Enigma time: {context.enigma_current_time}")
print(f"UTC time: {context.utc_time}")
```

### Deadline Analysis

```python
from app.time_intelligence.deadline_analysis import DeadlineAnalyzer

analyzer = DeadlineAnalyzer()

analysis = analyzer.analyze_deadline(
    deadline="2026-08-10T17:00:00",
    deadline_timezone="America/Toronto",
)

print(f"Risk: {analysis.risk}")
print(f"Feasible: {analysis.is_feasible}")
print(f"Reason: {analysis.reason}")
```

### Working Hour Overlap

```python
from app.time_intelligence.working_hours import WorkingHoursAnalyzer, WorkingHours

analyzer = WorkingHoursAnalyzer()

customer_hours = WorkingHours(
    start_hour=9,
    end_hour=18,
    timezone="America/Toronto",
)

overlap = analyzer.analyze_overlap(customer_hours)

print(f"Overlap: {overlap.overlap_hours} hours")
print(f"Status: {overlap.status}")
```

## Supported Regions

### Countries
- Egypt, Canada, USA, UK, Australia, India, China
- Germany, France, Japan, UAE, Saudi Arabia
- Brazil, Mexico, Argentina, South Africa
- And many more (see registry.py)

### Cities
- Toronto, Montreal, Vancouver, New York, Los Angeles
- London, Paris, Berlin, Rome, Madrid
- Cairo, Dubai, Tokyo, Sydney, Mumbai
- And many more (see registry.py)

## Integration with Pipeline

Time Intelligence integrates with the pipeline at:

1. **Work Specification**: Customer timezone inference
2. **Decision**: Deadline feasibility analysis
3. **Execution Planning**: Availability window analysis
4. **Client Communication**: Optimal timing recommendations

## Testing

Tests cover:
- Timezone conversion
- DST handling
- Country ambiguity
- Unknown timezone handling
- Working hour overlap
- Deadline risk analysis
- Weekend differences
- Customer/Enigma offset

## Negative Tests

- Unknown timezone ≠ guessed timezone
- Invalid timezone ≠ silent fallback
- DST changes ≠ incorrect offset
- Country inference ≠ high confidence
