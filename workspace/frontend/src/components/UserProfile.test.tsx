import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import UserProfile from './UserProfile';
import { mockUsers } from '../mocks/users';

// Mock the userService to avoid actual API calls
vi.mock('../services/userService', () => ({
  getUsers: vi.fn(() => Promise.resolve(mockUsers)),
}));

describe('UserProfile', () => {
  it('renders user profile and displays users', async () => {
    render(<UserProfile />);

    // Check for the main heading
    expect(screen.getByText('User Profile')).toBeInTheDocument();

    // Check if the mock users are displayed
    // Note: We use findAllByRole because the data is fetched asynchronously
    const listItems = await screen.findAllByRole('listitem');
    expect(listItems).toHaveLength(mockUsers.length);

    // Check the content of the list items
    expect(screen.getByText('john_doe - john.doe@example.com')).toBeInTheDocument();
    expect(screen.getByText('jane_doe - jane.doe@example.com')).toBeInTheDocument();
  });
});
