# Person Entity Deduplication Feature

## Overview

The Person Entity Deduplication feature provides comprehensive functionality to identify, merge, and track duplicate person entities in a Neo4j knowledge graph while maintaining original mapping for future data loads and updates.

## Key Features

- **Intelligent Duplicate Detection**: Uses fuzzy string matching, exact email matching, and relationship similarity analysis
- **Safe Merging Process**: Preserves all relationships and properties during entity consolidation
- **Original Mapping Preservation**: Maintains tracking of original entity IDs for future data loads
- **Configurable Thresholds**: Adjustable confidence levels for automatic vs manual merge decisions
- **Interactive CLI**: User-friendly command-line interface for managing the deduplication process
- **Comprehensive Testing**: Full test suite ensuring reliability and correctness
- **Audit Trail**: Complete logging and tracking of all merge operations

## Installation

### Dependencies

Install the required dependencies for this feature:

```bash
pip install -r requirements_deduplication.txt
```

### Core Dependencies
- `neo4j>=5.0.0` - Neo4j database driver
- `fuzzywuzzy>=0.18.0` - Fuzzy string matching
- `python-levenshtein>=0.20.0` - Enhanced fuzzy matching performance
- `click>=8.0.0` - CLI framework
- `rich>=12.0.0` - Beautiful terminal output
- `questionary>=1.10.0` - Interactive prompts

## Quick Start

### 1. Basic Usage

```python
from deduplication import PersonDeduplicationEngine
from deduplication.deduplication_config import get_config

# Load configuration
config = get_config('development')

# Initialize engine
engine = PersonDeduplicationEngine(
    config.NEO4J_URI,
    config.NEO4J_USER, 
    config.NEO4J_PASSWORD
)

# Run deduplication
results = engine.run_deduplication(
    auto_merge_threshold=0.9,
    interactive_mode=True
)

print(f"Merged {results['auto_merges']} entities")
engine.close()
```

### 2. Command Line Interface

The CLI provides an easy way to manage deduplication:

```bash
# Run complete deduplication process
python3 deduplication/deduplication_cli.py run --interactive

# Review candidates without merging
python3 deduplication/deduplication_cli.py review --threshold 0.8

# Show database statistics
python3 deduplication/deduplication_cli.py stats

# Look up canonical ID for original entity
python3 deduplication/deduplication_cli.py lookup "original_entity_123"

# Validate configuration
python3 deduplication/deduplication_cli.py validate
```

## Configuration

### Environment Variables

Set these environment variables for database connection:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export AVATAR_ENGINE_ENV="development"
```

### Configuration Settings

Key configurable parameters in `deduplication_config.py`:

- `NAME_SIMILARITY_THRESHOLD`: Minimum similarity score for name matching (0.8)
- `AUTO_MERGE_THRESHOLD`: Confidence threshold for automatic merging (0.9)
- `EMAIL_EXACT_MATCH_WEIGHT`: Weight given to exact email matches (0.9)
- `INTERACTIVE_MODE`: Whether to prompt for manual review (True)

### Environment-Specific Configurations

- **Development**: Verbose logging, interactive mode enabled, backups created
- **Production**: Conservative thresholds, minimal logging, batch processing
- **Testing**: Minimal output, no backups, fast processing

## Matching Algorithm

### Matching Strategies

1. **Name Similarity Matching**
   - Uses fuzzy string matching with configurable threshold
   - Supports phonetic matching (Soundex/Metaphone)
   - Nickname expansion (Bob → Robert)

2. **Email Exact Matching**
   - High-confidence matches for identical email addresses
   - Case-insensitive comparison

3. **Relationship Similarity**
   - Analyzes shared relationship patterns
   - Jaccard similarity for relationship types

### Confidence Scoring

The system calculates confidence scores based on:
- Name similarity (weighted at 70%)
- Email exact matches (weighted at 90%)
- Relationship patterns (weighted at 30%)

### Merge Decision Process

```
Confidence >= 0.9  → Automatic merge
0.6 <= Confidence < 0.9  → Manual review required
Confidence < 0.6  → No action
```

## Database Schema

### Entity Mapping Node

The system creates `EntityMapping` nodes to track merges:

```cypher
(:EntityMapping {
  mapping_id: "uuid",
  original_entity_id: "original_id",
  canonical_entity_id: "merged_to_id", 
  merge_timestamp: datetime(),
  merge_confidence: 0.95,
  merge_reasons: ["name_similarity_0.92", "email_exact_match"],
  source_system: "avatar_engine_deduplication"
})
```

### Constraints

Add these constraints to your Neo4j database:

```cypher
CREATE CONSTRAINT entity_mapping_id IF NOT EXISTS 
FOR (m:EntityMapping) REQUIRE m.mapping_id IS UNIQUE;

CREATE INDEX entity_mapping_original IF NOT EXISTS 
FOR (m:EntityMapping) ON (m.original_entity_id);

