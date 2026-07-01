"""
Medical prompt templates for the AI assistant.

Provides carefully crafted prompts for different medical query types.
"""

from typing import Dict, Any
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate


# System instruction for all medical queries
SYSTEM_INSTRUCTION = """You are a medical AI assistant providing educational information based on retrieved medical knowledge.

CRITICAL RULES:
1. Base ALL answers ONLY on the provided context documents
2. NEVER fabricate or infer medical information not in the context
3. Cite sources using [Source: document_name] format
4. State "I don't have enough information" if context is insufficient
5. Always encourage consulting healthcare professionals
6. Never provide diagnosis, treatment recommendations, or dosage advice
7. Focus on education and awareness only

RESPONSE STRUCTURE:
- Provide a clear, accurate summary
- Cite specific sources for each claim
- Acknowledge limitations or uncertainties
- Suggest follow-up questions when appropriate
- Include medical disclaimer

Remember: This is educational information, not medical advice."""


# Medical Q&A Template
MEDICAL_QA_TEMPLATE = """Context Documents:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the context provided
- Cite sources for every claim [Source: document_name]
- If information is incomplete, state what's missing
- Be concise but thorough
- Use clear, accessible language
- Include key points in bullet format if helpful

Answer:"""


# Disease Explanation Template
DISEASE_EXPLANATION_TEMPLATE = """Context Documents:
{context}

Question: Explain {disease_name}

Instructions:
- Provide a comprehensive overview based on the context
- Cover: definition, causes, symptoms, risk factors, prevention
- Use clear medical terminology with explanations
- Cite sources for each section
- Organize information logically
- Highlight important warnings or considerations

Explanation:"""


# Drug Information Template
DRUG_INFORMATION_TEMPLATE = """Context Documents:
{context}

Question: Provide information about {drug_name}

Instructions:
- Answer based ONLY on the context documents
- Cover: drug class, uses, mechanism, contraindications
- DO NOT provide dosage recommendations
- Cite sources for each claim
- Emphasize the need for professional medical guidance
- Note any warnings or precautions mentioned

Information:"""


# Clinical Guidelines Template
CLINICAL_GUIDELINES_TEMPLATE = """Context Documents:
{context}

Question: What are the clinical guidelines for {condition}?

Instructions:
- Summarize guidelines based on the provided context
- Focus on evidence-based recommendations
- Cite authoritative sources
- Organize by guideline category
- Note any updates or variations mentioned
- Emphasize that guidelines should be applied by healthcare professionals

Guidelines Summary:"""


# Medical Definition Template
MEDICAL_DEFINITION_TEMPLATE = """Context Documents:
{context}

Question: Define {medical_term}

Instructions:
- Provide a clear, accurate definition from the context
- Use accessible language while maintaining accuracy
- Include related terms or concepts if mentioned
- Cite the source of the definition
- Provide context about usage or significance

Definition:"""


# Research Question Template
RESEARCH_QUESTION_TEMPLATE = """Context Documents:
{context}

Research Question: {question}

Instructions:
- Synthesize information from the provided research documents
- Highlight key findings and evidence
- Note any conflicting information or limitations
- Cite specific studies or sources
- Distinguish between established facts and ongoing research
- Avoid overstating conclusions

Research Summary:"""


# Conversation Continuation Template
CONVERSATION_CONTINUATION_TEMPLATE = """Previous Conversation:
{conversation_history}

Context Documents:
{context}

Current Question: {question}

Instructions:
- Consider the conversation history for context
- Answer the current question based on retrieved documents
- Maintain consistency with previous responses
- Cite sources as always
- If the question refers to previous topics, acknowledge that
- Provide coherent follow-up information

Answer:"""


# Follow-up Question Generation Template
FOLLOWUP_GENERATION_TEMPLATE = """Original Question: {question}

Answer Provided: {answer}

Context: {context}

Instructions:
Generate 3 relevant follow-up questions that:
- Help the user explore related topics
- Are answerable based on available context
- Progress from general to specific
- Cover different aspects (causes, symptoms, treatment, prevention)

Format:
1. [Question about treatment/management]
2. [Question about symptoms/diagnosis]
3. [Question about prevention/risk factors]

Follow-up Questions:"""


