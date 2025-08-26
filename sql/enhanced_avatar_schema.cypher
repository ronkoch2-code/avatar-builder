// Avatar Intelligence System - Enhanced Neo4j Schema with LLM Integration
// =====================================================================
// This schema supports rich personality profiling, semantic analysis, and LLM-generated insights

// ===================
// ENHANCED PERSON PROFILING NODES
// ===================

// Core personality traits from LLM analysis
CREATE CONSTRAINT personality_profile_id IF NOT EXISTS 
FOR (pp:PersonalityProfile) REQUIRE pp.id IS UNIQUE;

// Communication style patterns
CREATE CONSTRAINT communication_style_id IF NOT EXISTS 
FOR (cs:CommunicationStyle) REQUIRE cs.id IS UNIQUE;

// Relationship dynamics
CREATE CONSTRAINT relationship_dynamic_id IF NOT EXISTS 
FOR (rd:RelationshipDynamic) REQUIRE rd.id IS UNIQUE;

// Topic interests and expertise
CREATE CONSTRAINT topic_analysis_id IF NOT EXISTS 
FOR (ta:TopicAnalysis) REQUIRE ta.id IS UNIQUE;

// Emotional patterns
CREATE CONSTRAINT emotional_profile_id IF NOT EXISTS 
FOR (ep:EmotionalProfile) REQUIRE ep.id IS UNIQUE;

// Conversation contexts
CREATE CONSTRAINT conversation_context_id IF NOT EXISTS 
FOR (cc:ConversationContext) REQUIRE cc.id IS UNIQUE;

// LLM analysis sessions
CREATE CONSTRAINT llm_analysis_id IF NOT EXISTS 
FOR (la:LLMAnalysis) REQUIRE la.id IS UNIQUE;

// Semantic embeddings for conversation segments
CREATE CONSTRAINT semantic_cluster_id IF NOT EXISTS 
FOR (sc:SemanticCluster) REQUIRE sc.id IS UNIQUE;

// ===================
// ENHANCED INDEXES FOR PERFORMANCE
// ===================

// Personality profiling indexes
CREATE INDEX personality_big_five_lookup IF NOT EXISTS 
FOR (pp:PersonalityProfile) ON (pp.openness, pp.conscientiousness, pp.extraversion, pp.agreeableness, pp.neuroticism);

CREATE INDEX communication_formality_lookup IF NOT EXISTS 
FOR (cs:CommunicationStyle) ON (cs.formalityLevel, cs.directnessScore);

CREATE INDEX relationship_intimacy_lookup IF NOT EXISTS 
FOR (rd:RelationshipDynamic) ON (rd.intimacyLevel, rd.relationshipType);

CREATE INDEX topic_expertise_lookup IF NOT EXISTS 
FOR (ta:TopicAnalysis) ON (ta.topicCategory, ta.expertiseLevel);

CREATE INDEX emotional_valence_lookup IF NOT EXISTS 
FOR (ep:EmotionalProfile) ON (ep.overallValence, ep.emotionalRange);

CREATE INDEX llm_model_lookup IF NOT EXISTS 
FOR (la:LLMAnalysis) ON (la.model, la.analysisDate);

CREATE INDEX semantic_similarity_lookup IF NOT EXISTS 
FOR (sc:SemanticCluster) ON (sc.similarityThreshold, sc.clusterSize);

// ===================
// EXISTING SCHEMA ENHANCEMENTS
// ===================

// Enhanced CommunicationProfile with LLM insights
CREATE INDEX profile_llm_enhanced_lookup IF NOT EXISTS 
FOR (cp:CommunicationProfile) ON (cp.llmEnhanced, cp.lastLLMAnalysis);

// Enhanced Message with semantic analysis
CREATE INDEX message_semantic_lookup IF NOT EXISTS 
FOR (m:Message) ON (m.sentimentScore, m.emotionalTone);

// ===================
// LLM SYSTEM METADATA
// ===================

CREATE (:LLMSystem {
  id: 'avatar_llm_intelligence_v1',
  version: '1.0',
  supportedModels: ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku'],
  deploymentDate: datetime(),
  status: 'active',
  description: 'LLM-Enhanced Avatar Intelligence System for deep personality analysis'
});

// ===================
// SAMPLE LLM-ENHANCED QUERIES
// ===================

