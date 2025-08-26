/**
 * @fileoverview Cultural theme system for Indian Palmistry AI
 * Provides culturally authentic messages, colors, and styling utilities
 * Based on traditional Indian palmistry (Hast Rekha Shastra)
 */

/**
 * Collection of culturally appropriate welcome messages
 * Rotates randomly to provide variety while maintaining authenticity
 */
const welcomeMessages = [
  "Discover the ancient wisdom of your palms",
  "Let the sacred art of Hast Rekha Shastra guide you",
  "Unlock the secrets written in your hands",
  "Journey into the mystic knowledge of palmistry",
  "Experience the timeless wisdom of Indian palm reading",
];

const loadingMessages = [
  "Reading the lines of destiny...",
  "Consulting ancient palmistry wisdom...",
  "Analyzing the sacred symbols in your palms...",
  "Interpreting the divine signs...",
  "Unveiling the secrets of your hands...",
];

const completionMessages = [
  "Your palm reading is complete!",
  "The ancient wisdom has spoken",
  "Your destiny has been revealed",
  "The sacred knowledge is yours",
  "Your palm's secrets are unveiled",
];

const messageCategories = {
  welcome: welcomeMessages,
  loading: loadingMessages,
  completion: completionMessages,
};

/**
 * Get a random culturally appropriate message from the specified category
 * @param category - Message category (welcome, loading, completion)
 * @returns Random message string from the specified category
 */
export function getRandomMessage(category: keyof typeof messageCategories): string {
  const messages = messageCategories[category];
  if (!messages || messages.length === 0) {
    console.warn(`No messages found for category: ${category}`);
    return `Loading ${category} message...`;
  }
  const randomIndex = Math.floor(Math.random() * messages.length);
  return messages[randomIndex];
}

export const culturalThemes = {
  saffronColor: '#FF9933',
  greenColor: '#138808', 
  whiteColor: '#FFFFFF',
  
  // Traditional Indian palmistry terms
  palmistryTerms: {
    lifeLineHindi: 'जीवन रेखा (Jeevan Rekha)',
    headLineHindi: 'मस्तिष्क रेखा (Mastishk Rekha)',
    heartLineHindi: 'हृदय रेखा (Hridaya Rekha)',
    fateLineHindi: 'भाग्य रेखा (Bhagya Rekha)',
  }
};

/**
 * Component styling utilities for consistent design system
 * Generates Tailwind CSS classes based on component type, variant, and size
 * @param componentType - Type of component (button, card, input)
 * @param variant - Style variant (default, outline, ghost, destructive)
 * @param size - Size variant (sm, md, lg)
 * @returns Tailwind CSS class string
 */
export function getComponentClasses(componentType: string, variant?: string, size?: string) {
  const baseClasses = {
    button: {
      base: 'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
      default: 'bg-saffron-500 text-white hover:bg-saffron-600',
      outline: 'border border-saffron-500 text-saffron-500 hover:bg-saffron-50',
      ghost: 'text-saffron-500 hover:bg-saffron-50',
      destructive: 'bg-red-500 text-white hover:bg-red-600',
      sm: 'h-9 px-3 text-xs',
      md: 'h-10 px-4 py-2',
      lg: 'h-11 px-8 text-lg',
    },
    card: {
      base: 'rounded-lg border bg-card text-card-foreground shadow-sm',
      default: 'border-border bg-background',
      outline: 'border-saffron-200',
    },
    input: {
      base: 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
      default: 'border-border',
    }
  };

  const component = baseClasses[componentType as keyof typeof baseClasses];
  if (!component) return '';

  let classes = component.base || '';
  
  if (variant && component[variant as keyof typeof component]) {
    classes += ' ' + component[variant as keyof typeof component];
  } else if (component.default) {
    classes += ' ' + component.default;
  }
  
  if (size && component[size as keyof typeof component]) {
    classes += ' ' + component[size as keyof typeof component];
  } else if (component.md) {
    classes += ' ' + component.md;
  }

  return classes.trim();
}