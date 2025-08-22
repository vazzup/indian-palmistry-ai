import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MobileImageUpload } from '@/components/analysis/MobileImageUpload';

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock FileReader
global.FileReader = class {
  result = new ArrayBuffer(8);
  readAsArrayBuffer = vi.fn(() => {
    // Simulate JPEG magic bytes
    this.result = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]).buffer;
    if (this.onload) this.onload({} as ProgressEvent<FileReader>);
  });
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
} as any;

describe('MobileImageUpload Component', () => {
  const mockOnUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload interface', () => {
    render(<MobileImageUpload onUpload={mockOnUpload} />);
    
    expect(screen.getByText(/upload your palm images/i)).toBeInTheDocument();
    expect(screen.getByText(/up to 2 images/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose files/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /take photo/i })).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    render(<MobileImageUpload onUpload={mockOnUpload} />);
    
    const file = new File(['dummy content'], 'palm.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 1024 * 1024 }); // 1MB
    
    const fileInput = document.querySelector('input[type="file"]:not([capture])') as HTMLInputElement;
    
    fireEvent.change(fileInput!, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith([file]);
    });
  });

  it('validates file types', async () => {
    render(<MobileImageUpload onUpload={mockOnUpload} />);
    
    const invalidFile = new File(['dummy'], 'document.pdf', { type: 'application/pdf' });
    const fileInput = document.querySelector('input[type="file"]:not([capture])') as HTMLInputElement;
    
    fireEvent.change(fileInput!, { target: { files: [invalidFile] } });
    
    await waitFor(() => {
      expect(screen.getByText(/only jpeg and png files are allowed/i)).toBeInTheDocument();
    });
    
    expect(mockOnUpload).not.toHaveBeenCalled();
  });

  it('validates file size', async () => {
    render(<MobileImageUpload onUpload={mockOnUpload} maxSize={1} />);
    
    const largeFile = new File(['dummy'], 'large.jpg', { type: 'image/jpeg' });
    Object.defineProperty(largeFile, 'size', { value: 2 * 1024 * 1024 }); // 2MB
    
    const fileInput = document.querySelector('input[type="file"]:not([capture])') as HTMLInputElement;
    
    fireEvent.change(fileInput!, { target: { files: [largeFile] } });
    
    await waitFor(() => {
      expect(screen.getByText(/file size must be less than 1mb/i)).toBeInTheDocument();
    });
  });

  it('limits maximum number of files', async () => {
    render(<MobileImageUpload onUpload={mockOnUpload} maxFiles={1} />);
    
    const file1 = new File(['dummy1'], 'palm1.jpg', { type: 'image/jpeg' });
    const file2 = new File(['dummy2'], 'palm2.jpg', { type: 'image/jpeg' });
    
    const fileInput = document.querySelector('input[type="file"]:not([capture])') as HTMLInputElement;
    
    fireEvent.change(fileInput!, { target: { files: [file1, file2] } });
    
    await waitFor(() => {
      expect(screen.getByText(/maximum 1 images allowed/i)).toBeInTheDocument();
    });
  });

  it('shows preview of uploaded images', async () => {
    render(<MobileImageUpload onUpload={mockOnUpload} />);
    
    const file = new File(['dummy'], 'palm.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 1024 });
    
    const fileInput = document.querySelector('input[type="file"]:not([capture])') as HTMLInputElement;
    
    fireEvent.change(fileInput!, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText(/selected images/i)).toBeInTheDocument();
      expect(screen.getByAltText(/left palm preview/i)).toBeInTheDocument();
    });
  });

  it('allows removing individual previews', async () => {
    render(<MobileImageUpload onUpload={mockOnUpload} />);
    
    const file = new File(['dummy'], 'palm.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 1024 });
    
    const fileInput = document.querySelector('input[type="file"]:not([capture])') as HTMLInputElement;
    
    fireEvent.change(fileInput!, { target: { files: [file] } });
    
    await waitFor(() => {
      const removeButton = document.querySelector('button[class*="absolute"]');
      expect(removeButton).toBeInTheDocument();
    });
    
    const removeButton = document.querySelector('button[class*="absolute"]')!;
    fireEvent.click(removeButton);
    
    expect(screen.queryByText(/selected images/i)).not.toBeInTheDocument();
  });

  it('handles drag and drop', () => {
    render(<MobileImageUpload onUpload={mockOnUpload} />);
    
    const dropZone = screen.getByText(/upload your palm images/i).closest('div')!;
    
    const file = new File(['dummy'], 'palm.jpg', { type: 'image/jpeg' });
    
    fireEvent.dragOver(dropZone, {
      dataTransfer: {
        files: [file],
      },
    });
    
    // Should show dragging state
    expect(dropZone.parentElement).toHaveClass('border-saffron-500');
    
    fireEvent.dragLeave(dropZone);
    
    // Should remove dragging state
    expect(dropZone.parentElement).not.toHaveClass('border-saffron-500');
  });

  it('disables interaction when uploading', () => {
    render(<MobileImageUpload onUpload={mockOnUpload} isUploading />);
    
    const chooseButton = screen.getByRole('button', { name: /choose files/i });
    const cameraButton = screen.getByRole('button', { name: /take photo/i });
    
    expect(chooseButton).toBeDisabled();
    expect(cameraButton).toBeDisabled();
  });
});