// Query to get comprehensive personality profile
// MATCH (p:Person {name: 'Claire Russell'})-[:HAS_PERSONALITY_PROFILE]->(pp:PersonalityProfile)
// MATCH (p)-[:HAS_COMMUNICATION_STYLE]->(cs:CommunicationStyle)
// MATCH (p)-[:HAS_EMOTIONAL_PROFILE]->(ep:EmotionalProfile)
// RETURN p.name, 
//        pp.bigFiveScores, pp.personalityInsights,
//        cs.communicationPatterns, cs.preferredStyle,
//        ep.emotionalRange, ep.emotionalTriggers
// ORDER BY pp.confidenceScore DESC;

// Query to get relationship dynamics with LLM insights
// MATCH (p:Person {name: 'Claire Russell'})-[:HAS_RELATIONSHIP_DYNAMIC]->(rd:RelationshipDynamic)
// MATCH (rd)-[:WITH_PERSON]->(partner:Person)
// RETURN partner.name, 
//        rd.relationshipType, rd.intimacyLevel, rd.communicationPattern,
//        rd.llmInsights, rd.conversationTopics, rd.emotionalDynamics
// ORDER BY rd.messageCount DESC;

// Query to get topic expertise and interests
// MATCH (p:Person {name: 'Claire Russell'})-[:INTERESTED_IN]->(ta:TopicAnalysis)
// RETURN ta.topicCategory, ta.expertiseLevel, ta.engagementLevel,
//        ta.keyInsights, ta.relatedTopics, ta.conversationFrequency
// ORDER BY ta.expertiseLevel DESC, ta.engagementLevel DESC;

// Query to find similar communication styles
// MATCH (p1:Person)-[:HAS_COMMUNICATION_STYLE]->(cs1:CommunicationStyle)
// MATCH (p2:Person)-[:HAS_COMMUNICATION_STYLE]->(cs2:CommunicationStyle)
// WHERE p1 <> p2 AND abs(cs1.formalityLevel - cs2.formalityLevel) < 0.2
//   AND abs(cs1.directnessScore - cs2.directnessScore) < 0.2
// RETURN p1.name, p2.name, 
//        cs1.communicationPatterns as style1,
//        cs2.communicationPatterns as style2,
//        abs(cs1.formalityLevel - cs2.formalityLevel) as formalityDiff
// ORDER BY formalityDiff;

// ===================
// LLM ANALYSIS TRACKING
// ===================

// Track LLM analysis sessions for audit and improvement
// CREATE (la:LLMAnalysis {
//   id: 'analysis_' + randomUUID(),
//   personId: 'person_claire_russell',
//   model: 'claude-3-sonnet',
//   analysisType: 'personality_profile',
//   tokensUsed: 15420,
//   cost: 0.23,
//   confidenceScore: 0.87,
//   analysisDate: datetime(),
//   version: '1.0'
// });

// ===================
// SEMANTIC CLUSTERING FOR CONVERSATION ANALYSIS
// ===================

// Create semantic clusters for similar conversation segments
// CREATE (sc:SemanticCluster {
//   id: 'cluster_' + randomUUID(),
//   personId: 'person_claire_russell',
//   topicTheme: 'health_and_wellness',
//   clusterSize: 145,
//   similarityThreshold: 0.75,
//   representativeMessages: ['message_id_1', 'message_id_2'],
//   keyInsights: 'Shows consistent interest in holistic health approaches',
//   createdDate: datetime()
// });

// ===================
// MAINTENANCE AND MONITORING
// ===================

// Monitor LLM analysis costs and usage
// MATCH (la:LLMAnalysis)
// WHERE datetime(la.analysisDate) > datetime() - duration('P30D')
// RETURN la.model, 
//        count(*) as analysisCount,
//        sum(la.tokensUsed) as totalTokens,
//        sum(la.cost) as totalCost,
//        avg(la.confidenceScore) as avgConfidence
// ORDER BY totalCost DESC;

// Clean up old LLM analysis records (keep for audit purposes)
// MATCH (la:LLMAnalysis)
// WHERE datetime(la.analysisDate) < datetime() - duration('P365D')
//   AND la.confidenceScore < 0.5
// SET la.status = 'archived';

// Update system statistics with LLM enhancements
// MATCH (sys:LLMSystem {id: 'avatar_llm_intelligence_v1'})
// MATCH (pp:PersonalityProfile) WHERE pp.llmGenerated = true
// WITH sys, count(pp) as llmProfiles
// MATCH (la:LLMAnalysis) WHERE datetime(la.analysisDate) > datetime() - duration('P7D')
// WITH sys, llmProfiles, count(la) as recentAnalyses
// SET sys.totalLLMProfiles = llmProfiles,
//     sys.recentAnalyses = recentAnalyses,
//     sys.lastUpdate = datetime();
