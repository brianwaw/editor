import React, { useState } from 'react';
import axios from 'axios';

const Register = ({ onLogin, onSwitchToLogin }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://127.0.0.1:8001/api/auth/register/', {
                username,
                email,
                password
            });
            onLogin(response.data.token);
        } catch (err) {
            setError(err.response?.data?.error || 'Registration failed');
        }
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '4px', background: '#333', color: 'white' }}>
            <h3>Register</h3>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    style={{ padding: '5px' }}
                />
                <input
                    type="email"
                    placeholder="Email (Optional)"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    style={{ padding: '5px' }}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    style={{ padding: '5px' }}
                />
                <button type="submit" style={{ padding: '5px', cursor: 'pointer', background: '#4CAF50', color: 'white', border: 'none' }}>
                    Register
                </button>
            </form>
            <p style={{ marginTop: '10px', fontSize: '0.9em' }}>
                Already have an account? <button onClick={onSwitchToLogin} style={{ background: 'none', border: 'none', color: '#4CAF50', textDecoration: 'underline', cursor: 'pointer' }}>Login</button>
            </p>
        </div>
    );
};

export default Register;
