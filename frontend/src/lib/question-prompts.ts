/**
 * Shared question prompts for palmistry readings
 * Used across reading page and conversation page for consistent user experience
 */

export interface QuestionPrompt {
  label: string;
  fullQuestion: string;
}

export const QUESTION_PROMPTS: QuestionPrompt[] = [
  {
    label: "My Future",
    fullQuestion: "What does my life line reveal about my future?"
  },
  {
    label: "Love & Relationships",
    fullQuestion: "Tell me about my love and relationships"
  },
  {
    label: "Career Path",
    fullQuestion: "What career path is best suited for me?"
  },
  {
    label: "Health & Wellness",
    fullQuestion: "How can I improve my health and wellness?"
  },
  {
    label: "Hidden Talents",
    fullQuestion: "What are my hidden talents and strengths?"
  }
];