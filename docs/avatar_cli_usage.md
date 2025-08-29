# Avatar Intelligence Pipeline - CLI Usage Guide

## Important: Command-Line Argument Format

When using the avatar intelligence pipeline CLI, **DO NOT use quotes** around multi-word arguments. The script uses `nargs='*'` which handles multiple words automatically.

## Commands

### 1. Initialize All Profiles
Initialize avatar profiles for all people with sufficient message data:

```bash
python3 src/avatar_intelligence_pipeline.py \
  --command init-all \
  --min-messages 1000 \
  --password YOUR_NEO4J_PASSWORD
```

### 2. Initialize Single Person
Initialize a profile for a specific person:

```bash
# For single-word names
python3 src/avatar_intelligence_pipeline.py \
  --command init-person \
  --person John \
  --password YOUR_NEO4J_PASSWORD

# For multi-word names (NO QUOTES!)
python3 src/avatar_intelligence_pipeline.py \
  --command init-person \
  --person Gay Vietzke \
  --password YOUR_NEO4J_PASSWORD
```

### 3. Generate Avatar Response
Generate an avatar prompt for a person:

```bash
# Basic generation
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person Gay Vietzke \
  --password YOUR_NEO4J_PASSWORD

# With conversation partners (multiple partners supported)
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person Gay Vietzke \
  --partners Keifth Zotti Ryan Mastro \
  --password YOUR_NEO4J_PASSWORD

# With topic
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person Gay Vietzke \
  --partners Keifth Zotti \
  --topic weekend plans \
  --password YOUR_NEO4J_PASSWORD

# Complex multi-word example
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person clAIre Russell \
  --partners Virginia Koch Nanna Poptart \
  --topic holiday dinner planning \
  --password YOUR_NEO4J_PASSWORD
```

### 4. Get System Statistics
Check the status of the avatar system:

```bash
python3 src/avatar_intelligence_pipeline.py \
  --command stats \
  --password YOUR_NEO4J_PASSWORD
```

## Common Issues and Solutions

### Issue: "No person found" error with quotes
**Problem**: Using quotes around names causes them to be included in the search string
```bash
# WRONG - quotes become part of the name
--person "Gay Vietzke"  # Searches for '"Gay Vietzke"' (with quotes)

# CORRECT - no quotes needed
--person Gay Vietzke    # Searches for 'Gay Vietzke'
```

### Issue: Special characters in names
For names with special characters or unusual formatting:
```bash
# This works fine without quotes
--person clAIre Russell

# Email addresses work too
--person v.h.koch@me.com
```

### Issue: Names with apostrophes
Names with apostrophes should be escaped or avoided:
```bash
# If a name has an apostrophe, you may need to escape it
--person O\'Brien

# Or use the person's ID or phone number instead
--person person_12345678
```

## Optional Arguments

- `--neo4j-uri`: Neo4j connection URI (default: bolt://localhost:7687)
- `--username`: Neo4j username (default: neo4j)
- `--password`: Neo4j password (required)
- `--min-messages`: Minimum messages for init-all (default: 50)

## Examples of Full Commands

### Example 1: Initialize and generate for a new person
```bash
# First, check if they have enough messages
python3 src/avatar_intelligence_pipeline.py --command stats --password M@ry1and2

# Initialize their profile
python3 src/avatar_intelligence_pipeline.py \
  --command init-person \
  --person Bobby Alicea \
  --password M@ry1and2

# Generate an avatar prompt
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person Bobby Alicea \
  --topic work project updates \
  --password M@ry1and2
```

### Example 2: Batch initialization and testing
```bash
# Initialize all people with 500+ messages
python3 src/avatar_intelligence_pipeline.py \
  --command init-all \
  --min-messages 500 \
  --password M@ry1and2

# Test generation for multiple people
for person in "Gay Vietzke" "Bobby Alicea" "Laura Dichter"; do
  echo "Generating for $person..."
  python3 src/avatar_intelligence_pipeline.py \
    --command generate \
    --person $person \
    --password M@ry1and2
done
```

## Debugging

If you encounter issues, the script now includes debug logging that shows:
- The exact identifier being searched for
- The raw arguments received
- The processed person name

This helps diagnose parsing issues with command-line arguments.