CREATE INDEX entity_mapping_canonical IF NOT EXISTS 
FOR (m:EntityMapping) ON (m.canonical_entity_id);
```

## Merge Process

### 1. Entity Selection

The system selects the canonical entity based on:
- Presence of email address (preferred)
- Number of complete properties (more is better)
- Relationship count (more connections preferred)

### 2. Property Merging

Properties are merged using configurable strategies:
- `prefer_longer`: Keep the longer string value
- `prefer_non_null`: Keep the non-null value
- `concatenate`: Combine both values
- `prefer_earlier`/`prefer_later`: Choose by date

### 3. Relationship Consolidation

Relationships are handled based on type:
- `WORKS_FOR`: Remove duplicates, keep most recent
- `KNOWS`: Consolidate similar relationships
- `FAMILY_OF`: Preserve all relationships

### 4. Mapping Creation

Creates permanent mapping record linking original → canonical entity IDs.

## Usage Examples

### Programmatic Usage

```python
# Find potential duplicates
matcher = PersonEntityMatcher(driver)
candidates = matcher.find_potential_duplicates()

# Review specific candidate
for candidate in candidates:
    if candidate.is_high_confidence:
        print(f"High confidence match: {candidate.entity1.name} <-> {candidate.entity2.name}")
        print(f"Confidence: {candidate.confidence_score:.2f}")
        print(f"Reasons: {candidate.match_reasons}")

# Merge entities
merger = PersonEntityMerger(driver)
canonical_id = merger.merge_entities(candidate, preserve_original_mapping=True)

# Look up mappings later
canonical_id = engine.get_mapping_by_original_id("original_123")
```

### CLI Examples

```bash
# Interactive deduplication with custom threshold
python3 deduplication/deduplication_cli.py run --interactive --threshold 0.85

# Batch processing in production
python3 deduplication/deduplication_cli.py --env production run --no-interactive

# Review only high-confidence candidates
python3 deduplication/deduplication_cli.py review --threshold 0.9

# Get statistics
python3 deduplication/deduplication_cli.py stats
```

## Testing

### Running Tests

```bash
# Run all tests
python3 -m pytest deduplication/test_person_deduplication.py -v

# Run specific test category
python3 -m pytest deduplication/test_person_deduplication.py::TestPersonEntityMatcher -v

# Run with coverage
python3 -m pytest deduplication/test_person_deduplication.py --cov=person_entity_deduplication
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Configuration Tests**: Config validation and environment testing
- **Scenario Tests**: Real-world deduplication scenarios

## Performance Considerations

### Scalability

- **Batch Processing**: Configurable batch sizes for large datasets
- **Memory Management**: Efficient entity loading and comparison
- **Database Optimization**: Indexed lookups and optimized queries

### Performance Tips

1. **Database Indexing**: Ensure proper indexes on Person.name, Person.email
2. **Batch Size Tuning**: Adjust `BATCH_SIZE` based on available memory
3. **Threshold Optimization**: Higher thresholds = fewer candidates to review
4. **Relationship Caching**: Cache relationship patterns for repeated runs

## Troubleshooting

### Common Issues

1. **Memory Issues with Large Datasets**
   ```python
   # Reduce batch size in config
   config.BATCH_SIZE = 500
   ```

2. **Too Many False Positives**
   ```python
   # Increase similarity thresholds
   config.NAME_SIMILARITY_THRESHOLD = 0.85
   config.AUTO_MERGE_THRESHOLD = 0.95
   ```

3. **Database Connection Issues**
   ```bash
   # Verify connection
   python3 deduplication/deduplication_cli.py validate
   ```

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

## Backup and Recovery

### Pre-Merge Backup

The system can automatically create backups before merging:

```python
config.CREATE_BACKUP_BEFORE_MERGE = True
config.BACKUP_RETENTION_DAYS = 30
```

### Manual Backup

```cypher
// Export person entities and relationships
MATCH (p:Person)-[r]-(other)
RETURN p, r, other
```

### Recovery Process

If you need to reverse a merge:

1. Find the mapping record
2. Recreate the original entity
3. Restore original relationships
4. Delete the mapping record

## Integration with Data Loads

### New Data Loading

When loading new data, check for existing mappings:

```python
# Before creating new person entity
canonical_id = engine.get_mapping_by_original_id(source_person_id)
if canonical_id:
    # Use canonical entity instead of creating new one
    person_id = canonical_id
else:
    # Create new entity
    person_id = create_new_person_entity(person_data)
```

### Data Update Process

1. Check for existing mapping
2. Update canonical entity if mapping exists
3. Otherwise, update original entity
4. Run periodic deduplication to catch new duplicates

## Future Enhancements

### Planned Features

- **Machine Learning Integration**: Use embeddings for semantic similarity
- **Bulk Import Optimization**: Streaming deduplication for large imports
- **Advanced Relationship Analysis**: Deep relationship pattern matching
- **Multi-Entity Type Support**: Extend beyond person entities
- **REST API Interface**: Web service for deduplication operations

### Contributing

When contributing to this feature:

1. Follow the existing code structure
2. Add comprehensive tests for new functionality
3. Update configuration options as needed
4. Document new parameters and usage
5. Test with realistic datasets

## Support and Maintenance

### Monitoring

Monitor these metrics in production:
- Merge success rate
- False positive rate
- Processing time per batch
- Memory usage during processing

### Regular Maintenance

- Review and tune threshold parameters
- Archive old mapping records
- Monitor database performance
- Update nickname mappings as needed

## License

This feature is part of the Avatar-Engine project and follows the same licensing terms.
