import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from '../LoginForm';

// Mock useAuth
const mockLogin = jest.fn();
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
  }),
}));

describe('LoginForm', () => {
  beforeEach(() => {
    mockLogin.mockReset();
  });

  it('renders email and password inputs', () => {
    render(<LoginForm />);
    expect(screen.getByLabelText('email')).toBeInTheDocument();
    expect(screen.getByLabelText('password')).toBeInTheDocument();
  });

  it('renders remember me checkbox', () => {
    render(<LoginForm />);
    expect(screen.getByLabelText('rememberMe')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<LoginForm />);
    expect(screen.getByRole('button', { name: 'loginButton' })).toBeInTheDocument();
  });

  it('renders forgot password link', () => {
    render(<LoginForm />);
    expect(screen.getByText('forgotPassword')).toBeInTheDocument();
  });

  it('calls login on form submission', async () => {
    mockLogin.mockResolvedValue({ success: true });

    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText('email'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'loginButton' }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        remember_me: false,
      });
    });
  });

  it('calls login with remember_me true when checkbox is checked', async () => {
    mockLogin.mockResolvedValue({ success: true });

    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText('email'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByLabelText('rememberMe'));
    fireEvent.click(screen.getByRole('button', { name: 'loginButton' }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        remember_me: true,
      });
    });
  });

  it('shows error message on login failure', async () => {
    mockLogin.mockResolvedValue({
      success: false,
      error: 'Invalid credentials',
    });

    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText('email'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('password'), {
      target: { value: 'wrongpassword' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'loginButton' }));

    await waitFor(() => {
      expect(screen.getByText('invalidCredentials')).toBeInTheDocument();
    });
  });
});
