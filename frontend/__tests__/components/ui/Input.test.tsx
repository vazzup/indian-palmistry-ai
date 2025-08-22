import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '@/components/ui/Input';
import { Mail } from 'lucide-react';

describe('Input Component', () => {
  it('renders with label and placeholder', () => {
    render(
      <Input 
        label="Email Address" 
        placeholder="Enter your email"
        data-testid="email-input"
      />
    );
    
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <Input 
        label="Email" 
        error="This field is required"
        data-testid="email-input"
      />
    );
    
    expect(screen.getByText(/this field is required/i)).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveClass('border-vermillion');
  });

  it('displays hint text', () => {
    render(
      <Input 
        label="Password" 
        hint="Must be at least 8 characters"
        data-testid="password-input"
      />
    );
    
    expect(screen.getByText(/must be at least 8 characters/i)).toBeInTheDocument();
  });

  it('renders with icon', () => {
    render(
      <Input 
        label="Email" 
        icon={<Mail data-testid="mail-icon" />}
        data-testid="email-input"
      />
    );
    
    expect(screen.getByTestId('mail-icon')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveClass('pl-10');
  });

  it('handles password toggle functionality', () => {
    render(
      <Input 
        type="password"
        showPasswordToggle
        label="Password"
        data-testid="password-input"
      />
    );
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'password');
    
    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);
    
    expect(input).toHaveAttribute('type', 'text');
  });

  it('handles input changes', () => {
    const handleChange = vi.fn();
    render(
      <Input 
        label="Name" 
        onChange={handleChange}
        data-testid="name-input"
      />
    );
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'John Doe' } });
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('renders different sizes correctly', () => {
    const { rerender } = render(<Input size="sm" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveClass('h-8');

    rerender(<Input size="lg" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveClass('h-12');
  });

  it('disables input when disabled prop is true', () => {
    render(<Input disabled label="Disabled Input" />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    expect(input).toHaveClass('disabled:bg-muted');
  });
});