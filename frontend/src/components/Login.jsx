import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin, onSwitchToRegister }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://127.0.0.1:8001/api/auth/login/', {
                username,
                password
            });
            onLogin(response.data.token);
        } catch (err) {
            setError('Invalid credentials');
        }
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '4px', background: '#333', color: 'white' }}>
            <h3>Login</h3>
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
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    style={{ padding: '5px' }}
                />
                <button type="submit" style={{ padding: '5px', cursor: 'pointer', background: '#4CAF50', color: 'white', border: 'none' }}>
                    Login
                </button>
            </form>
            <p style={{ marginTop: '10px', fontSize: '0.9em' }}>
                Don't have an account? <button onClick={onSwitchToRegister} style={{ background: 'none', border: 'none', color: '#4CAF50', textDecoration: 'underline', cursor: 'pointer' }}>Register</button>
            </p>
        </div>
    );
};

export default Login;
