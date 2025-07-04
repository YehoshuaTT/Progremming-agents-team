import React, { useEffect, useState } from 'react';
import { getUsers } from '../services/userService';

interface User {
  id: number;
  username: string;
  email: string;
}

const UserProfile: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await getUsers();
        setUsers(data);
      } catch (error) {
        // Handle error
      }
    };

    fetchUsers();
  }, []);

  return (
    <div>
      <h1>User Profile</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>{user.username} - {user.email}</li>
        ))}
      </ul>
    </div>
  );
};

export default UserProfile;
