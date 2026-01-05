import React from 'react';
import Editor from '@monaco-editor/react';

const CodeEditor = ({
    language = "python",
    code = "",
    onChange
}) => {

    const handleEditorChange = (value, event) => {
        if (onChange) {
            onChange(value);
        }
    };

    // Map languages to file extensions for Monaco to hint syntax highlighting
    const fileExtensionMap = {
        python: 'py',
        javascript: 'js',
        typescript: 'ts',
        c: 'c',
        cpp: 'cpp',
        java: 'java',
        csharp: 'cs',
        rust: 'rs',
        go: 'go',
        php: 'php',
        ruby: 'rb',
        sql: 'sql',
        html: 'html',
        css: 'css',
        json: 'json',
        xml: 'xml',
        yaml: 'yaml'
    };

    const extension = fileExtensionMap[language] || 'txt';
    const path = `model.${extension}`;

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <Editor
                height="100%"
                width="100%"
                language={language}
                path={path}
                value={code}
                theme="vs-dark"
                onChange={handleEditorChange}
                options={{
                    minimap: { enabled: true },
                    fontSize: 14,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 4,
                    wordWrap: 'on',
                    mouseWheelZoom: true,
                    smoothScrolling: true,
                    cursorBlinking: "smooth",
                    cursorSmoothCaretAnimation: "on",
                    formatOnPaste: true,
                    formatOnType: true,
                    semanticHighlighting: { enabled: true },
                }}
            />
        </div>
    );
};

export default CodeEditor;
