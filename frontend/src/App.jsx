import React, { useState } from 'react';
import CodeEditor from './components/CodeEditor';
import Login from './components/Login';
import Register from './components/Register';
import './App.css';
import axios from 'axios';

function App() {
  const CODE_SNIPPETS = {
    python: "# Write your Python code here\nprint('Hello, World!')\n",
    javascript: "// Write your JavaScript code here\nconsole.log('Hello, World!');\n",
    typescript: "// Write your TypeScript code here\nconst message: string = 'Hello, World!';\nconsole.log(message);\n",
    c: "#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}\n",
    cpp: "#include <iostream>\n\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}\n",
    java: "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}\n",
    csharp: "using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine(\"Hello, World!\");\n    }\n}\n",
    rust: "fn main() {\n    println!(\"Hello, World!\");\n}\n",
    go: "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"Hello, World!\")\n}\n",
    php: "<?php\necho \"Hello, World!\";\n?>\n",
    ruby: "# Write your Ruby code here\nputs 'Hello, World!'\n",
    sql: "-- Write your SQL query here\nSELECT * FROM users;\n",
    html: "<!DOCTYPE html>\n<html>\n<head>\n    <title>Hello World</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>\n",
    css: "body {\n    font-family: Arial, sans-serif;\n    background-color: #f0f0f0;\n}\n",
    json: "{\n    \"message\": \"Hello, World!\"\n}\n",
    xml: "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<note>\n    <to>User</to>\n    <from>System</from>\n    <heading>Reminder</heading>\n    <body>Hello, World!</body>\n</note>\n",
    yaml: "---\nmessage: Hello, World!\n"
  };

  const [code, setCode] = useState(CODE_SNIPPETS["python"]);
  const [language, setLanguage] = useState("python");
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [showLogin, setShowLogin] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'

  const handleLogin = (newToken) => {
    setToken(newToken);
    localStorage.setItem('token', newToken);
    setShowLogin(false);
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
  };

  const handleCodeChange = (newCode) => {
    setCode(newCode);
  };

  const handleLanguageChange = (e) => {
    const selectedLang = e.target.value;
    setLanguage(selectedLang);
    // Switch to the default snippet for the new language
    setCode(CODE_SNIPPETS[selectedLang] || "");
  };

  const saveCode = async () => {
    if (!token) {
      alert("Please login to save code.");
      setAuthMode('login');
      setShowLogin(true);
      return;
    }

    try {
      const response = await axios.post('http://127.0.0.1:8001/api/save/', {
        language: language,
        code: code
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      console.log("Saved:", response.data);
      alert("Code saved successfully!");
    } catch (error) {
      console.error("Error saving code:", error);
      if (error.response && error.response.status === 403) {
        alert("Session expired. Please login again.");
        handleLogout();
        setAuthMode('login');
        setShowLogin(true);
      } else {
        alert("Failed to save code.");
      }
    }
  };

  const supportedLanguages = [
    { id: "python", name: "Python" },
    { id: "javascript", name: "JavaScript" },
    { id: "typescript", name: "TypeScript" },
    { id: "c", name: "C" },
    { id: "cpp", name: "C++" },
    { id: "java", name: "Java" },
    { id: "csharp", name: "C#" },
    { id: "rust", name: "Rust" },
    { id: "go", name: "Go" },
    { id: "php", name: "PHP" },
    { id: "ruby", name: "Ruby" },
    { id: "sql", name: "SQL" },
    { id: "html", name: "HTML" },
    { id: "css", name: "CSS" },
    { id: "json", name: "JSON" },
    { id: "xml", name: "XML" },
    { id: "yaml", name: "YAML" },
  ];

  return (
    <div className="app-container" style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <header style={{ padding: '10px 20px', background: '#20232a', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Logic Gate & Code Editor</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button onClick={saveCode} style={{ padding: '5px 10px', cursor: 'pointer', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px' }}>Save</button>
          {token ? (
            <button onClick={handleLogout} style={{ padding: '5px 10px', cursor: 'pointer', background: '#f44336', color: 'white', border: 'none', borderRadius: '4px' }}>Logout</button>
          ) : (
            <button onClick={() => { setShowLogin(true); setAuthMode('login'); }} style={{ padding: '5px 10px', cursor: 'pointer', background: '#2196F3', color: 'white', border: 'none', borderRadius: '4px' }}>Login</button>
          )}
          <label htmlFor="language-select">Language:</label>
          <select
            id="language-select"
            value={language}
            onChange={handleLanguageChange}
            style={{ padding: '5px', borderRadius: '4px' }}
          >
            {supportedLanguages.map(lang => (
              <option key={lang.id} value={lang.id}>{lang.name}</option>
            ))}
          </select>
        </div>
      </header>
      <main style={{ flex: 1, padding: '20px', display: 'flex', overflow: 'hidden' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{ marginBottom: '10px' }}>
            <h3>Code Editor ({supportedLanguages.find(l => l.id === language)?.name})</h3>
          </div>
          <div style={{ flex: 1, minHeight: 0, border: '1px solid #333' }}>
            <CodeEditor
              language={language}
              code={code}
              onChange={handleCodeChange}
            />
          </div>
        </div>
      </main>
      {showLogin && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 1000 }}>
          <button
            onClick={() => setShowLogin(false)}
            style={{ position: 'absolute', right: 0, top: 0, background: 'red', color: 'white', border: 'none', cursor: 'pointer' }}
          >X</button>
          {authMode === 'login' ? (
            <Login onLogin={handleLogin} onSwitchToRegister={() => setAuthMode('register')} />
          ) : (
            <Register onLogin={handleLogin} onSwitchToLogin={() => setAuthMode('login')} />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