class MedicalPromptTemplates:
    """Collection of medical prompt templates."""
    
    def __init__(self):
        """Initialize prompt templates."""
        self.templates = self._create_templates()
    
    def _create_templates(self) -> Dict[str, PromptTemplate]:
        """Create all prompt templates."""
        return {
            'medical_qa': PromptTemplate(
                input_variables=['context', 'question'],
                template=MEDICAL_QA_TEMPLATE
            ),
            
            'disease_explanation': PromptTemplate(
                input_variables=['context', 'disease_name'],
                template=DISEASE_EXPLANATION_TEMPLATE
            ),
            
            'drug_information': PromptTemplate(
                input_variables=['context', 'drug_name'],
                template=DRUG_INFORMATION_TEMPLATE
            ),
            
            'clinical_guidelines': PromptTemplate(
                input_variables=['context', 'condition'],
                template=CLINICAL_GUIDELINES_TEMPLATE
            ),
            
            'medical_definition': PromptTemplate(
                input_variables=['context', 'medical_term'],
                template=MEDICAL_DEFINITION_TEMPLATE
            ),
            
            'research_question': PromptTemplate(
                input_variables=['context', 'question'],
                template=RESEARCH_QUESTION_TEMPLATE
            ),
            
            'conversation_continuation': PromptTemplate(
                input_variables=['conversation_history', 'context', 'question'],
                template=CONVERSATION_CONTINUATION_TEMPLATE
            ),
            
            'followup_generation': PromptTemplate(
                input_variables=['question', 'answer', 'context'],
                template=FOLLOWUP_GENERATION_TEMPLATE
            )
        }
    
    def get_template(self, template_name: str) -> PromptTemplate:
        """
        Get a specific prompt template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            PromptTemplate instance
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        return self.templates[template_name]
    
    def create_chat_prompt(
        self,
        template_name: str,
        system_instruction: str = SYSTEM_INSTRUCTION
    ) -> ChatPromptTemplate:
        """
        Create a chat prompt with system instruction.
        
        Args:
            template_name: Name of the template
            system_instruction: System instruction (override default)
            
        Returns:
            ChatPromptTemplate
        """
        template = self.get_template(template_name)
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_instruction),
            HumanMessagePromptTemplate(prompt=template)
        ])
    
    def list_templates(self) -> list:
        """List all available templates."""
        return list(self.templates.keys())


# Disclaimer templates
MEDICAL_DISCLAIMER = """
---
**Medical Disclaimer**: This information is for educational purposes only and should not replace professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for personalized medical guidance.
"""

EMERGENCY_WARNING = """
⚠️ **EMERGENCY WARNING**: If this is a medical emergency, please call emergency services immediately (911 in the US) or go to the nearest emergency room. Do not rely on this AI assistant for emergency medical situations.
"""

DIAGNOSIS_DISCLAIMER = """
---
**Important**: This AI cannot provide medical diagnoses. The information provided is educational only. For accurate diagnosis and treatment, please consult with a licensed healthcare professional who can evaluate your specific situation.
"""

NO_DOSAGE_DISCLAIMER = """
---
**Medication Safety**: Dosage information must be determined by a healthcare provider based on individual factors. Never adjust medication dosages without professional medical supervision.
"""


def get_disclaimer(disclaimer_type: str) -> str:
    """
    Get appropriate disclaimer text.
    
    Args:
        disclaimer_type: Type of disclaimer (medical, emergency, diagnosis, dosage)
        
    Returns:
        Disclaimer text
    """
    disclaimers = {
        'medical': MEDICAL_DISCLAIMER,
        'emergency': EMERGENCY_WARNING,
        'diagnosis': DIAGNOSIS_DISCLAIMER,
        'dosage': NO_DOSAGE_DISCLAIMER
    }
    
    return disclaimers.get(disclaimer_type, MEDICAL_DISCLAIMER)
