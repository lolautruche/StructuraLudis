import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RegisterForm } from '../RegisterForm';

// Mock useAuth
const mockRegister = jest.fn();
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    register: mockRegister,
  }),
}));

describe('RegisterForm', () => {
  beforeEach(() => {
    mockRegister.mockReset();
  });

  it('renders all form fields', () => {
    render(<RegisterForm />);
    expect(screen.getByLabelText('email')).toBeInTheDocument();
    expect(screen.getByLabelText('fullName')).toBeInTheDocument();
    expect(screen.getByLabelText('password')).toBeInTheDocument();
    expect(screen.getByLabelText('confirmPassword')).toBeInTheDocument();
  });

  it('renders privacy policy checkbox', () => {
    render(<RegisterForm />);
    expect(screen.getByRole('checkbox')).toBeInTheDocument();
    expect(screen.getByText(/politique de confidentialité/i)).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<RegisterForm />);
    expect(screen.getByRole('button', { name: 'registerButton' })).toBeInTheDocument();
  });

  it('shows password strength indicator when typing password', () => {
    render(<RegisterForm />);

    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'weak' },
    });

    // Should show strength indicator (label varies based on strength)
    expect(screen.getByText(/Faible|Moyen|Fort/)).toBeInTheDocument();
  });

  it('calls register on valid form submission', async () => {
    mockRegister.mockResolvedValue({ success: true });

    render(<RegisterForm />);

    fireEvent.change(screen.getByLabelText('email'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('fullName'), {
      target: { value: 'John Doe' },
    });
    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'securepassword123' },
    });
    fireEvent.change(screen.getByLabelText('confirmPassword'), {
      target: { value: 'securepassword123' },
    });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'registerButton' }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'securepassword123',
        full_name: 'John Doe',
        accept_privacy_policy: true,
      });
    });
  });

  it('shows success message on successful registration', async () => {
    mockRegister.mockResolvedValue({ success: true });

    render(<RegisterForm />);

    fireEvent.change(screen.getByLabelText('email'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'securepassword123' },
    });
    fireEvent.change(screen.getByLabelText('confirmPassword'), {
      target: { value: 'securepassword123' },
    });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'registerButton' }));

    await waitFor(() => {
      expect(screen.getByText(/Compte créé avec succès/)).toBeInTheDocument();
    });
  });

  it('shows error when email already exists', async () => {
    mockRegister.mockResolvedValue({
      success: false,
      error: 'email already exists',
    });

    render(<RegisterForm />);

    fireEvent.change(screen.getByLabelText('email'), {
      target: { value: 'existing@example.com' },
    });
    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'securepassword123' },
    });
    fireEvent.change(screen.getByLabelText('confirmPassword'), {
      target: { value: 'securepassword123' },
    });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'registerButton' }));

    await waitFor(() => {
      expect(screen.getByText('emailExists')).toBeInTheDocument();
    });
  });
});
