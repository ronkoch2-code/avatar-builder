// Avatar Intelligence System - Neo4j Schema
// ============================================
// This file creates the complete schema for the Avatar Intelligence System
// Run these commands in Neo4j Browser or via cypher-shell

// ===================
// CONSTRAINTS
// ===================

CREATE CONSTRAINT avatar_profile_id IF NOT EXISTS 
FOR (cp:CommunicationProfile) REQUIRE cp.id IS UNIQUE;

CREATE CONSTRAINT style_pattern_id IF NOT EXISTS 
FOR (sp:StylePattern) REQUIRE sp.id IS UNIQUE;

CREATE CONSTRAINT relationship_pattern_id IF NOT EXISTS 
FOR (rp:RelationshipPattern) REQUIRE rp.id IS UNIQUE;

CREATE CONSTRAINT signature_phrase_id IF NOT EXISTS 
FOR (sp:SignaturePhrase) REQUIRE sp.id IS UNIQUE;

CREATE CONSTRAINT topic_preference_id IF NOT EXISTS 
FOR (tp:TopicPreference) REQUIRE tp.id IS UNIQUE;

CREATE CONSTRAINT emotional_expression_id IF NOT EXISTS 
FOR (ee:EmotionalExpression) REQUIRE ee.id IS UNIQUE;

CREATE CONSTRAINT temporal_pattern_id IF NOT EXISTS 
FOR (tp:TemporalPattern) REQUIRE tp.id IS UNIQUE;

CREATE CONSTRAINT context_trigger_id IF NOT EXISTS 
FOR (ct:ContextTrigger) REQUIRE ct.id IS UNIQUE;

// ===================
// INDEXES FOR PERFORMANCE
// ===================

CREATE INDEX profile_person_lookup IF NOT EXISTS 
FOR (cp:CommunicationProfile) ON (cp.personId);

CREATE INDEX profile_status_lookup IF NOT EXISTS 
FOR (cp:CommunicationProfile) ON (cp.status);

CREATE INDEX profile_version_lookup IF NOT EXISTS 
FOR (cp:CommunicationProfile) ON (cp.personId, cp.version);

CREATE INDEX style_context_lookup IF NOT EXISTS 
FOR (sp:StylePattern) ON (sp.contextType);

CREATE INDEX relationship_partner_lookup IF NOT EXISTS 
FOR (rp:RelationshipPattern) ON (rp.partnerId);

CREATE INDEX phrase_frequency_lookup IF NOT EXISTS 
FOR (sp:SignaturePhrase) ON (sp.frequency);

CREATE INDEX topic_lookup IF NOT EXISTS 
FOR (tp:TopicPreference) ON (tp.topic);

CREATE INDEX emotion_type_lookup IF NOT EXISTS 
FOR (ee:EmotionalExpression) ON (ee.emotion);

CREATE INDEX temporal_timeframe_lookup IF NOT EXISTS 
FOR (tp:TemporalPattern) ON (tp.timeFrame);

// ===================
// SYSTEM METADATA
// ===================

CREATE (:AvatarSystem {
  id: 'avatar_intelligence_v1',
  version: '1.0',
  deploymentDate: datetime(),
  status: 'active',
  description: 'Avatar Intelligence System for personalized conversation analysis'
});

// ===================
// SAMPLE ANALYSIS QUERIES
// ===================

// Query to get all active communication profiles
// MATCH (cp:CommunicationProfile {status: 'active'})
// RETURN cp.personName, cp.totalMessagesAnalyzed, cp.analysisDate
// ORDER BY cp.totalMessagesAnalyzed DESC;

// Query to get relationship patterns for a specific person
// MATCH (p:Person {name: 'clAIre Russell'})-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
// MATCH (cp)-[:HAS_RELATIONSHIP_PATTERN]->(rp:RelationshipPattern)
// RETURN rp.partnerId, rp.relationshipType, rp.messageCount, 
//        rp.relationshipInference.confidence as confidence
// ORDER BY rp.messageCount DESC;

// Query to get nickname usage for a person
// MATCH (p:Person {name: 'clAIre Russell'})-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
// MATCH (cp)-[:HAS_RELATIONSHIP_PATTERN]->(rp:RelationshipPattern)
// WHERE rp.nicknameUsage.nickname_patterns.has_nicknames = true
// RETURN rp.partnerId, rp.nicknameUsage.partner_nicknames, rp.nicknameUsage.nickname_patterns
// ORDER BY rp.messageCount DESC;

// ===================
// VERIFICATION QUERIES
// ===================

// Check system deployment
// MATCH (sys:AvatarSystem) RETURN sys;

// Count nodes by type
// MATCH (n) RETURN labels(n) as nodeType, count(n) as count ORDER BY count DESC;

// Check constraints
// SHOW CONSTRAINTS;

// Check indexes  
// SHOW INDEXES;

// ===================
// MAINTENANCE QUERIES
// ===================

// Clean up inactive profiles older than 90 days
// MATCH (cp:CommunicationProfile)
// WHERE cp.status = 'inactive' 
//   AND datetime(cp.analysisDate) < datetime() - duration('P90D')
// DETACH DELETE cp;

// Update system statistics
// MATCH (sys:AvatarSystem {id: 'avatar_intelligence_v1'})
// MATCH (cp:CommunicationProfile {status: 'active'})
// WITH sys, count(cp) as activeProfiles
// MATCH (artifact) WHERE artifact:StylePattern OR artifact:RelationshipPattern 
//                     OR artifact:SignaturePhrase OR artifact:TopicPreference
// WITH sys, activeProfiles, count(artifact) as totalArtifacts
// SET sys.totalProfiles = activeProfiles,
//     sys.totalArtifacts = totalArtifacts,
//     sys.lastUpdate = datetime();
